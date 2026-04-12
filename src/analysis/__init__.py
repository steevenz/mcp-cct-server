"""
Analysis domain module for cognitive quality metrics.
Provides token-efficient evaluation with caching and budget awareness.
"""

from src.analysis.bias import (
    detect_bias_flags,
    comprehensive_bias_check,
    has_critical_bias,
)
from src.analysis.metrics import (
    cosine_similarity,
    sample_based_novelty,
)
from src.analysis.quality import (
    clarity_score,
    estimate_token_count,
)
from src.analysis.scoring_engine import (
    ScoringEngine,
    IncrementalSessionAnalyzer,
    AnalysisConfig,
)

__all__ = [
    # Bias detection
    "detect_bias_flags",
    "comprehensive_bias_check",
    "has_critical_bias",
    # Metrics
    "cosine_similarity",
    "sample_based_novelty",
    # Quality
    "clarity_score",
    "estimate_token_count",
    # Scoring
    "ScoringEngine",
    "IncrementalSessionAnalyzer",
    "AnalysisConfig",
]
