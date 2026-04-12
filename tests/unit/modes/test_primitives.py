import pytest
from src.modes.primitives.orchestrator import DynamicPrimitiveEngine
from src.core.models.enums import ThinkingStrategy, ThoughtType, CCTProfile

# Exhaustive list of primitives derived from ThinkingStrategy (except hybrids)
HYBRID_STRATEGIES = [
    ThinkingStrategy.ACTOR_CRITIC_LOOP,
    ThinkingStrategy.UNCONVENTIONAL_PIVOT,
    ThinkingStrategy.LONG_TERM_HORIZON,
    ThinkingStrategy.MULTI_AGENT_FUSION
]
ALL_PRIMITIVES = [s for s in ThinkingStrategy if s not in HYBRID_STRATEGIES]

@pytest.mark.parametrize("strategy", ALL_PRIMITIVES)
def test_all_primitives_traversal(memory_manager, sequential_engine, strategy):
    """Verify that every primitive defined in ThinkingStrategy can be orchestrated."""
    session = memory_manager.create_session(f"Testing {strategy.value}", CCTProfile.BALANCED, 5)
    engine = DynamicPrimitiveEngine(memory_manager, sequential_engine, strategy)
    
    payload = {
        "thought_content": f"Analyzing using {strategy.value}",
        "thought_type": "analysis",
        "strategy": strategy.value,
        "thought_number": 1,
        "estimated_total_thoughts": 5,
        "next_thought_needed": True
    }
    
    result = engine.execute(session.session_id, payload)
    
    assert result["status"] == "success"
    assert "generated_thought_id" in result
    assert result["orchestration_mode"] == strategy.value
    
    saved_thought = memory_manager.get_thought(result["generated_thought_id"])
    assert saved_thought is not None
    assert saved_thought.strategy == strategy

def test_invalid_payload_rejection(memory_manager, sequential_engine):
    """Verify that malformed JSON payloads throw ValueError."""
    session = memory_manager.create_session("Test Error", CCTProfile.BALANCED, 3)
    engine = DynamicPrimitiveEngine(memory_manager, sequential_engine, ThinkingStrategy.LINEAR)
    
    with pytest.raises(ValueError, match="Invalid payload"):
        engine.execute(session.session_id, {"broken": "data"})
