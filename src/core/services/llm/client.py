import logging
import httpx
from typing import Dict, Any, Optional
from src.core.config import Settings
from src.core.models import CognitiveTaskContext
from src.core.services.llm.router import RouterService

logger = logging.getLogger(__name__)

class ClientService:
    """
    Thought Generation Service for autonomous cognitive processing.
    Supports Gemini (Google), OpenAI, Anthropic, and Ollama.
    
    Uses intelligent model selection for cost-performance optimization.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.selection_strategy = RouterService(settings)

    async def generate_thought(self, prompt: str, system_prompt: Optional[str] = None, 
                               complexity: str = "moderate", requires_reasoning: bool = False) -> str:
        """
        Generates a thought based on the configured provider.
        
        Now supports asymmetric model routing for cost-performance optimization.
        """
        # Use selection strategy for intelligent provider/model selection
        task_context = CognitiveTaskContext(
            complexity=complexity,
            requires_reasoning=requires_reasoning,
            requires_code="code" in prompt.lower() or "implement" in prompt.lower(),
            token_estimate=len(prompt.split()) + 500,  # Rough estimate
            latency_preference="balanced"
        )
        
        selection = self.selection_strategy.select_model(task_context)
        provider = selection.provider
        
        # Temporarily override model for this call
        original_model = self.settings.default_model
        self.settings.default_model = selection.model

        logger.info(
            f"[THOUGHT_SERVICE] Selected {provider}/{selection.model} ({selection.depth.value}) "
            f"- est. cost: ${selection.estimated_cost_per_1k:.4f}/1K tokens"
        )

        try:
            if provider == "gemini":
                result = await self._call_gemini(prompt, system_prompt)
            elif provider == "openai":
                result = await self._call_openai(prompt, system_prompt)
            elif provider == "anthropic":
                result = await self._call_anthropic(prompt, system_prompt)
            elif provider == "ollama":
                result = await self._call_ollama(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
            
            logger.info(f"[THOUGHT_SERVICE] {selection.provider}/{selection.model} call successful")
            return result
            
        except Exception as e:
            logger.error(f"LLM Call failed: {str(e)}")
            return f"[ERROR] Autonomous reasoning failed. Fallback to manual mode required. Details: {str(e)}"
        finally:
            # Restore original model
            self.settings.default_model = original_model

    async def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Calls Google AI Studio (Gemini)."""
        # [HARDENING] Use default_model if it's a gemini model, otherwise fallback to gemini-flash-latest (Reliable Free Tier)
        model = self.settings.default_model if self.settings.default_model and "gemini" in self.settings.default_model.lower() else "gemini-flash-latest"
        
        # Strip path if it contains 'models/'
        model_id = model.split("/")[-1]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={self.settings.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.8,
                "topK": 40
            }
        }

        # [UPGRADE] Use dedicated system_instruction field for alignment with v1beta
        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                error_detail = resp.text
                logger.error(f"Gemini API Error {resp.status_code}: {error_detail}")
                raise ValueError(f"Gemini API returned {resp.status_code}: {error_detail}")
                
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                logger.error(f"Unexpected Gemini response format: {data}")
                return "[ERROR] Unexpected response format from Gemini."

    async def _call_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Calls OpenAI-compatible API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.settings.default_model or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Calls Anthropic Messages API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.settings.default_model or "claude-3-5-sonnet-20240620",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_ollama(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Calls Local Ollama API."""
        url = f"{self.settings.ollama_base_url}/api/generate"
        
        payload = {
            "model": self.settings.default_model or "llama3",
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["response"]
