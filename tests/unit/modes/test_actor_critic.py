import pytest
from src.modes.hybrids.actor_critic.orchestrator import ActorCriticEngine
from src.core.models.enums import ThinkingStrategy, CCTProfile

def test_actor_critic_trigger(memory_manager, sequential_engine):
    """Test standard hybrid payload injects context and prompts into the session flow."""
    session = memory_manager.create_session("Refactor to DDD", CCTProfile.BALANCED, 5)
    
    # 1. Create the parent (target) thought utilizing direct storage
    from src.core.models.domain import EnhancedThought
    from src.engines.sequential.models import SequentialContext
    from src.core.models.enums import ThoughtType
    
    target = EnhancedThought(
        id="tt_target_1",
        content="We should use a layered DDD approach.",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext()
    )
    memory_manager.save_thought(session.session_id, target)
    
    # 2. Trigger the Actor-Critic proxy
    engine = ActorCriticEngine(memory_manager, sequential_engine)
    
    payload = {
        "target_thought_id": target.id,
        "critic_persona": "DevOps Architect"
    }
    
    result = engine.execute(session.session_id, payload)
    
    # Assert successful orchestration and internal prompt generation
    assert result["status"] == "success"
    assert result["target_thought_id"] == target.id
    
    # Assert the generated prompt was safely persisted
    prompt_thought = memory_manager.get_thought(result["critic_phase"]["generated_id"])
    assert prompt_thought is not None
    assert prompt_thought.strategy == ThinkingStrategy.CRITICAL
    assert prompt_thought.thought_type == ThoughtType.EVALUATION
    assert "DevOps Architect" in prompt_thought.content

def test_actor_critic_missing_target(memory_manager, sequential_engine):
    """Test safely catching an execution call for a ghost parent node."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 3)
    engine = ActorCriticEngine(memory_manager, sequential_engine)
    
    with pytest.raises(ValueError, match="Target thought 'not_real' not found in memory registry"):
        engine.execute(session.session_id, {"target_thought_id": "not_real"})
