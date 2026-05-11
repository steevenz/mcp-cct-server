"""
SmartLLMService: Local-first, Online-boost LLM service.

Drop-in replacement for ClientService.generate_thought().

Architecture:
  - TIER 1: Gemma 2B (classification, light tasks)
  - TIER 2: Gemma 9B (reasoning, generation, all thinking engines)
  - TIER 3: Online API (optional quality boost)

All engines (Actor-Critic, Council, Multi-Agent, Fusion) use this service.
NOTHING is mandatory online. Online is purely a quality multiplier.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

from src.core.config import Settings
from src.core.services.llm.client import ClientService

logger = logging.getLogger(__name__)

# Task types that map to LLM tiers
_TASK_TYPES = {
    "critique": "reasoning",
    "refinement": "reasoning",
    "synthesis": "reasoning",
    "persona_insight": "creative",
    "challenge": "creative",
    "guidance": "light",
    "analysis": "reasoning",
    "evaluation": "light",
}


class SmartLLMService:
    """
    Local-first LLM service that wraps online ClientService.

    generate_thought() flow:
      1. If local Gemma 9B available -> use it (fast, free, private)
      2. If quality_boost=True AND online API available -> use online
      3. If no online API -> always use local
      4. If no local model either -> fallback to online

    This means: ZERO mandatory online dependency.
    The system runs 100% offline with Gemma 9B.
    Online API only boosts quality when explicitly requested.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._online = None
        self._gemma_9b = None
        self._gemma_2b = None
        self._online_available = bool(
            settings.openai_api_key
            or settings.anthropic_api_key
            or settings.gemini_api_key
        )

        # Initialize online client if available
        if self._online_available:
            self._online = ClientService(settings)
            logger.info("[SMARTLLM] Online API available for quality boost")

        # Try loading local Gemma engines
        self._try_load_local()

    def _try_load_local(self):
        """Try to load local Gemma engines (non-blocking, fail gracefully)."""
        try:
            from src.core.llm_offline.engine import get_gemma_engine

            # Check if Tier 1 (2B) available
            try:
                engine_2b = get_gemma_engine("2b")
                if engine_2b.is_available():
                    self._gemma_2b = engine_2b
                    logger.info("[SMARTLLM] Gemma 2B loaded (Tier 1)")
            except Exception as e:
                logger.debug(f"[SMARTLLM] Gemma 2B not available: {e}")

            # Check if Tier 2 (9B) available
            try:
                engine_9b = get_gemma_engine("9b")
                if engine_9b.is_available():
                    self._gemma_9b = engine_9b
                    logger.info("[SMARTLLM] Gemma 9B loaded (Tier 2)")
            except Exception as e:
                logger.debug(f"[SMARTLLM] Gemma 9B not available: {e}")

        except ImportError:
            logger.warning("[SMARTLLM] llama-cpp-python not installed. Local LLM unavailable.")
        except Exception as e:
            logger.warning(f"[SMARTLLM] Failed to load local engines: {e}")

    def has_local(self) -> bool:
        """Check if any local model is loaded."""
        return self._gemma_9b is not None or self._gemma_2b is not None

    def has_online(self) -> bool:
        """Check if online API is available."""
        return self._online_available and self._online is not None

    async def generate_thought(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        complexity: str = "moderate",
        requires_reasoning: bool = False,
        model_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        quality_boost: bool = False,
    ) -> str:
        """
        Generate thought using best available LLM tier.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            complexity: Task complexity hint
            requires_reasoning: Whether deep reasoning is needed
            model_id: Optional specific model request
            max_tokens: Max response tokens
            quality_boost: If True, prefer online for higher quality

        Returns:
            Generated text content
        """
        # Determine if this task should use online
        use_online = self._should_use_online(
            complexity=complexity,
            requires_reasoning=requires_reasoning,
            quality_boost=quality_boost,
            model_id=model_id,
        )

        # Online path
        if use_online and self.has_online():
            try:
                logger.debug(f"[SMARTLLM] Using online API (quality_boost={quality_boost})")
                result = await self._online.generate_thought(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    complexity=complexity,
                    requires_reasoning=requires_reasoning,
                    model_id=model_id,
                    max_tokens=max_tokens,
                )
                return result
            except Exception as e:
                logger.warning(f"[SMARTLLM] Online failed, falling back to local: {e}")

        # Local path - try Tier 2 first (Gemma 9B)
        if self._gemma_9b:
            try:
                logger.debug("[SMARTLLM] Using Gemma 9B (Tier 2)")
                full_prompt = self._build_prompt(prompt, system_prompt)
                max_tok = min(max_tokens or 1024, 2048)
                temp = 0.3 if requires_reasoning else 0.1
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    lambda: self._gemma_9b.generate(full_prompt, max_tokens=max_tok, temperature=temp),
                )
                return text
            except Exception as e:
                logger.warning(f"[SMARTLLM] Gemma 9B failed, falling back: {e}")

        # Local path - Tier 1 (Gemma 2B)
        if self._gemma_2b:
            try:
                logger.debug("[SMARTLLM] Using Gemma 2B (Tier 1)")
                full_prompt = self._build_prompt(prompt, system_prompt)
                max_tok = min(max_tokens or 512, 1024)
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    lambda: self._gemma_2b.generate(full_prompt, max_tokens=max_tok, temperature=0.3),
                )
                return text
            except Exception as e:
                logger.warning(f"[SMARTLLM] Gemma 2B failed: {e}")

        # Absolute fallback: online if nothing else works
        if self.has_online():
            logger.warning("[SMARTLLM] No local model, using online as last resort")
            return await self._online.generate_thought(
                prompt=prompt, system_prompt=system_prompt, complexity=complexity,
                requires_reasoning=requires_reasoning, model_id=model_id, max_tokens=max_tokens,
            )

        return "[No LLM available - install Gemma model or configure API key]"

    async def generate_with_quality(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        min_quality: str = "high",
    ) -> Tuple[str, str]:
        """
        Generate with quality guarantee. Uses local first, re-runs with online if quality check fails.

        Returns (content, source) where source is 'local', 'online', or 'local_fallback'.
        """
        # Try local first
        content = await self.generate_thought(prompt, system_prompt, quality_boost=False)
        if self._check_quality(content, min_quality):
            return content, "local"

        # Boost with online if available
        if self.has_online():
            online_content = await self._online.generate_thought(prompt=prompt, system_prompt=system_prompt)
            if self._check_quality(online_content, min_quality):
                return online_content, "online"

        return content, "local_fallback"

    def _should_use_online(
        self, complexity: str, requires_reasoning: bool, quality_boost: bool, model_id: Optional[str]
    ) -> bool:
        """
        Determine if online should be used.
        FORCE LOCAL (Gemma) as default unless explicitly overridden.
        """
        if model_id:
            return True  # explicit model request = force online (likely for specific testing)
        
        # If we have local models, we ALWAYS use them unless quality_boost is TRUE
        # AND we explicitly want to spend tokens for better quality.
        if self.has_local():
            if quality_boost and self.has_online():
                return True
            return False # DEFAULT: LOCAL
            
        # If no local model, then use online as fallback
        return self.has_online()

    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Build full prompt for local models."""
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt

    def _check_quality(self, content: str, min_quality: str) -> bool:
        """Basic quality check on generated content."""
        if not content or len(content.strip()) < 20:
            return False
        if min_quality == "high":
            return len(content) > 100 and not content.startswith("[No LLM")
        return True

    async def aclose(self):
        """Cleanup resources."""
        if self._online and hasattr(self._online, "aclose"):
            await self._online.aclose()
        self._gemma_9b = None
        self._gemma_2b = None
