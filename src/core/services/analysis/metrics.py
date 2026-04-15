"""
Engine performance metrics collection service.

Tracks and aggregates performance metrics for cognitive engines
including execution time, token usage, and quality scores.
"""
from __future__ import annotations

import time
import logging
import functools
import math
import random
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict, Counter
import statistics

from src.utils.tokenizer import count_tokens
from src.core.models.analysis import EngineMetric, AggregatedMetrics


logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS FOR TEXT ANALYSIS
# ============================================================================

# Compile regex once for performance
_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


@functools.lru_cache(maxsize=1024)
def _cached_tokenize(text: str) -> Tuple[str, ...]:
    """
    Cached tokenization to avoid re-processing same text.
    Returns tuple for hashability (required for cache key).
    """
    return tuple(_TOKEN_PATTERN.findall(text.lower()))


def _tokenize(text: str) -> list[str]:
    """
    [DEPRECATED] Use count_tokens for counting. 
    Kept for backward compatibility in similarity calculations.
    """
    return list(_cached_tokenize(text))


@functools.lru_cache(maxsize=512)
def _cached_token_counts(text: str) -> Counter:
    """Cached token counter for cosine similarity."""
    return Counter(_cached_tokenize(text))


def cosine_similarity(a: str, b: str) -> float:
    """
    Calculate cosine similarity between two texts.
    Uses cached tokenization for O(1) lookup on repeated texts.
    """
    a_counts = _cached_token_counts(a)
    b_counts = _cached_token_counts(b)

    if not a_counts or not b_counts:
        return 0.0

    # Fast path: if identical token sets
    if a_counts == b_counts:
        return 1.0

    # Calculate dot product only for common tokens (optimization)
    common_tokens = set(a_counts.keys()) & set(b_counts.keys())
    if not common_tokens:
        return 0.0

    dot = sum(float(a_counts[t]) * float(b_counts[t]) for t in common_tokens)

    norm_a = math.sqrt(sum(float(v * v) for v in a_counts.values()))
    norm_b = math.sqrt(sum(float(v * v) for v in b_counts.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def sample_based_novelty(text: str, history: List[str], sample_size: int = 10) -> float:
    """
    Approximate novelty using sampling for large histories.
    Instead of O(n) comparison with all history, sample recent thoughts.

    Args:
        text: New thought content
        history: List of previous thought contents
        sample_size: Number of recent thoughts to compare

    Returns:
        Novelty score [0.0, 1.0], higher = more novel
    """
    if not history:
        return 1.0

    # Sample recent thoughts + some from older history
    if len(history) <= sample_size:
        sample = history
    else:
        # Always include most recent 5, sample 5 from rest
        recent = history[-5:]
        older = history[:-5]
        sampled_older = random.sample(older, min(5, len(older)))
        sample = recent + sampled_older

    # Find max similarity with sampled set
    max_sim = 0.0
    text_tokens = set(_cached_tokenize(text))

    for prev in sample:
        # Quick pre-filter: if token sets are very different, skip calculation
        prev_tokens = set(_cached_tokenize(prev))
        if len(text_tokens & prev_tokens) < 2:  # Very different
            continue

        sim = cosine_similarity(text, prev)
        max_sim = max(max_sim, sim)

    return 1.0 - max_sim


class MetricsService:
    """
    Collects and aggregates performance metrics for cognitive engines.
    
    Provides real-time monitoring and historical analysis of engine performance.
    """
    
    def __init__(self):
        self._metrics: List[EngineMetric] = []
        self._engine_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "total_tokens": 0,
            "clarity_scores": [],
            "coherence_scores": [],
            "evidence_scores": [],
            "novelty_scores": []
        })
        self._enabled = True
    
    def record_execution(
        self,
        engine_name: str,
        strategy: str,
        execution_time_ms: float,
        input_tokens: int,
        output_tokens: int,
        clarity_score: float,
        coherence_score: float,
        evidence_score: float,
        novelty_score: float,
        session_id: str
    ) -> None:
        """
        Record a single engine execution metric.
        
        Args:
            engine_name: Name of the cognitive engine
            strategy: Thinking strategy used
            execution_time_ms: Execution time in milliseconds
            input_tokens: Input token count
            output_tokens: Output token count
            clarity_score: Quality clarity score
            coherence_score: Quality coherence score
            evidence_score: Quality evidence score
            novelty_score: Quality novelty score
            session_id: Session identifier
        """
        if not self._enabled:
            return
        
        metric = EngineMetric(
            timestamp=datetime.now(timezone.utc).isoformat(),
            engine_name=engine_name,
            strategy=strategy,
            execution_time_ms=execution_time_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            clarity_score=clarity_score,
            coherence_score=coherence_score,
            evidence_score=evidence_score,
            novelty_score=novelty_score,
            session_id=session_id
        )
        
        self._metrics.append(metric)
        
        # Update running stats
        key = f"{engine_name}:{strategy}"
        stats = self._engine_stats[key]
        stats["count"] += 1
        stats["total_time"] += execution_time_ms
        stats["total_tokens"] += metric.total_tokens
        stats["clarity_scores"].append(clarity_score)
        stats["coherence_scores"].append(coherence_score)
        stats["evidence_scores"].append(evidence_score)
        stats["novelty_scores"].append(novelty_score)
        
        logger.debug(
            f"[METRICS] Recorded execution: {engine_name} ({strategy}) | "
            f"time={execution_time_ms:.2f}ms | tokens={metric.total_tokens} | "
            f"coherence={coherence_score:.3f}"
        )
    
    def get_aggregated_metrics(
        self,
        engine_name: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> List[AggregatedMetrics]:
        """
        Get aggregated metrics for specified engine/strategy.
        
        Args:
            engine_name: Filter by engine name (optional)
            strategy: Filter by strategy (optional)
        
        Returns:
            List of aggregated metrics
        """
        aggregated = []
        
        # Filter metrics
        filtered = self._metrics
        if engine_name:
            filtered = [m for m in filtered if m.engine_name == engine_name]
        if strategy:
            filtered = [m for m in filtered if m.strategy == strategy]
        
        # Group by engine:strategy
        groups = defaultdict(list)
        for metric in filtered:
            key = f"{metric.engine_name}:{metric.strategy}"
            groups[key].append(metric)
        
        # Calculate aggregates
        for key, metrics in groups.items():
            if not metrics:
                continue
            
            engine_name, strategy = key.split(":")
            times = [m.execution_time_ms for m in metrics]
            input_tokens = [m.input_tokens for m in metrics]
            output_tokens = [m.output_tokens for m in metrics]
            total_tokens = [m.total_tokens for m in metrics]
            clarity = [m.clarity_score for m in metrics]
            coherence = [m.coherence_score for m in metrics]
            evidence = [m.evidence_score for m in metrics]
            novelty = [m.novelty_score for m in metrics]
            
            # Estimate costs (using average rates)
            total_tokens_sum = sum(total_tokens)
            estimated_cost_usd = (total_tokens_sum * 0.00001)  # Rough estimate
            estimated_cost_idr = estimated_cost_usd * 15000  # Rough IDR estimate
            
            aggregated.append(AggregatedMetrics(
                engine_name=engine_name,
                strategy=strategy,
                total_executions=len(metrics),
                avg_execution_time_ms=statistics.mean(times),
                min_execution_time_ms=min(times),
                max_execution_time_ms=max(times),
                avg_input_tokens=statistics.mean(input_tokens),
                avg_output_tokens=statistics.mean(output_tokens),
                avg_total_tokens=statistics.mean(total_tokens),
                avg_clarity_score=statistics.mean(clarity),
                avg_coherence_score=statistics.mean(coherence),
                avg_evidence_score=statistics.mean(evidence),
                avg_novelty_score=statistics.mean(novelty),
                total_tokens=total_tokens_sum,
                estimated_cost_usd=estimated_cost_usd,
                estimated_cost_idr=estimated_cost_idr
            ))
        
        return aggregated
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall metrics summary.
        
        Returns:
            Dictionary containing summary statistics
        """
        if not self._metrics:
            return {
                "total_executions": 0,
                "total_tokens": 0,
                "total_time_ms": 0.0,
                "avg_coherence": 0.0,
                "engines": []
            }
        
        total_executions = len(self._metrics)
        total_tokens = sum(m.total_tokens for m in self._metrics)
        total_time = sum(m.execution_time_ms for m in self._metrics)
        avg_coherence = statistics.mean([m.coherence_score for m in self._metrics])
        
        # Get engine breakdown
        engine_breakdown = []
        for key, stats in self._engine_stats.items():
            engine_name, strategy = key.split(":")
            engine_breakdown.append({
                "engine": engine_name,
                "strategy": strategy,
                "executions": stats["count"],
                "avg_time_ms": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0,
                "total_tokens": stats["total_tokens"],
                "avg_coherence": statistics.mean(stats["coherence_scores"]) if stats["coherence_scores"] else 0
            })
        
        return {
            "total_executions": total_executions,
            "total_tokens": total_tokens,
            "total_time_ms": total_time,
            "avg_coherence": avg_coherence,
            "engines": engine_breakdown
        }
    
    def get_recent_metrics(self, n: int = 100) -> List[EngineMetric]:
        """
        Get the most recent n metrics.
        
        Args:
            n: Number of recent metrics to retrieve
        
        Returns:
            List of recent metrics
        """
        return self._metrics[-n:]
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self._engine_stats.clear()
        logger.info("[METRICS] All metrics cleared")
    
    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True
        logger.info("[METRICS] Metrics collection enabled")
    
    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False
        logger.info("[METRICS] Metrics collection disabled")
    
    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self._enabled


# Global metrics collector instance
_global_metrics_collector = MetricsService()


def get_metrics_collector() -> MetricsService:
    """
    Get the global metrics collector instance.
    
    Returns:
        Global MetricsCollector instance
    """
    return _global_metrics_collector


def record_engine_execution(
    engine_name: str,
    strategy: str,
    execution_time_ms: float,
    input_tokens: int,
    output_tokens: int,
    clarity_score: float,
    coherence_score: float,
    evidence_score: float,
    novelty_score: float,
    session_id: str
) -> None:
    """
    Convenience function to record engine execution to global collector.
    
    Args:
        engine_name: Name of the cognitive engine
        strategy: Thinking strategy used
        execution_time_ms: Execution time in milliseconds
        input_tokens: Input token count
        output_tokens: Output token count
        clarity_score: Quality clarity score
        coherence_score: Quality coherence score
        evidence_score: Quality evidence score
        novelty_score: Quality novelty score
        session_id: Session identifier
    """
    _global_metrics_collector.record_execution(
        engine_name=engine_name,
        strategy=strategy,
        execution_time_ms=execution_time_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        clarity_score=clarity_score,
        coherence_score=coherence_score,
        evidence_score=evidence_score,
        novelty_score=novelty_score,
        session_id=session_id
    )


def get_metrics_summary() -> Dict[str, Any]:
    """
    Convenience function to get metrics summary from global collector.
    
    Returns:
        Dictionary containing summary statistics
    """
    return _global_metrics_collector.get_summary()


def clear_all_metrics() -> None:
    """
    Convenience function to clear all metrics from global collector.
    """
    _global_metrics_collector.clear_metrics()
