import pytest
import uuid
from src.core.models.domain import EnhancedThought, ThoughtMetrics
from src.core.services.analysis.scoring import ScoringService
from src.core.models.enums import ThinkingStrategy, ThoughtType

def test_scoring_confidence_and_contradiction():
    scoring = ScoringService()
    
    # Baseline thought - longer to pass skip_analysis_threshold (default 100)
    thought1 = EnhancedThought(
        id="t1",
        content="We should use a microservices architecture to ensure scalability and independent deployment. " * 5,
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context={"thought_number": 1, "estimated_total_thoughts": 5, "next_thought_needed": True}
    )
    
    # Contradictory thought - longer
    thought2 = EnhancedThought(
        id="t2",
        content="Actually, we should not use microservices. A monolith is better for this stage. " * 5,
        thought_type=ThoughtType.EVALUATION,
        strategy=ThinkingStrategy.ACTOR_CRITIC_LOOP,
        sequential_context={"thought_number": 2, "estimated_total_thoughts": 5, "next_thought_needed": True}
    )
    
    metrics = scoring.analyze_thought(thought2, [thought1], model_id="test-model")
    
    assert metrics.confidence_score > 0
    assert len(metrics.contradiction_flags) > 0
    assert "Potential conflict" in metrics.contradiction_flags[0]

def test_trace_id_propagation():
    # This test would require a more complex setup with Orchestrator
    # But we can verify the model fields exist
    thought = EnhancedThought(
        id="t1",
        reasoning_trace_id="trace_test_123",
        content="Test content",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context={"thought_number": 1, "estimated_total_thoughts": 5, "next_thought_needed": True}
    )
    assert thought.reasoning_trace_id == "trace_test_123"
