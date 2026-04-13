import pytest
from src.utils.harness import TokenHarness
from src.core.models.domain import CCTSessionState
from src.core.models.enums import CCTProfile

def test_token_harness_calculation():
    harness = TokenHarness()
    
    # Test Claude 3.5 Sonnet ($3 / $15 per 1M)
    # 1000 input, 1000 output -> 0.003 + 0.015 = 0.018
    cost = harness.calculate_cost("claude-3-5-sonnet-20240620", 1000, 1000)
    assert cost == 0.018

    # Test GPT-4o ($5 / $15 per 1M)
    # 1000 input, 1000 output -> 0.005 + 0.015 = 0.020
    cost = harness.calculate_cost("gpt-4o", 1000, 1000)
    assert cost == 0.020

def test_efficiency_metrics():
    harness = TokenHarness()
    
    state = CCTSessionState(
        session_id="test-session",
        problem_statement="test",
        profile=CCTProfile.BALANCED,
        current_thought_number=10,
        total_prompt_tokens=5000,
        total_completion_tokens=5000,
        total_cost_usd=0.10,
        consistency_score=0.8
    )
    
    metrics = harness.get_efficiency_metrics(state)
    
    # 10 thoughts / 10K tokens * 1000 = 1.0 thoughts per 1K tokens
    assert metrics["token_efficiency_idx"] == 1.0
    
    # 0.8 consistency / 0.10 cost = 8.0 consistency per $1
    assert metrics["cost_efficiency_idx"] == 8.0
    
    # 0.10 cost / 10 thoughts = 0.01 per thought
    assert metrics["avg_cost_per_thought"] == 0.01

def test_registry_fallback():
    harness = TokenHarness(pricing_path="non_existent.json")
    # Should fallback to default (Sonnet prices)
    cost = harness.calculate_cost("unknown-model", 1000, 1000)
    assert cost == 0.018
