import httpx
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.config import Settings
from src.core.services.llm.client import ClientService

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealth:
    """Health status for a single provider."""
    provider: str
    is_available: bool
    latency_ms: float
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    models_available: List[str] = field(default_factory=list)


@dataclass
class TokenUsageMetrics:
    """Token usage metrics for monitoring."""
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostAlert:
    """Cost overrun alert."""
    alert_type: str  # "daily_limit", "hourly_spike", "budget_threshold"
    current_cost: float
    threshold: float
    severity: str  # "warning", "critical"
    message: str


class MonitorService:
    """
    Enhanced Domain Service for multi-provider LLM diagnostics and monitoring.
    
    Features:
    - Cross-provider health checks (Gemini, OpenAI, Anthropic, Ollama)
    - Performance metrics aggregation
    - Token usage tracking and alerting
    - Cost overrun notifications
    
    Follows DDD 'Lego Principle'.
    """
    
    def __init__(self, settings: Settings, thought_service: ClientService = None):
        self.settings = settings
        self.thought_service = thought_service
        self._health_cache: Dict[str, ProviderHealth] = {}
        self._token_usage_history: List[TokenUsageMetrics] = []
        self._cost_alerts: List[CostAlert] = []
        self._daily_cost: Dict[str, float] = defaultdict(float)  # provider -> cost
        self._last_reset = datetime.now()
    
    async def check_all_providers_health(self) -> Dict[str, ProviderHealth]:
        """
        Check health of all configured providers.
        Returns health status for each provider.
        """
        providers = self._get_configured_providers()
        results = {}
        
        for provider in providers:
            health = await self._check_provider_health(provider)
            results[provider] = health
            self._health_cache[provider] = health
        
        return results
    
    def _get_configured_providers(self) -> List[str]:
        """Get list of configured providers based on API keys."""
        providers = []
        if self.settings.gemini_api_key:
            providers.append("gemini")
        if self.settings.openai_api_key:
            providers.append("openai")
        if self.settings.anthropic_api_key:
            providers.append("anthropic")
        if self.settings.ollama_base_url:
            providers.append("ollama")
        return providers
    
    async def _check_provider_health(self, provider: str) -> ProviderHealth:
        """Check health of a single provider."""
        start_time = time.time()
        
        try:
            # Probe connectivity
            connectivity = await self.probe_connectivity(provider)
            latency_ms = (time.time() - start_time) * 1000
            
            is_available = connectivity.get("is_operational", False)
            
            # Get available models if provider-specific method exists
            models = []
            if provider == "gemini":
                models_data = await self.list_available_gemini_models()
                models = [m.get("name", "").split("/")[-1] for m in models_data]
            
            # Update consecutive failures tracking
            prev_health = self._health_cache.get(provider)
            consecutive_failures = 0
            if prev_health:
                if is_available:
                    consecutive_failures = 0
                else:
                    consecutive_failures = prev_health.consecutive_failures + 1
            
            return ProviderHealth(
                provider=provider,
                is_available=is_available,
                latency_ms=latency_ms,
                last_success=datetime.now() if is_available else (prev_health.last_success if prev_health else None),
                last_error=connectivity.get("error") if not is_available else None,
                consecutive_failures=consecutive_failures,
                models_available=models
            )
            
        except Exception as e:
            logger.error(f"Health check failed for {provider}: {e}")
            prev_health = self._health_cache.get(provider)
            return ProviderHealth(
                provider=provider,
                is_available=False,
                latency_ms=0,
                last_error=str(e),
                consecutive_failures=(prev_health.consecutive_failures + 1 if prev_health else 1)
            )
    
    async def list_available_gemini_models(self) -> List[Dict[str, Any]]:
        """
        Probes Google AI Studio for models accessible with the current key.
        """
        api_key = self.settings.gemini_api_key
        if not api_key:
            logger.warning("Diagnostics: No Gemini API Key found.")
            return []

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get("models", [])
            except Exception as e:
                logger.error(f"Diagnostics: Gemini Probe failed: {e}")
                return []
    
    async def list_available_openai_models(self) -> List[str]:
        """List available OpenAI models."""
        if not self.settings.openai_api_key:
            return []
        
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return [m.get("id", "") for m in data.get("data", [])]
            except Exception as e:
                logger.error(f"Diagnostics: OpenAI models probe failed: {e}")
                return []
    
    async def probe_connectivity(self, provider: str = "gemini") -> Dict[str, Any]:
        """
        Perform a live 'Thought' probe to verify provider responsiveness.
        """
        logger.info(f"Diagnostics: Probing connectivity for {provider}...")
        
        test_prompt = "Cognitive Probe: Respond with 'READY' if operational."
        test_system = "You are a CCT Diagnostic System."
        
        start_time = time.time()
        
        try:
            # Temporarily override provider settings
            original_provider = self.settings.llm_provider
            self.settings.llm_provider = provider
            
            response = await self.thought_service.generate_thought(test_prompt, test_system)
            latency_ms = (time.time() - start_time) * 1000
            
            # Restore original provider
            self.settings.llm_provider = original_provider
            
            is_success = "READY" in response.upper()
            
            return {
                "provider": provider,
                "status": "success" if is_success else "partial_success",
                "response": response,
                "is_operational": is_success,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "provider": provider,
                "status": "error",
                "error": str(e),
                "is_operational": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def record_token_usage(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage for monitoring."""
        metrics = TokenUsageMetrics(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        
        self._token_usage_history.append(metrics)
        
        # Calculate and record cost
        cost = self._calculate_cost(provider, model, prompt_tokens, completion_tokens)
        self._daily_cost[provider] += cost
        
        # Check for alerts
        self._check_cost_alerts(provider)
    
    def _calculate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD for token usage."""
        # Simplified pricing - in production, use actual pricing API
        pricing = {
            "openai": {
                "gpt-4o-mini": (0.15, 0.60),  # input, output per 1M tokens
                "gpt-4o": (2.50, 10.00),
                "gpt-4-turbo": (10.00, 30.00),
            },
            "anthropic": {
                "claude-3-haiku": (0.25, 1.25),
                "claude-3-sonnet": (3.00, 15.00),
                "claude-3-opus": (15.00, 75.00),
            },
            "gemini": {
                "default": (0.0, 0.0),  # Free tier
            }
        }
        
        provider_pricing = pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, provider_pricing.get("default", (0.0, 0.0)))
        
        input_cost = (prompt_tokens / 1_000_000) * model_pricing[0]
        output_cost = (completion_tokens / 1_000_000) * model_pricing[1]
        
        return input_cost + output_cost
    
    def _check_cost_alerts(self, provider: str) -> None:
        """Check for cost overrun conditions and generate alerts."""
        daily_cost = self._daily_cost[provider]
        
        # Define thresholds
        thresholds = {
            "warning": 10.0,   # $10/day
            "critical": 50.0   # $50/day
        }
        
        if daily_cost > thresholds["critical"]:
            alert = CostAlert(
                alert_type="daily_limit",
                current_cost=daily_cost,
                threshold=thresholds["critical"],
                severity="critical",
                message=f"CRITICAL: Daily cost for {provider} exceeded ${thresholds['critical']}: ${daily_cost:.2f}"
            )
            self._cost_alerts.append(alert)
            logger.error(alert.message)
            
        elif daily_cost > thresholds["warning"]:
            alert = CostAlert(
                alert_type="daily_limit",
                current_cost=daily_cost,
                threshold=thresholds["warning"],
                severity="warning",
                message=f"WARNING: Daily cost for {provider} exceeded ${thresholds['warning']}: ${daily_cost:.2f}"
            )
            self._cost_alerts.append(alert)
            logger.warning(alert.message)
    
    def get_token_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get token usage summary for the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_usage = [u for u in self._token_usage_history if u.timestamp > cutoff]
        
        by_provider = defaultdict(lambda: {"prompt": 0, "completion": 0, "total": 0})
        
        for usage in recent_usage:
            by_provider[usage.provider]["prompt"] += usage.prompt_tokens
            by_provider[usage.provider]["completion"] += usage.completion_tokens
            by_provider[usage.provider]["total"] += usage.total_tokens
        
        total_prompt = sum(u.prompt_tokens for u in recent_usage)
        total_completion = sum(u.completion_tokens for u in recent_usage)
        
        return {
            "period_hours": hours,
            "total_requests": len(recent_usage),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "by_provider": dict(by_provider),
            "estimated_cost_usd": sum(self._daily_cost.values())
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary for all providers."""
        if not self._health_cache:
            return {"status": "unknown", "providers": []}
        
        available_count = sum(1 for h in self._health_cache.values() if h.is_available)
        total_count = len(self._health_cache)
        
        return {
            "status": "healthy" if available_count > 0 else "degraded" if total_count > 0 else "down",
            "available_providers": available_count,
            "total_providers": total_count,
            "providers": {
                name: {
                    "is_available": h.is_available,
                    "latency_ms": round(h.latency_ms, 2),
                    "consecutive_failures": h.consecutive_failures,
                    "last_error": h.last_error,
                    "models_count": len(h.models_available)
                }
                for name, h in self._health_cache.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_alerts(self, clear: bool = False) -> List[CostAlert]:
        """Get current alerts, optionally clearing them."""
        alerts = self._cost_alerts.copy()
        if clear:
            self._cost_alerts.clear()
        return alerts
    
    def reset_daily_costs(self) -> None:
        """Reset daily cost tracking (call at midnight)."""
        self._daily_cost.clear()
        self._last_reset = datetime.now()
        logger.info("[DIAGNOSTICS] Daily cost tracking reset")
