"""
AdversarialReviewService: Cross-Model Audit for True Adversarial Review.

Implements the 'Gold Standard' external cross-model audit pattern from CCT v5.0.
Routes review phase to a separate model architecture to eliminate sycophancy bias.

Features:
- Configurable external review endpoint (GPT-4o, DeepSeek, Local LLM)
- Fallback chain: External → Primary LLM → Internal Persona
- Response caching to prevent duplicate API costs
- Timeout handling with graceful degradation
"""

import logging
import hashlib
import time
from typing import Dict, Any, Optional

import httpx
from src.core.config import Settings
from src.core.models import ReviewOutcome
from src.core.services.user.identity import UserIdentityService

logger = logging.getLogger(__name__)


class CriticService:
    """
    Adversarial Review Service for cross-model audit.
    
    Provides true adversarial review by routing review to a separate model,
    eliminating the 'echo chamber' effect of same-model actor-critic.
    
    DIGITAL TWIN IMPLEMENTATION: Injects the human master's identity (USER_MINDSET + CCT_SOUL)
    into external LLM calls to ensure the critic behaves as the human master, not as a generic auditor.
    """
    
    def __init__(self, settings: Settings, identity_service: UserIdentityService = None):
        self.settings = settings
        self.identity = identity_service
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self._cache: Dict[str, ReviewOutcome] = {}
        self._cache_ttl_seconds = 3600  # 1 hour cache
        
        # Critic configuration from environment
        self.critic_api_url = getattr(settings, 'critic_llm_api_url', None)
        self.critic_model = getattr(settings, 'critic_model', None)
        self.critic_api_key = getattr(settings, 'critic_api_key', None)
        self.critic_provider = getattr(settings, 'critic_provider', None)
        
        # Enable/disable external critic
        self.enabled = bool(self.critic_api_url or self.critic_provider)
        
        if self.enabled:
            logger.info(f"[REVIEW] External cross-model audit enabled: {self.critic_provider or 'custom'}")
        else:
            logger.info("[REVIEW] External review not configured. Will use fallback chain.")
    
    def _get_cache_key(self, prompt: str, system_prompt: Optional[str], persona: str) -> str:
        """Generate cache key for critic requests."""
        content = f"{prompt}:{system_prompt}:{persona}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached(self, cache_key: str) -> Optional[ReviewOutcome]:
        """Retrieve cached review if valid."""
        if cache_key not in self._cache:
            return None
        
        cached = self._cache[cache_key]
        # Check if cache is still valid (simplified - in production use proper TTL)
        return cached
    
    def _cache_response(self, cache_key: str, review: ReviewOutcome) -> None:
        """Cache review outcome."""
        self._cache[cache_key] = review
        logger.debug(f"[REVIEW] Cached review for key: {cache_key[:8]}...")
    
    async def review(
        self, 
        target_content: str,
        persona: str,
        system_prompt: Optional[str] = None,
        primary_thought_service: Optional[Any] = None
    ) -> ReviewOutcome:
        """
        Execute cross-model adversarial review with fallback chain.
        
        Chain: External Review → Primary LLM → Internal Persona (simulated)
        
        DIGITAL TWIN: The external LLM (critic) receives the human master's identity prompts
        to behave as the human master, ensuring consistency with the Digital Twin paradigm.
        """
        # Prepare review prompt
        review_prompt = (
            f"AUDIT TARGET:\n{target_content}\n\n"
            f"PERSONA: {persona}\n\n"
            f"TASK: Identify flaws, vulnerabilities, or bottlenecks from your specialized perspective. "
            f"Be ruthlessly critical. Focus on architectural weaknesses, security risks, performance issues, "
            f"and any assumptions that may not hold under stress."
        )
        
        default_sys_prompt = f"You are a {persona} expert. Critically attack the provided proposal with no mercy."
        
        # [DIGITAL TWIN] Inject identity layer into system prompt for external LLM
        # This ensures the external critic behaves as the human master, not a generic auditor
        if self.identity:
            try:
                identity_context = self.identity.load_identity()
                identity_prefix = self.identity.format_system_prefix(identity_context)
                # Decorate the system prompt with Digital Twin identity
                if system_prompt:
                    final_system_prompt = f"{identity_prefix}\n\n{system_prompt}"
                else:
                    final_system_prompt = f"{identity_prefix}\n\n{default_sys_prompt}"
                logger.debug("[REVIEW] Digital Twin identity injected into external LLM system prompt")
            except Exception as e:
                logger.warning(f"[REVIEW] Failed to load identity for external LLM: {e}. Using fallback.")
                final_system_prompt = system_prompt or default_sys_prompt
        else:
            final_system_prompt = system_prompt or default_sys_prompt
        
        # Check cache
        cache_key = self._get_cache_key(review_prompt, final_system_prompt, persona)
        cached = self._get_cached(cache_key)
        if cached:
            logger.info("[REVIEW] Cache hit - returning cached review")
            return ReviewOutcome(
                content=cached.content,
                source=f"{cached.source}_cached",
                cached=True,
                latency_ms=0.0
            )
        
        start_time = time.time()
        
        # TIER 1: Try external review if configured
        if self.enabled:
            try:
                logger.info(f"[REVIEW] Attempting external review via {self.critic_provider or 'custom endpoint'}")
                external_response = await self._call_external_review(
                    review_prompt, 
                    final_system_prompt
                )
                latency = (time.time() - start_time) * 1000
                
                review = ReviewOutcome(
                    content=external_response,
                    source="external",
                    cached=False,
                    latency_ms=latency
                )
                self._cache_response(cache_key, review)
                logger.info(f"[REVIEW] External review successful ({latency:.0f}ms)")
                return review
                
            except Exception as e:
                logger.warning(f"[REVIEW] External review failed: {e}. Falling back to primary thought service.")
        
        # TIER 2: Fallback to primary thought service
        if primary_thought_service:
            try:
                logger.info("[REVIEW] Attempting primary thought service review")
                primary_response = await primary_thought_service.generate_thought(
                    prompt=review_prompt,
                    system_prompt=final_system_prompt
                )
                latency = (time.time() - start_time) * 1000
                
                review = ReviewOutcome(
                    content=primary_response,
                    source="primary",
                    cached=False,
                    latency_ms=latency
                )
                self._cache_response(cache_key, review)
                logger.info(f"[REVIEW] Primary thought service review successful ({latency:.0f}ms)")
                return review
                
            except Exception as e:
                logger.warning(f"[REVIEW] Primary thought service failed: {e}. Falling back to persona simulation.")
        
        # TIER 3: Fallback to internal persona simulation (synthetic review)
        logger.info("[REVIEW] Using persona simulation fallback")
        synthetic_response = self._generate_synthetic_review(target_content, persona)
        latency = (time.time() - start_time) * 1000
        
        review = ReviewOutcome(
            content=synthetic_response,
            source="persona",
            cached=False,
            latency_ms=latency
        )
        # Don't cache synthetic responses
        return review
    
    async def _call_external_review(self, prompt: str, system_prompt: str) -> str:
        """Call external review API."""
        if self.critic_provider == "openai":
            return await self._call_openai_review(prompt, system_prompt)
        elif self.critic_provider == "anthropic":
            return await self._call_anthropic_review(prompt, system_prompt)
        elif self.critic_provider == "ollama":
            return await self._call_ollama_review(prompt, system_prompt)
        elif self.critic_api_url:
            return await self._call_custom_review(prompt, system_prompt)
        else:
            raise ValueError("No review provider configured")
    
    async def _call_openai_review(self, prompt: str, system_prompt: str) -> str:
        """Call OpenAI-compatible review API."""
        url = self.critic_api_url or "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.critic_api_key or self.settings.openai_api_key}"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.critic_model or "gpt-4o",
            "messages": messages,
            "temperature": 0.2
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_anthropic_review(self, prompt: str, system_prompt: str) -> str:
        """Call Anthropic review API."""
        url = self.critic_api_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.critic_api_key or self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.critic_model or "claude-3-opus-20240229",
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
    
    async def _call_ollama_review(self, prompt: str, system_prompt: str) -> str:
        """Call Ollama review API."""
        url = f"{self.critic_api_url or self.settings.ollama_base_url}/api/generate"
        
        payload = {
            "model": self.critic_model or "llama3",
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["response"]
    
    async def _call_custom_review(self, prompt: str, system_prompt: str) -> str:
        """Call custom review endpoint."""
        # Generic OpenAI-compatible endpoint
        headers = {}
        if self.critic_api_key:
            headers["Authorization"] = f"Bearer {self.critic_api_key}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.critic_model or "gpt-4",
            "messages": messages,
            "temperature": 0.2
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.critic_api_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    
    def _generate_synthetic_review(self, target_content: str, persona: str) -> str:
        """
        Generate synthetic review when all LLM options fail.
        This is a structured template-based review to maintain utility.
        """
        logger.warning("[REVIEW] Generating synthetic review - all LLM depths failed")
        
        # Template-based review structure
        return (
            f"[SYNTHETIC REVIEW - {persona} MODE]\n\n"
            f"AUDIT TARGET: {target_content[:200]}...\n\n"
            f"CRITICAL OBSERVATIONS:\n"
            f"1. ASSUMPTIONS: The proposal contains unverified assumptions about system state.\n"
            f"2. EDGE CASES: Edge case handling may be incomplete.\n"
            f"3. SCALABILITY: Scalability considerations require validation.\n"
            f"4. ERROR HANDLING: Error paths need explicit testing.\n\n"
            f"RECOMMENDATION: Review with domain expert before implementation.\n\n"
            f"[NOTE: This is a synthetic fallback review. For production use, configure external review.]"
        )
    
    def clear_cache(self) -> None:
        """Clear review response cache."""
        self._cache.clear()
        logger.info("[REVIEW] Response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_entries": len(self._cache),
            "cache_ttl_seconds": self._cache_ttl_seconds,
            "external_enabled": self.enabled,
            "critic_provider": self.critic_provider,
            "critic_model": self.critic_model
        }
