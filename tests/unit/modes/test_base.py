import pytest
from pydantic import BaseModel, ValidationError
from src.modes.base import BaseCognitiveEngine
from src.core.models.domain import EnhancedThought, CCTSessionState, ThoughtMetrics
from src.core.models.enums import ThoughtType, ThinkingStrategy, CCTProfile
from src.core.models.contexts import SequentialContext


class MockCognitiveEngine(BaseCognitiveEngine):
    """Mock implementation of BaseCognitiveEngine for testing."""
    
    @property
    def strategy_type(self) -> ThinkingStrategy:
        return ThinkingStrategy.SYSTEMATIC
    
    def execute(self, session_id: str, input_payload: dict) -> dict:
        """Mock execute method."""
        session = self._get_session_or_raise(session_id)
        
        thought = EnhancedThought(
            id=self._generate_thought_id("test"),
            session_id=session_id,
            content="Mock thought content",
            thought_type=ThoughtType.ANALYSIS,
            strategy=self.strategy_type.value,
            sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
        )
        
        self._score_and_save(session_id, thought, [], "claude-3-5-sonnet-20240620")
        
        return {
            "status": "success",
            "generated_thought_id": thought.id
        }


class PayloadSchemaForTest(BaseModel):
    """Test schema for payload validation."""
    required_field: str
    optional_field: int = 10


def test_base_cognitive_engine_init(memory_manager, sequential_engine):
    """Test BaseCognitiveEngine initialization."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    assert engine.memory == memory_manager
    assert engine.sequential == sequential_engine
    assert engine.scoring is not None


def test_strategy_type_property(memory_manager, sequential_engine):
    """Test that strategy_type property returns correct enum."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    assert engine.strategy_type == ThinkingStrategy.SYSTEMATIC


def test_generate_thought_id(memory_manager, sequential_engine):
    """Test thought ID generation."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    thought_id = engine._generate_thought_id("test")
    
    assert thought_id.startswith("test_")
    assert "_" in thought_id
    # Format: prefix_timestamp_uuid
    parts = thought_id.split("_")
    assert len(parts) == 3


def test_generate_thought_id_uniqueness(memory_manager, sequential_engine):
    """Test that generated thought IDs are unique."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    id1 = engine._generate_thought_id("test")
    id2 = engine._generate_thought_id("test")
    
    assert id1 != id2


def test_get_session_or_raise_valid(memory_manager, sequential_engine):
    """Test getting valid session."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    retrieved = engine._get_session_or_raise(session.session_id)
    assert retrieved.session_id == session.session_id


def test_get_session_or_raise_invalid(memory_manager, sequential_engine):
    """Test that invalid session raises ValueError."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    with pytest.raises(ValueError, match="Active session 'invalid' not found"):
        engine._get_session_or_raise("invalid")


def test_get_thought_or_raise_valid(memory_manager, sequential_engine):
    """Test getting valid thought."""
    import uuid
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    thought_id = f"thought_{uuid.uuid4().hex[:8]}"
    thought = EnhancedThought(
        id=thought_id,
        session_id=session.session_id,
        content="Test thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    memory_manager.save_thought(session.session_id, thought)
    
    retrieved = engine._get_thought_or_raise(thought_id)
    
    assert retrieved.id == thought_id


def test_get_thought_or_raise_invalid(memory_manager, sequential_engine):
    """Test that invalid thought raises ValueError."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    with pytest.raises(ValueError, match="Thought 'invalid' not found"):
        engine._get_thought_or_raise("invalid")


def test_validate_session_id_valid(memory_manager, sequential_engine):
    """Test validating valid session ID."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    # Should not raise exception
    engine._validate_session_id(session.session_id)


def test_validate_session_id_invalid(memory_manager, sequential_engine):
    """Test that invalid session ID raises ValueError."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    with pytest.raises(ValueError, match="invalid"):
        engine._validate_session_id("session@123")


def test_validate_payload_valid(memory_manager, sequential_engine):
    """Test validating valid payload."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    payload = {"required_field": "test_value", "optional_field": 20}
    
    validated = engine._validate_payload(payload, PayloadSchemaForTest)
    
    assert validated.required_field == "test_value"
    assert validated.optional_field == 20


def test_validate_payload_missing_required(memory_manager, sequential_engine):
    """Test that missing required field raises ValueError."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    payload = {"optional_field": 20}
    
    with pytest.raises(ValueError, match="Invalid payload for MockCognitiveEngine"):
        engine._validate_payload(payload, PayloadSchemaForTest)


def test_validate_payload_invalid_type(memory_manager, sequential_engine):
    """Test that invalid type raises ValueError."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    payload = {"required_field": "test", "optional_field": "invalid"}
    
    with pytest.raises(ValueError, match="Invalid payload for MockCognitiveEngine"):
        engine._validate_payload(payload, PayloadSchemaForTest)


def test_link_thought_to_parent_valid(memory_manager, sequential_engine):
    """Test linking thought to valid parent."""
    import uuid
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    parent_id = f"parent_{uuid.uuid4().hex[:8]}"
    child_id = f"child_{uuid.uuid4().hex[:8]}"
    
    parent = EnhancedThought(
        id=parent_id,
        session_id=session.session_id,
        content="Parent thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    memory_manager.save_thought(session.session_id, parent)
    
    child = EnhancedThought(
        id=child_id,
        session_id=session.session_id,
        content="Child thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        parent_id=parent_id,
        sequential_context=SequentialContext(thought_number=2, estimated_total_thoughts=5)
    )
    
    engine._link_thought_to_parent(session.session_id, child)
    
    # Verify parent was updated
    updated_parent = memory_manager.get_thought(parent_id)
    assert child_id in updated_parent.children_ids


def test_link_thought_to_parent_invalid(memory_manager, sequential_engine):
    """Test linking thought to invalid parent (should not fail)."""
    import uuid
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    child = EnhancedThought(
        id=f"child_{uuid.uuid4().hex[:8]}",
        session_id=session.session_id,
        content="Child thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        parent_id="invalid_parent",
        sequential_context=SequentialContext(thought_number=2, estimated_total_thoughts=5)
    )
    
    # Should not raise exception
    engine._link_thought_to_parent(session.session_id, child)


def test_link_thought_no_parent(memory_manager, sequential_engine):
    """Test linking thought with no parent ID."""
    import uuid
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    thought = EnhancedThought(
        id=f"thought_{uuid.uuid4().hex[:8]}",
        session_id=session.session_id,
        content="Thought without parent",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    # Should not raise exception
    engine._link_thought_to_parent(session.session_id, thought)


def test_score_and_save(memory_manager, sequential_engine):
    """Test scoring and saving thought."""
    import uuid
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    thought_id = f"thought_{uuid.uuid4().hex[:8]}"
    thought = EnhancedThought(
        id=thought_id,
        session_id=session.session_id,
        content="This is a detailed thought that should be analyzed and scored properly",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    engine._score_and_save(session.session_id, thought, [], "claude-3-5-sonnet-20240620")
    
    # Verify thought was saved with metrics
    retrieved = memory_manager.get_thought(thought_id)
    assert retrieved.metrics is not None
    assert retrieved.metrics.clarity_score >= 0.0
    assert retrieved.metrics.clarity_score <= 1.0
    assert retrieved.summary is not None


def test_score_and_save_with_parent(memory_manager, sequential_engine):
    """Test scoring and saving thought with parent linking."""
    import uuid
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    parent_id = f"parent_{uuid.uuid4().hex[:8]}"
    child_id = f"child_{uuid.uuid4().hex[:8]}"
    
    parent = EnhancedThought(
        id=parent_id,
        session_id=session.session_id,
        content="Parent thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    memory_manager.save_thought(session.session_id, parent)
    
    child = EnhancedThought(
        id=child_id,
        session_id=session.session_id,
        content="Child thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        parent_id=parent_id,
        sequential_context=SequentialContext(thought_number=2, estimated_total_thoughts=5)
    )
    
    engine._score_and_save(session.session_id, child, [parent], "claude-3-5-sonnet-20240620")
    
    # Verify parent was updated with child ID
    updated_parent = memory_manager.get_thought(parent_id)
    assert child_id in updated_parent.children_ids


def test_execute_full_workflow(memory_manager, sequential_engine):
    """Test full execute workflow."""
    engine = MockCognitiveEngine(memory_manager, sequential_engine)
    
    session = memory_manager.create_session("Test problem", CCTProfile.BALANCED, 5)
    
    result = engine.execute(session.session_id, {})
    
    assert result["status"] == "success"
    assert "generated_thought_id" in result
    
    # Verify thought was saved
    thought = memory_manager.get_thought(result["generated_thought_id"])
    assert thought is not None
    assert thought.metrics is not None
