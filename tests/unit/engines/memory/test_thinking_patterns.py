import pytest
import os
import tempfile
from datetime import datetime
from src.engines.memory.thinking_patterns import PatternArchiver
from src.core.models.domain import EnhancedThought, GoldenThinkingPattern, CCTSessionState, ThoughtMetrics
from src.core.models.enums import ThoughtType, ThinkingStrategy
from src.core.models.contexts import SequentialContext


@pytest.fixture
def temp_docs_root():
    """Create temporary directory for pattern exports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_session():
    """Create sample session state."""
    return CCTSessionState(
        session_id="test_session",
        problem_statement="Design a scalable microservices architecture",
        profile="balanced",
        status="active"
    )


@pytest.fixture
def high_quality_thought():
    """Create a thought that meets pattern thresholds."""
    return EnhancedThought(
        id="thought_1",
        session_id="test_session",
        content="Implement event-driven architecture with message brokers for loose coupling and scalability",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        summary="Event-driven architecture pattern",
        metrics=ThoughtMetrics(
            logical_coherence=0.95,
            evidence_strength=0.85,
            clarity_score=0.9
        ),
        tags=["architecture", "scalability"]
    )


@pytest.fixture
def low_quality_thought():
    """Create a thought that doesn't meet pattern thresholds."""
    return EnhancedThought(
        id="thought_2",
        session_id="test_session",
        content="Basic thought without evidence",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.LINEAR,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        metrics=ThoughtMetrics(
            logical_coherence=0.5,
            evidence_strength=0.3,
            clarity_score=0.6
        )
    )


def test_pattern_archiver_init(memory_manager, temp_docs_root):
    """Test PatternArchiver initialization."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    assert archiver.memory == memory_manager
    assert archiver.docs_root == temp_docs_root
    assert os.path.exists(temp_docs_root)


def test_process_thought_high_quality(memory_manager, temp_docs_root, sample_session, high_quality_thought):
    """Test processing a high-quality thought that becomes a pattern."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    pattern = archiver.process_thought(sample_session, high_quality_thought)
    
    assert pattern is not None
    assert pattern.id.startswith("TP_")
    assert pattern.thought_id == high_quality_thought.id
    assert pattern.session_id == sample_session.session_id
    assert pattern.original_problem == sample_session.problem_statement
    assert pattern.metrics.logical_coherence == 0.95
    assert pattern.metrics.evidence_strength == 0.85
    assert pattern.usage_count == 1
    assert pattern.timestamp is not None


def test_process_thought_low_quality(memory_manager, temp_docs_root, sample_session, low_quality_thought):
    """Test processing a low-quality thought that doesn't become a pattern."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    pattern = archiver.process_thought(sample_session, low_quality_thought)
    
    assert pattern is None


def test_process_thought_threshold_logic_low_coherence(memory_manager, temp_docs_root, sample_session):
    """Test that low coherence prevents pattern creation."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    thought = EnhancedThought(
        id="thought_1",
        session_id="test_session",
        content="Valid content",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        metrics=ThoughtMetrics(
            logical_coherence=0.85,  # Below 0.9 threshold
            evidence_strength=0.85
        )
    )
    
    pattern = archiver.process_thought(sample_session, thought)
    assert pattern is None


def test_process_thought_threshold_logic_low_evidence(memory_manager, temp_docs_root, sample_session):
    """Test that low evidence prevents pattern creation."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    thought = EnhancedThought(
        id="thought_1",
        session_id="test_session",
        content="Valid content",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        metrics=ThoughtMetrics(
            logical_coherence=0.95,
            evidence_strength=0.75  # Below 0.8 threshold
        )
    )
    
    pattern = archiver.process_thought(sample_session, thought)
    assert pattern is None


def test_export_to_markdown(memory_manager, temp_docs_root, sample_session, high_quality_thought):
    """Test that pattern is exported to markdown file."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    pattern = archiver.process_thought(sample_session, high_quality_thought)
    
    # Check that topic directory was created
    topic_dir = os.path.join(temp_docs_root, "Systematic")
    assert os.path.exists(topic_dir)
    
    # Check that markdown file was created
    md_file = os.path.join(topic_dir, f"{pattern.id}.md")
    assert os.path.exists(md_file)
    
    # Check file content
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert pattern.id in content
    assert "Golden Thinking Pattern" in content
    assert sample_session.problem_statement in content


def test_ensure_context_md(memory_manager, temp_docs_root):
    """Test that context.md files are created."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    # Create a pattern to trigger context.md creation
    session = CCTSessionState(
        session_id="test_session",
        problem_statement="Test problem",
        profile="balanced",
        status="active"
    )
    
    thought = EnhancedThought(
        id="thought_1",
        session_id="test_session",
        content="Valid content with sufficient evidence and logic",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        metrics=ThoughtMetrics(
            logical_coherence=0.95,
            evidence_strength=0.85
        )
    )
    
    archiver.process_thought(session, thought)
    
    # Check root context.md
    root_context = os.path.join(temp_docs_root, "context.md")
    assert os.path.exists(root_context)
    
    # Check topic context.md
    topic_context = os.path.join(temp_docs_root, "Systematic", "context.md")
    assert os.path.exists(topic_context)


def test_thought_marked_as_pattern(memory_manager, temp_docs_root, sample_session, high_quality_thought):
    """Test that thought is marked as thinking pattern after processing."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    assert high_quality_thought.is_thinking_pattern is False
    
    archiver.process_thought(sample_session, high_quality_thought)
    
    assert high_quality_thought.is_thinking_pattern is True


def test_pattern_saved_to_database(memory_manager, temp_docs_root, sample_session, high_quality_thought):
    """Test that pattern is saved to database."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    pattern = archiver.process_thought(sample_session, high_quality_thought)
    
    # Verify pattern was created successfully
    assert pattern is not None
    assert pattern.id is not None
    assert pattern.thought_id == high_quality_thought.id


def test_pattern_with_different_strategy(memory_manager, temp_docs_root, sample_session):
    """Test pattern creation with different strategies."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    thought = EnhancedThought(
        id="thought_1",
        session_id="test_session",
        content="Valid content",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.ACTOR_CRITIC_LOOP,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        metrics=ThoughtMetrics(
            logical_coherence=0.95,
            evidence_strength=0.85
        )
    )
    
    pattern = archiver.process_thought(sample_session, thought)
    
    # Check that correct topic directory was created
    topic_dir = os.path.join(temp_docs_root, "Actor-Critic-Loop")
    assert os.path.exists(topic_dir)


def test_pattern_with_tags(memory_manager, temp_docs_root, sample_session, high_quality_thought):
    """Test that pattern tags are preserved."""
    archiver = PatternArchiver(memory_manager, docs_root=temp_docs_root)
    
    pattern = archiver.process_thought(sample_session, high_quality_thought)
    
    assert pattern.tags == ["architecture", "scalability"]
