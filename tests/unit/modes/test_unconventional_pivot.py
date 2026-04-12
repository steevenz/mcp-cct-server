import pytest
from src.modes.hybrids.lateral.orchestrator import LateralEngine
from src.core.models.enums import ThinkingStrategy, CCTProfile

def test_unconventional_pivot_trigger(memory_manager, sequential_engine):
    """Test hybrid payload correctly injects a provocation mechanism and flags for lateral sequence split."""
    session = memory_manager.create_session("Build caching layer", CCTProfile.BALANCED, 5)
    
    engine = LateralEngine(memory_manager, sequential_engine)
    
    payload = {
        "current_paradigm": "Redis based caching locally",
        "provocation_method": "INVERSION"
    }
    
    result = engine.execute(session.session_id, payload)
    
    # Assert successful orchestration
    assert result["status"] == "success"
    assert result["provocation_applied"] == "INVERSION"
    assert "generated_thought_id" in result
    
    # Assert the generated provocation is accurately saved and context branching occurs
    provocation = memory_manager.get_thought(result["generated_thought_id"])
    assert provocation is not None
    assert provocation.strategy == ThinkingStrategy.UNCONVENTIONAL_PIVOT
    
    # Verify sequence engine tracking caught the implicit revision flag
    assert provocation.sequential_context.is_revision is True
    assert provocation.sequential_context.branch_id == "lateral_inversion"

def test_unconventional_invalid_payload(memory_manager, sequential_engine):
    """Test schema payload rejection for UnconventionalPivot."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 3)
    engine = LateralEngine(memory_manager, sequential_engine)
    
    # Missing current_paradigm
    with pytest.raises(ValueError, match="Invalid payload"):
        engine.execute(session.session_id, {"provocation_method": "RANDOM"})
