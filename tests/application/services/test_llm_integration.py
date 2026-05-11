import pytest

from src.core.config import load_settings
from src.core.models.llm.config import CognitiveTaskContext
from src.core.services.llm.client import ClientService, GENERIC_LLM_ERROR
from src.core.services.llm.critic import CriticService
from src.core.services.llm.monitor import MonitorService
from src.core.services.llm.router import RouterService


def _build_settings(monkeypatch, **overrides):
    keys = {
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "GEMINI_API_KEY": "",
        "OLLAMA_BASE_URL": "",
        "CCT_LLM_PROVIDER": "",
        "CCT_BOOTSTRAP_API_KEY": "test-bootstrap-key",
    }
    keys.update(overrides)
    for key, value in keys.items():
        monkeypatch.setenv(key, value)
    return load_settings()


def test_router_select_model_uses_valid_cost_table(monkeypatch):
    settings = _build_settings(monkeypatch, OPENAI_API_KEY="test-openai-key", CCT_LLM_PROVIDER="openai")
    router = RouterService(settings)

    selection = router.select_model(
        CognitiveTaskContext(
            complexity="moderate",
            requires_reasoning=False,
            requires_code=False,
            token_estimate=1000,
            latency_preference="balanced",
        )
    )

    assert selection.provider == "openai"
    stats = router.get_stats()
    assert stats["total_requests"] == 1
    assert isinstance(stats["cost_savings"], float)


def test_router_rejects_unconfigured_provider_override(monkeypatch):
    settings = _build_settings(monkeypatch, OPENAI_API_KEY="test-openai-key", CCT_LLM_PROVIDER="openai")
    router = RouterService(settings)

    with pytest.raises(ValueError, match="not configured"):
        router.select_model(
            CognitiveTaskContext(
                complexity="simple",
                requires_reasoning=False,
                requires_code=False,
                token_estimate=500,
                latency_preference="fast",
            ),
            provider_override="anthropic",
        )


@pytest.mark.asyncio
async def test_monitor_probe_connectivity_uses_provider_override(monkeypatch):
    settings = _build_settings(monkeypatch, OPENAI_API_KEY="test-openai-key", CCT_LLM_PROVIDER="openai")

    class DummyThoughtService:
        def __init__(self):
            self.provider_override = None

        async def generate_thought(self, prompt, system_prompt=None, complexity="moderate", requires_reasoning=False, provider_override=None):
            del prompt, system_prompt, complexity, requires_reasoning
            self.provider_override = provider_override
            return "READY"

    thought_service = DummyThoughtService()
    monitor = MonitorService(settings, thought_service=thought_service)
    result = await monitor.probe_connectivity(provider="openai")

    assert result["is_operational"] is True
    assert thought_service.provider_override == "openai"


@pytest.mark.asyncio
async def test_client_service_returns_sanitized_error(monkeypatch):
    settings = _build_settings(monkeypatch, OPENAI_API_KEY="test-openai-key", CCT_LLM_PROVIDER="openai")
    service = ClientService(settings)

    async def _raise_error(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("SECRET_TOKEN=leak")

    service._call_openai = _raise_error  # type: ignore[method-assign]
    result = await service.generate_thought("hello")
    await service.aclose()

    assert result == GENERIC_LLM_ERROR
    assert "SECRET_TOKEN" not in result


@pytest.mark.asyncio
async def test_client_service_closes_pooled_http_client(monkeypatch):
    settings = _build_settings(monkeypatch, OPENAI_API_KEY="test-openai-key", CCT_LLM_PROVIDER="openai")
    service = ClientService(settings)
    assert service._http_client.is_closed is False
    await service.aclose()
    assert service._http_client.is_closed is True


@pytest.mark.asyncio
async def test_critic_cache_ttl_and_hash(monkeypatch):
    settings = _build_settings(monkeypatch, OPENAI_API_KEY="test-openai-key", CCT_LLM_PROVIDER="openai")
    critic = CriticService(settings)

    key = critic._get_cache_key("prompt", "system", "persona")
    assert len(key) == 64

    outcome = await critic.review("content", "persona", primary_thought_service=None)
    assert outcome.source == "persona"

    cached_key = critic._get_cache_key("A", "B", "C")
    critic._cache[cached_key] = (outcome, 0.0)
    critic._cache_ttl_seconds = 1

    assert critic._get_cached(cached_key) is None
    await critic.aclose()
