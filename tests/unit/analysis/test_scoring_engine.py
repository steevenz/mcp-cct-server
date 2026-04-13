import pytest
from src.analysis.scoring_engine import (
    AnalysisConfig,
    ScoringEngine,
    IncrementalSessionAnalyzer
)
from src.core.models.domain import EnhancedThought, ThoughtMetrics
from src.core.models.enums import ThoughtType, ThinkingStrategy
from src.core.models.contexts import SequentialContext


def test_analysis_config_defaults():
    """Test AnalysisConfig with default values."""
    config = AnalysisConfig()
    assert config.max_token_budget == 4000
    assert config.enable_novelty_sampling is True
    assert config.novelty_sample_size == 10
    assert config.skip_analysis_threshold == 100
    assert config.enable_lazy_metrics is True


def test_analysis_config_custom():
    """Test AnalysisConfig with custom values."""
    config = AnalysisConfig(
        max_token_budget=8000,
        enable_novelty_sampling=False,
        novelty_sample_size=20
    )
    assert config.max_token_budget == 8000
    assert config.enable_novelty_sampling is False
    assert config.novelty_sample_size == 20


def test_scoring_engine_init():
    """Test ScoringEngine initialization."""
    engine = ScoringEngine()
    assert engine.config is not None
    assert engine.tp_threshold == 0.9
    assert engine._metrics_cache == {}


def test_scoring_engine_custom_threshold():
    """Test ScoringEngine with custom threshold."""
    engine = ScoringEngine(tp_threshold=0.85)
    assert engine.tp_threshold == 0.85


def test_scoring_engine_is_pattern_candidate():
    """Test pattern candidate detection."""
    engine = ScoringEngine(tp_threshold=0.9)
    
    # High coherence and evidence should be candidate
    thought = EnhancedThought(
        id="test_1",
        session_id="sess_1",
        content="Valid thought",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
        metrics=ThoughtMetrics(
            logical_coherence=0.95,
            evidence_strength=0.85
        )
    )
    assert engine.is_pattern_candidate(thought) is True
    
    # Low coherence should not be candidate
    thought.metrics.logical_coherence = 0.5
    assert engine.is_pattern_candidate(thought) is False


def test_scoring_engine_analyze_thought_short_content():
    """Test analyzing thought with short content (skip analysis)."""
    engine = ScoringEngine(config=AnalysisConfig(skip_analysis_threshold=200))
    
    thought = EnhancedThought(
        id="test_1",
        session_id="sess_1",
        content="Short",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    metrics = engine.analyze_thought(thought, [])
    
    # Short content gets default scores
    assert metrics.clarity_score == 0.5
    assert metrics.logical_coherence == 0.5
    assert metrics.evidence_strength == 0.5
    assert metrics.novelty_score == 1.0


def test_scoring_engine_analyze_thought_with_history():
    """Test analyzing thought with history for coherence calculation."""
    engine = ScoringEngine()
    
    parent_thought = EnhancedThought(
        id="parent_1",
        session_id="sess_1",
        content="Parent thought about system design",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    child_thought = EnhancedThought(
        id="child_1",
        session_id="sess_1",
        content="Child thought about system design details",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        parent_id="parent_1",
        sequential_context=SequentialContext(thought_number=2, estimated_total_thoughts=5)
    )
    
    metrics = engine.analyze_thought(child_thought, [parent_thought])
    
    assert metrics.clarity_score >= 0.0
    assert metrics.clarity_score <= 1.0
    assert metrics.logical_coherence >= 0.0
    assert metrics.logical_coherence <= 1.0
    assert metrics.novelty_score >= 0.0
    assert metrics.novelty_score <= 1.0


def test_scoring_engine_analyze_thought_no_parent():
    """Test analyzing thought without parent."""
    engine = ScoringEngine()
    
    thought = EnhancedThought(
        id="test_1",
        session_id="sess_1",
        content="This is a detailed thought with enough content to analyze properly and should trigger full analysis",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    metrics = engine.analyze_thought(thought, [])
    
    # No parent should give default coherence of 0.5
    assert metrics.logical_coherence == 0.5
    assert metrics.clarity_score > 0.0
    assert metrics.novelty_score == 1.0  # First thought is always 100% novel


def test_scoring_engine_cache():
    """Test that metrics are cached."""
    engine = ScoringEngine()
    
    thought = EnhancedThought(
        id="test_1",
        session_id="sess_1",
        content="This is a detailed thought with enough content to analyze properly",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    # First call
    metrics1 = engine.analyze_thought(thought, [])
    
    # Second call should use cache
    metrics2 = engine.analyze_thought(thought, [])
    
    assert metrics1.clarity_score == metrics2.clarity_score
    assert metrics1.logical_coherence == metrics2.logical_coherence


def test_scoring_engine_clear_cache():
    """Test clearing the cache."""
    engine = ScoringEngine()
    
    thought = EnhancedThought(
        id="test_1",
        session_id="sess_1",
        content="This is a detailed thought with enough content to analyze properly",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    engine.analyze_thought(thought, [])
    assert len(engine._metrics_cache) > 0
    
    engine.clear_cache()
    assert len(engine._metrics_cache) == 0


def test_scoring_engine_generate_summary_short():
    """Test generating summary for short content."""
    summary = ScoringEngine.generate_summary("Short content", max_length=100)
    assert summary == "Short content"


def test_scoring_engine_generate_summary_long():
    """Test generating summary for long content."""
    long_content = "This is a very long piece of content that should be truncated. " * 10
    summary = ScoringEngine.generate_summary(long_content, max_length=50)
    # Summary should be truncated to near max_length (allowing for "..." suffix)
    assert len(summary) <= 60  # Allow some flexibility for truncation logic


def test_scoring_engine_generate_summary_empty():
    """Test generating summary for empty content."""
    summary = ScoringEngine.generate_summary("")
    assert summary == ""


def test_incremental_session_analyzer_init():
    """Test IncrementalSessionAnalyzer initialization."""
    analyzer = IncrementalSessionAnalyzer()
    assert analyzer._running_clarity_sum == 0.0
    assert analyzer._running_clarity_count == 0
    assert analyzer._bias_flags == set()
    assert analyzer._last_consistency == 1.0
    assert analyzer._prev_text is None


def test_incremental_session_analyzer_add_thought():
    """Test adding thought to incremental analyzer."""
    analyzer = IncrementalSessionAnalyzer()
    
    metrics = analyzer.add_thought("This is a clear thought")
    
    assert "clarity_avg" in metrics
    assert "bias_flags" in metrics
    assert "consistency" in metrics
    assert "thought_count" in metrics
    assert metrics["thought_count"] == 1


def test_incremental_session_analyzer_multiple_thoughts():
    """Test adding multiple thoughts incrementally."""
    analyzer = IncrementalSessionAnalyzer()
    
    analyzer.add_thought("First thought")
    analyzer.add_thought("Second thought")
    m3 = analyzer.add_thought("Third thought")
    
    assert m3["thought_count"] == 3
    
    metrics = analyzer.get_final_metrics()
    assert 0.0 <= metrics["clarity_score"] <= 1.0
    assert 0.0 <= metrics["consistency_score"] <= 1.0


def test_incremental_session_analyzer_consistency():
    """Test consistency calculation across thoughts."""
    analyzer = IncrementalSessionAnalyzer()
    
    analyzer.add_thought("Similar content about design")
    analyzer.add_thought("Similar content about design patterns")
    
    metrics = analyzer.get_final_metrics()
    # Similar content should have high consistency
    assert metrics["consistency_score"] > 0.5


def test_incremental_session_analyzer_get_final_metrics():
    """Test getting final metrics."""
    analyzer = IncrementalSessionAnalyzer()
    
    analyzer.add_thought("Test thought")
    
    final_metrics = analyzer.get_final_metrics()
    
    assert "clarity_score" in final_metrics
    assert "bias_flags" in final_metrics
    assert "consistency_score" in final_metrics


def test_scoring_engine_analyze_thought_with_token_usage():
    """Test analyzing thought with explicit token usage."""
    engine = ScoringEngine()
    
    thought = EnhancedThought(
        id="test_1",
        session_id="sess_1",
        content="This is a detailed thought with enough content to analyze properly",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
    )
    
    metrics = engine.analyze_thought(thought, [])
    
    assert metrics.input_tokens >= 0
    assert metrics.output_tokens >= 0
    assert metrics.input_cost_usd >= 0
    assert metrics.output_cost_usd >= 0
