import pytest
from src.core.models.enums import CCTProfile, ThoughtType, ThinkingStrategy
from src.core.models.domain import EnhancedThought
from src.engines.sequential.models import SequentialContext

def test_create_and_get_session(memory_manager):
    """Test full cycle of creating a session and retrieving it from SQLite."""
    session = memory_manager.create_session(
        problem_statement="Solve database scaling",
        profile=CCTProfile.BALANCED,
        estimated_thoughts=3
    )
    
    assert session.session_id is not None
    assert session.problem_statement == "Solve database scaling"
    
    # Retrieve
    retrieved = memory_manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.problem_statement == "Solve database scaling"
    assert retrieved.profile == CCTProfile.BALANCED

def test_save_and_get_thought(memory_manager):
    """Test saving a thought and validating session history appending."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 3)
    
    context = SequentialContext(thought_number=1, estimated_total_thoughts=3)
    thought = EnhancedThought(
        id="thought_idx_1",
        content="Testing thought",
        thought_type=ThoughtType.OBSERVATION,
        strategy=ThinkingStrategy.LINEAR,
        sequential_context=context
    )
    
    memory_manager.save_thought(session.session_id, thought)
    
    retrieved_thought = memory_manager.get_thought("thought_idx_1")
    assert retrieved_thought is not None
    assert retrieved_thought.id == "thought_idx_1"
    
    # Validates history appending works correctly in SQLite representation
    history = memory_manager.get_session_history(session.session_id)
    assert len(history) == 1
    assert history[0].id == "thought_idx_1"

def test_get_invalid_objects(memory_manager):
    """Test getting invalid references gracefully returns None, protecting against crashes."""
    assert memory_manager.get_session("void") is None
    assert memory_manager.get_thought("void") is None

def test_update_session(memory_manager):
    """Test that modifying a session and explicitly updating it persists changes."""
    session = memory_manager.create_session("Test", CCTProfile.BALANCED, 3)
    session.status = "completed"
    
    memory_manager.update_session(session)
    
    retrieved = memory_manager.get_session(session.session_id)
    assert retrieved.status == "completed"
