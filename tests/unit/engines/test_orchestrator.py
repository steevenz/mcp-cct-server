import pytest
from src.core.models.enums import ThinkingStrategy

def test_execute_strategy_valid(orchestrator):
    """Test routing to a valid primitive strategy ensures it hits the DynamicPrimitiveEngine."""
    payload = {
        "thought_content": "This is a basic test note",
        "thought_type": "observation",
        "strategy": "systematic",
        "thought_number": 1,
        "estimated_total_thoughts": 3,
        "next_thought_needed": True
    }
    
    from src.core.models.enums import ThinkingStrategy, CCTProfile
    session = orchestrator.memory.create_session("Test problem", CCTProfile.BALANCED, 3)
    
    # Executing the strategy should return the expected JSON output format from the Engine
    result = orchestrator.execute_strategy(
        session_id=session.session_id, 
        strategy=ThinkingStrategy.SYSTEMATIC, 
        payload=payload
    )
    
    assert result.get("status") == "success"
    assert result.get("generated_thought_id") is not None

def test_start_session(orchestrator):
    """Verify start_session initializes SQL memory properly via the Orchestrator Facade."""
    result = orchestrator.start_session("What is the meaning of life?", "balanced")
    
    assert result.get("status") == "success"
    assert "session_id" in result
    
    saved_session = orchestrator.memory.get_session(result["session_id"])
    assert saved_session is not None
    assert saved_session.problem_statement == "What is the meaning of life?"
