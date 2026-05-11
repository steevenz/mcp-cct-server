"""
Smart LLM Tier Router — Offline-First, Sampling-Escalate.

Architecture:
  Tier 1: Gemma 2B embedded (llama-cpp-python) — pattern extraction, classification
  Tier 2: Gemma 9B embedded (llama-cpp-python) — reasoning, clustering, fallback
  Tier 3: Client LLM via MCP Sampling — deep thinking, creative, complex

Routing Logic:
  1. Always try Tier 1 first (free, fast, always available)
  2. If confidence < threshold → escalate to Tier 2
  3. If still low confidence OR complex task → escalate to Tier 3 via MCP Sampling
  4. If Tier 3 unavailable (no MCP session) → fallback to Tier 2
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Model URLs (HuggingFace GGUF)
MODEL_URLS = {
    "gemma-2b": "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf",
    "gemma-9b": "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
}

MODEL_FILENAMES = {
    "gemma-2b": "gemma-2-2b-it-Q4_K_M.gguf",
    "gemma-9b": "gemma-2-9b-it-Q4_K_M.gguf",
}

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models")

# Confidence thresholds
TIER_1_MIN_CONFIDENCE = 0.4
TIER_2_MIN_CONFIDENCE = 0.6


# ============================================================================
# TIER 1 & 2: Embeded Gemma via llama-cpp-python
# ============================================================================

class GemmaEngine:
    """
    Embeded Gemma model via llama-cpp-python.

    Supports both 2B (Tier 1) and 9B (Tier 2) with shared interface.
    Auto-downloads model on first use.
    Lazy-loads: model only loaded in RAM when first inference is called.
    """

    instances: Dict[str, "GemmaEngine"] = {}

    def __init__(
        self,
        model_size: str = "2b",
        n_ctx: int = 4096,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
        auto_download: bool = True,
        verbose: bool = False,
    ):
        self.model_size = model_size.lower()
        assert self.model_size in ("2b", "9b"), f"Unsupported model size: {model_size}"

        self.n_ctx = 4096 if self.model_size == "9b" else n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self._llm = None
        self._model_path = self._resolve_model_path()

        if auto_download and not os.path.exists(self._model_path):
            self._download_model()

    def _resolve_model_path(self) -> str:
        model_dir = Path(MODEL_DIR)
        model_dir.mkdir(parents=True, exist_ok=True)
        key = "gemma-9b" if self.model_size == "9b" else "gemma-2b"
        return str(model_dir / MODEL_FILENAMES[key])

    def _download_model(self) -> None:
        key = "gemma-9b" if self.model_size == "9b" else "gemma-2b"
        url = MODEL_URLS[key]
        size_label = "~1.5GB" if self.model_size == "2b" else "~5GB"
        logger.info(f"[GEMMA-{self.model_size.upper()}] Downloading from HuggingFace ({size_label})...")
        logger.info(f"[GEMMA-{self.model_size.upper()}] URL: {url}")

        start = time.time()
        try:
            urllib.request.urlretrieve(url, self._model_path)
            elapsed = time.time() - start
            size_mb = os.path.getsize(self._model_path) / (1024 * 1024)
            logger.info(f"[GEMMA-{self.model_size.upper()}] Download complete: {size_mb:.0f}MB in {elapsed:.0f}s")
        except Exception as e:
            logger.error(f"[GEMMA-{self.model_size.upper()}] Download failed: {e}")
            raise

    def _ensure_loaded(self):
        if self._llm is not None:
            return
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("Install: pip install llama-cpp-python")

        logger.info(f"[GEMMA-{self.model_size.upper()}] Loading model ({self._model_path})...")
        start = time.time()
        self._llm = Llama(
            model_path=self._model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=self.n_gpu_layers,
            verbose=self.verbose,
        )
        elapsed = time.time() - start
        logger.info(f"[GEMMA-{self.model_size.upper()}] Loaded in {elapsed:.1f}s")

    def is_available(self) -> bool:
        return os.path.exists(self._model_path)

    def generate(
        self, prompt: str, max_tokens: int = 256, temperature: float = 0.1
    ) -> str:
        self._ensure_loaded()
        result = self._llm(prompt, max_tokens=max_tokens, temperature=temperature, stop=["</s>"])
        return self._extract_text(result)

    def generate_json(
        self, prompt: str, max_tokens: int = 256, temperature: float = 0.1
    ) -> Dict[str, Any]:
        text = self.generate(prompt, max_tokens=max_tokens, temperature=temperature)
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            return {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def _extract_text(self, result: Any) -> str:
        if isinstance(result, dict):
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("text", "")
        return str(result)

    def unload(self):
        self._llm = None
        logger.info(f"[GEMMA-{self.model_size.upper()}] Unloaded")


# ============================================================================
# TIER 3: MCP Sampling (Client LLM)
# ============================================================================

class MCPSamplingRouter:
    """
    Tier 3: Uses the requesting LLM via MCP Sampling protocol.

    No API key needed — the client's LLM (Claude/GPT/Gemini from IDE)
    does the heavy lifting. Falls back to Tier 2 if no MCP session available.
    """

    def __init__(self):
        self._mcp_session = None

    def set_session(self, session):
        """Set the active MCP session for Sampling."""
        self._mcp_session = session

    async def reason(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """
        Request deep reasoning from client LLM via MCP Sampling.

        Returns (content, confidence).
        Falls back to Tier 2 (Gemma 9B) if no session available.
        """
        if not self._mcp_session:
            logger.warning("[SAMPLING] No MCP session, falling back to Tier 2")
            return await self._tier_2_fallback(prompt, max_tokens)

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            result = await self._mcp_session.sampling.create_message(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model_preferences={
                    "hints": [{"name": "claude"}, {"name": "gpt"}, {"name": "gemini"}],
                    "intelligencePriority": 0.9,
                    "speedPriority": 0.3,
                },
            )
            content = result.content.text if hasattr(result.content, "text") else str(result.content)
            return content, 0.95

        except Exception as e:
            logger.warning(f"[SAMPLING] Failed: {e}. Falling back to Tier 2")
            return await self._tier_2_fallback(prompt, max_tokens)

    async def _tier_2_fallback(self, prompt: str, max_tokens: int) -> Tuple[str, float]:
        """Fallback to Tier 2 (Gemma 9B) when Sampling unavailable."""
        try:
            engine = get_gemma_engine("9b")
            text = engine.generate(prompt, max_tokens=min(max_tokens, 1024), temperature=0.3)
            return text, 0.5
        except Exception as e:
            logger.error(f"[TIER2] Fallback failed: {e}")
            return "", 0.0


# ============================================================================
# TIER ROUTER: Smart Selection Across All 3 Tiers
# ============================================================================

class TierRouter:
    """
    Smart router across all 3 LLM tiers.

    Selection logic:
      1. Classification/extraction → Tier 1 (Gemma 2B)
      2. Reasoning/clustering → Tier 2 (Gemma 9B)
      3. Deep/creative/complex → Tier 3 (MCP Sampling)
      4. Auto-escalate when confidence < threshold
    """

    _instance: Optional["TierRouter"] = None

    def __init__(self):
        self._engines: Dict[str, GemmaEngine] = {}
        self.sampling = MCPSamplingRouter()

    @classmethod
    def get_instance(cls) -> "TierRouter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_engine(self, size: str) -> GemmaEngine:
        if size not in self._engines:
            self._engines[size] = GemmaEngine(model_size=size)
        return self._engines[size]

    def set_mcp_session(self, session):
        """Set MCP session for Tier 3 Sampling."""
        self.sampling.set_session(session)

    async def route(
        self,
        task: str,
        prompt: str,
        system_prompt: str = "",
        min_confidence: float = 0.0,
        max_tokens: int = 512,
        allow_sampling: bool = True,
    ) -> Dict[str, Any]:
        """
        Route a task to the best LLM tier.

        Args:
            task: Task type: 'extract', 'classify', 'score', 'reason', 'creative', 'complex'
            prompt: The prompt to send
            system_prompt: Optional system prompt
            min_confidence: Minimum acceptable confidence
            max_tokens: Max tokens for response
            allow_sampling: Allow Tier 3 (MCP Sampling)

        Returns:
            Dict with content, confidence, tier_used, model
        """
        # Determine which tier to use
        tier = self._select_tier(task, min_confidence, allow_sampling)
        logger.info(f"[ROUTER] Task '{task}' → Tier {tier}")

        if tier == 3:
            content, confidence = await self.sampling.reason(prompt, system_prompt, max_tokens)
            return {"content": content, "confidence": confidence, "tier": 3, "model": "client_llm"}

        if tier == 2:
            engine = self.get_engine("9b")
            if engine.is_available():
                max_tok = min(max_tokens, 2048)
                text = engine.generate(prompt, max_tokens=max_tok, temperature=0.3)
                return {"content": text, "confidence": 0.6, "tier": 2, "model": "gemma_9b"}
            tier = 1  # fall through if 9B unavailable

        # Tier 1
        engine = self.get_engine("2b")
        if engine.is_available():
            max_tok = min(max_tokens, 1024)
            text = engine.generate(prompt, max_tokens=max_tok, temperature=0.1)
            return {"content": text, "confidence": 0.4, "tier": 1, "model": "gemma_2b"}

        return {"content": "", "confidence": 0.0, "tier": 0, "model": "none", "error": "no_llm_available"}

    def _select_tier(self, task: str, min_confidence: float, allow_sampling: bool) -> int:
        """Select the best tier for a task type."""
        # Tasks that MUST go to Tier 3
        complex_tasks = {"creative", "complex", "actor_critic", "council", "lateral", "temporal"}
        if task in complex_tasks and allow_sampling:
            return 3

        # Tasks that prefer Tier 2
        reasoning_tasks = {"reason", "cluster", "trend", "mindset"}
        if task in reasoning_tasks:
            return 2 if min_confidence > TIER_1_MIN_CONFIDENCE else 1

        # Tasks that can use Tier 1
        light_tasks = {"extract", "classify", "score", "tag", "summarize"}
        if task in light_tasks:
            return 1

        # Default: escalate based on min_confidence
        if min_confidence > TIER_2_MIN_CONFIDENCE and allow_sampling:
            return 3
        if min_confidence > TIER_1_MIN_CONFIDENCE:
            return 2
        return 1

    async def analyze_session_smart(
        self, session_text: str
    ) -> Dict[str, Any]:
        """
        Analyze a session using smart tier routing.

        Tier 1: Extract basic patterns (always)
        If confidence < 0.4 → Tier 2: Deep pattern clustering
        If still uncertain → Tier 3: Complex synthesis
        """
        basic = await self.route(
            task="extract",
            prompt=f"Extract patterns from this thinking session. Return JSON.\n\nSession: {session_text[:2000]}",
        )
        result = self._parse_json(basic.get("content", ""))

        if basic.get("confidence", 0) < TIER_1_MIN_CONFIDENCE:
            deep = await self.route(
                task="cluster",
                prompt=f"Deep analyze patterns in this session. What are the user's preferences and thinking style?\n\n{session_text[:2000]}",
                max_tokens=1024,
            )
            deep_data = self._parse_json(deep.get("content", ""))
            result.update(deep_data)
            result["escalated_to"] = "tier_2"

        if result.get("confidence", 0) < 0.3:
            complex_result = await self.route(
                task="complex",
                prompt=f"Synthesize user behavior patterns from this session:\n\n{session_text[:2000]}",
                max_tokens=2048,
            )
            complex_data = self._parse_json(complex_result.get("content", ""))
            result.update(complex_data)
            result["escalated_to"] = "tier_3"

        result["tier_used"] = basic.get("tier", 1)
        return result

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
        except (json.JSONDecodeError, TypeError):
            pass
        return {}

    def unload_all(self):
        for engine in self._engines.values():
            engine.unload()
        self._engines.clear()


# ============================================================================
# CONVENIENCE: Get engines & router
# ============================================================================

def get_gemma_engine(size: str = "2b") -> GemmaEngine:
    """Get or create a GemmaEngine for given size."""
    return TierRouter.get_instance().get_engine(size)


def get_tier_router() -> TierRouter:
    """Get the global tier router singleton."""
    return TierRouter.get_instance()


async def smart_analyze_session(session_text: str) -> Dict[str, Any]:
    """One-shot session analysis with smart tier routing."""
    router = get_tier_router()
    return await router.analyze_session_smart(session_text)
