import pytest
from src.modes.hybrids.multi_agent.orchestrator import MultiAgentFusionEngine
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.models.enums import ThoughtType, ThinkingStrategy, CCTProfile
from src.core.models.contexts import SequentialContext

def test_multi_agent_fusion_trigger(memory_manager, sequential_engine, fusion_orchestrator):
    """Test multi-agent hybrid payload creates divergent persona nodes and a fusion synthesis."""
    import uuid
    session = memory_manager.create_session("Design a secure auth system", CCTProfile.BALANCED, 10)
    
    # Create target thought
    target_id = f"t_auth_{uuid.uuid4().hex[:8]}"
    target = EnhancedThought(
        id=target_id,
        content="Use JWT with short expiration.",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext()
    )
    memory_manager.save_thought(session.session_id, target)
    
    engine = MultiAgentFusionEngine(memory_manager, sequential_engine, fusion_orchestrator)
    
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

    # Verify fusion result structure
    fusion = memory_manager.get_thought(result["fusion_thought_id"])
    assert fusion is not None
    assert fusion.thought_type == ThoughtType.SYNTHESIS
    assert len(fusion.builds_on) == 2 # 2 Persona Insights as inputs
