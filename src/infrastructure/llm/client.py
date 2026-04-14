import logging
import httpx
from typing import Dict, Any, Optional
from src.core.config import Settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Generic LLM Client for autonomous server-side thought generation.
    Supports Gemini (Google), OpenAI, Anthropic, and Ollama.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def generate_thought(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generates a thought based on the configured provider.
        """
        provider = self.settings.llm_provider
        
        # Auto-detect provider if not explicitly set but keys exist
        if not provider:
            if self.settings.gemini_api_key:
                provider = "gemini"
            elif self.settings.openai_api_key:
                provider = "openai"
            elif self.settings.anthropic_api_key:
                provider = "anthropic"
            else:
                raise ValueError("No LLM Provider configured or auto-detected.")

        logger.info(f"Generating autonomous thought using provider: {provider}")

        try:
            if provider == "gemini":
                return await self._call_gemini(prompt, system_prompt)
            elif provider == "openai":
                return await self._call_openai(prompt, system_prompt)
            elif provider == "anthropic":
                return await self._call_anthropic(prompt, system_prompt)
            elif provider == "ollama":
                return await self._call_ollama(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        except Exception as e:
            logger.error(f"LLM Call failed: {str(e)}")
            return f"[ERROR] Autonomous reasoning failed. Fallback to manual mode required. Details: {str(e)}"

    async def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Calls Google AI Studio (Gemini 1.5 Flash)."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.settings.gemini_api_key}"
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.8,
                "topK": 40
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

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
