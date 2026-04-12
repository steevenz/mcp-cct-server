import pytest
from src.engines.sequential.engine import SequentialEngine
from src.core.models.enums import CCTProfile

@pytest.fixture
def sequential_engine(memory_manager):
    return SequentialEngine(memory_manager)

def test_sequence_anti_hallucination(memory_manager, sequential_engine):
    """Ensure LLM skipping a completely invalid sequence number is auto-corrected."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 5)
    session_id = session.session_id
    
    # Valid first step
    ctx1 = sequential_engine.process_sequence_step(
        session_id=session_id,
        llm_thought_number=1,
        llm_estimated_total=5,
        next_thought_needed=True
    )
    assert ctx1.thought_number == 1
    
    # Simulated hallucination: the LLM suddenly skips to thought 5
    ctx2 = sequential_engine.process_sequence_step(
        session_id=session_id,
        llm_thought_number=5,
        llm_estimated_total=5,
        next_thought_needed=True
    )
    
    # Must be hard-corrected to 2
    assert ctx2.thought_number == 2

def test_dynamic_expansion_logic(memory_manager, sequential_engine):
    """Validates that checking 'is_revision' extends the thought tracks dynamically."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 3)
    
    # If the LLM indicates a revision is happening, bounds augment
    ctx = sequential_engine.process_sequence_step(
        session_id=session.session_id,
        llm_thought_number=1,
        llm_estimated_total=3,
        next_thought_needed=True,
        is_revision=True
    )
    
    # Evaluated bounds dynamically extended (+2 for revision)
    assert ctx.estimated_total_thoughts >= 5

def test_convergence_blocking(memory_manager, sequential_engine):
    """Validates the system blocks premature exit if constraints are unmet."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 5)
    
    # Try converging without history
    converg = sequential_engine.evaluate_convergence(session.session_id, next_thought_needed=False)
    assert not converg["is_ready"]
    assert "depth" in converg["reason"].lower()
    
    # Try converging with an LLM explicitly requesting continuation
    converg_needed = sequential_engine.evaluate_convergence(session.session_id, next_thought_needed=True)
    assert not converg_needed["is_ready"]

def test_missing_session_exception(sequential_engine):
    """Validate safe exception handling when requesting an invalid session"""
    with pytest.raises(ValueError, match="not found"):
        sequential_engine.process_sequence_step("invalid", 1, 5, True)
