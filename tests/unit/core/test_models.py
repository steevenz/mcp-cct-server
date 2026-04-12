import pytest
from pydantic import ValidationError
from src.core.models.domain import ThoughtMetrics, EnhancedThought
from src.core.models.enums import ThoughtType, ThinkingStrategy, ConfidenceLevel
from src.engines.sequential.models import SequentialContext

def test_thought_metrics_constraints():
    """Test that metrics fall exactly within the 0.0 - 1.0 bounds logic."""
    # Valid
    metrics = ThoughtMetrics(clarity_score=0.5, logical_coherence=1.0)
    assert metrics.clarity_score == 0.5
    assert metrics.logical_coherence == 1.0
    assert metrics.confidence_level == ConfidenceLevel.MEDIUM

    # Invalid limits should trigger Pydantic ValidationError
    with pytest.raises(ValidationError):
        ThoughtMetrics(clarity_score=1.5)
        
    with pytest.raises(ValidationError):
        ThoughtMetrics(logical_coherence=-0.1)

def test_enhanced_thought_instantiation():
    """Test full schema instantiation to ensure fields are typed correctly."""
    context = SequentialContext(thought_number=1, estimated_total_thoughts=3)
    
    thought = EnhancedThought(
        id="thought_1",
        content="This is a test thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=context
    )
    
    assert thought.id == "thought_1"
    assert thought.strategy == ThinkingStrategy.SYSTEMATIC
    # Verify default factories
    assert len(thought.children_ids) == 0
    assert len(thought.contradicts) == 0
    assert thought.metrics.evidence_strength == 0.0

def test_enums_contain_empirical_research():
    """Validate that the enums are properly loaded with the newest additions."""
    strategies = [s.value for s in ThinkingStrategy]
    assert "empirical_research" in strategies
