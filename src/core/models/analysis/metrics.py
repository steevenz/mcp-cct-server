"""
Metrics domain models.
"""
from dataclasses import dataclass


@dataclass
class EngineMetric:
    """Single metric data point for an engine."""
    timestamp: str
    engine_name: str
    strategy: str
    execution_time_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    clarity_score: float
    coherence_score: float
    evidence_score: float
    novelty_score: float
    session_id: str


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for an engine."""
    engine_name: str
    strategy: str
    total_executions: int
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    avg_input_tokens: int
    avg_output_tokens: int
    avg_total_tokens: int
    avg_clarity_score: float
    avg_coherence_score: float
    avg_evidence_score: float
    avg_novelty_score: float
    total_tokens: int
    estimated_cost_usd: float
    estimated_cost_idr: float
