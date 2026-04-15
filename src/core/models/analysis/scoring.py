"""
Scoring domain models.
"""
from dataclasses import dataclass


@dataclass
class AnalysisConfig:
    """Configuration for token-aware analysis."""
    max_token_budget: int = 4000
    enable_novelty_sampling: bool = True
    novelty_sample_size: int = 10
    skip_analysis_threshold: int = 100
    enable_lazy_metrics: bool = True
