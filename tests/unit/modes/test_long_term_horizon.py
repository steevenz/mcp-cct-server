import pytest
from src.modes.hybrids.temporal.orchestrator import LongTermHorizonEngine
from src.core.models.enums import ThinkingStrategy, CCTProfile

def test_long_term_horizon_trigger(memory_manager, sequential_engine):
    """Test standard long-term horizon payload triggers a scale projection."""
    import uuid
    session = memory_manager.create_session("Implement Monolithic DB", CCTProfile.BALANCED, 5)
    
    # Generate mock parent
    from src.core.models.domain import EnhancedThought, CCTSessionState
    from src.core.models.enums import ThoughtType, ThinkingStrategy
    from src.core.models.contexts import SequentialContext
    
    target_id = f"tt_arch_{uuid.uuid4().hex[:8]}"
    target = EnhancedThought(
        id=target_id,
        content="We will dump everything into Postgres.",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext()
    )
    memory_manager.save_thought(session.session_id, target)
    
    engine = LongTermHorizonEngine(memory_manager, sequential_engine)
    
    payload = {
        "target_thought_id": target.id,
        "projection_scale": "5_years"
    }
    
    result = engine.execute(session.session_id, payload)
    
    assert result["status"] == "success"
    assert "generated_thought_id" in result
    assert result["projection_scale"] == "5_years"
    
    prompt = memory_manager.get_thought(result["generated_thought_id"])
    assert prompt is not None
    assert prompt.strategy == ThinkingStrategy.LONG_TERM_HORIZON
    assert "5_years" in prompt.content

def test_long_term_horizon_invalid_target(memory_manager, sequential_engine):
    """Test that invalid target thought raises ValueError."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 5)
    
    engine = LongTermHorizonEngine(memory_manager, sequential_engine)
    
    with pytest.raises(ValueError, match="Thought 'not_real' not found"):
        engine.execute(session.session_id, {"target_thought_id": "not_real"})
