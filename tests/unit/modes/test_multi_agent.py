import pytest
from src.modes.hybrids.multi_agent.orchestrator import MultiAgentFusionEngine
from src.core.models.enums import ThinkingStrategy, CCTProfile, ThoughtType
from src.core.models.domain import EnhancedThought
from src.engines.sequential.models import SequentialContext

def test_multi_agent_fusion_trigger(memory_manager, sequential_engine):
    """Test multi-agent hybrid payload creates divergent persona nodes and a fusion synthesis."""
    session = memory_manager.create_session("Design a secure auth system", CCTProfile.BALANCED, 10)
    
    # Create target thought
    target = EnhancedThought(
        id="t_auth_base",
        content="Use JWT with short expiration.",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext()
    )
    memory_manager.save_thought(session.session_id, target)
    
    engine = MultiAgentFusionEngine(memory_manager, sequential_engine)
    
    payload = {
        "target_thought_id": target.id,
        "personas": ["Security Hardener", "Frontend Lead"]
    }
    
    result = engine.execute(session.session_id, payload)
    
    assert result["status"] == "success"
    assert len(result["persona_insights"]) == 2
    assert "fusion_thought_id" in result
    
    # Verify persona thoughts exist
    for p_id in result["persona_insights"]:
        p_thought = memory_manager.get_thought(p_id)
        assert p_thought is not None
        assert p_thought.strategy == ThinkingStrategy.CRITICAL
        assert "MULTI-AGENT FUSION" in p_thought.content

    # Verify fusion thought existence and integrity
    fusion = memory_manager.get_thought(result["fusion_thought_id"])
    assert fusion is not None
    assert fusion.strategy == ThinkingStrategy.INTEGRATIVE
    assert fusion.thought_type == ThoughtType.SYNTHESIS
    assert len(fusion.builds_on) == 3 # Target + 2 Personas
