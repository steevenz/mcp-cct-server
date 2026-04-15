"""
Scoring engine domain module.
Provides token-efficient cognitive performance evaluation with caching and budget awareness.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.core.models.domain import EnhancedThought, ThoughtMetrics
from src.core.models.enums import ThoughtType, ThinkingStrategy
from src.core.models.analysis import AnalysisConfig

from src.core.services.analysis.metrics import cosine_similarity, sample_based_novelty, _cached_tokenize
from src.core.services.analysis.quality import clarity_score
from src.utils.tokenizer import count_tokens
from src.core.services.analysis.bias import detect_bias_flags
from src.utils.pricing import pricing_manager

logger = logging.getLogger(__name__)


class ScoringService:
    """
    Token-efficient scoring engine with budget awareness and caching.

    Features:
    - Lazy metric calculation (only compute when accessed)
    - Token budget enforcement
    - Sampling-based novelty for large histories
    - Cached tokenization
    """

    def __init__(self, config: Optional[AnalysisConfig] = None, tp_threshold: float = 0.9):
        self.config = config or AnalysisConfig()
        self.tp_threshold = tp_threshold
        self._metrics_cache: Dict[str, ThoughtMetrics] = {}

    def is_pattern_candidate(self, thought: EnhancedThought) -> bool:
        """Check if thought qualifies as Golden Thinking Pattern."""
        metrics = thought.metrics
        return (
            metrics.logical_coherence >= self.tp_threshold and
            metrics.evidence_strength >= 0.8
        )

    def analyze_thought(
        self,
        thought: EnhancedThought,
        history: List[EnhancedThought],
        token_budget: Optional[int] = None,
        model_id: str = "claude-3-5-sonnet-20240620"
    ) -> ThoughtMetrics:
        """
        Token-aware multi-dimensional analysis of a thought step.

        Args:
            thought: The thought to analyze
            history: Previous thoughts for context
            token_budget: Optional override for max tokens to spend

        Returns:
            ThoughtMetrics with calculated scores
        """
        content = thought.content

        # Check cache
        cache_key = f"{thought.id}:{hash(content)}"
        if cache_key in self._metrics_cache:
            logger.debug(f"Cache hit for thought {thought.id}")
            return self._metrics_cache[cache_key]

        # [FIX] Comprehensive Transparency: Calculate tokens and costs for ALL thoughts
        # including those below the skip_analysis_threshold.
        usage = thought.token_usage or {}
        in_tokens = usage.get("input") 
        if in_tokens is None:
            # Fallback for single thought node analysis
            in_tokens = count_tokens(content, model_id)
            
        out_tokens = usage.get("output")
        if out_tokens is None:
            # For a thought being scored, the 'output' is the thought itself
            out_tokens = count_tokens(content, model_id)

        costs = pricing_manager.calculate_costs(
            model_id=model_id,
            input_tokens=in_tokens,
            output_tokens=out_tokens
        )

        # Determine analysis depth based on content length
        if len(content) < self.config.skip_analysis_threshold:
            metrics = ThoughtMetrics(
                clarity_score=0.5,
                logical_coherence=0.5,
                evidence_strength=0.5,
                novelty_score=1.0,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                input_cost_usd=costs["input_usd"],
                output_cost_usd=costs["output_usd"],
                input_cost_idr=costs["input_idr"],
                output_cost_idr=costs["output_idr"],
                currency_rate_idr=costs["currency_rate_idr"]
            )
            self._metrics_cache[cache_key] = metrics
            return metrics

        # 1. Clarity Score
        clarity = clarity_score(content)

        # 2. Logical Coherence
        coherence = self._calculate_coherence(thought, history, content)

        # 3. Novelty Detection
        novelty = self._calculate_novelty(content, history)

        # 4. Information Density
        density = self._calculate_density(content)

        # 5. Evidence Strength
        evidence_score = self._calculate_evidence(content)

        metrics = ThoughtMetrics(
            clarity_score=round(clarity, 3),
            logical_coherence=round(coherence, 3),
            evidence_strength=round(evidence_score, 3),
            novelty_score=round(novelty, 3),
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            input_cost_usd=costs["input_usd"],
            output_cost_usd=costs["output_usd"],
            input_cost_idr=costs["input_idr"],
            output_cost_idr=costs["output_idr"],
            currency_rate_idr=costs["currency_rate_idr"]
        )

        # Cache result
        self._metrics_cache[cache_key] = metrics

        logger.debug(
            f"Thought {thought.id} scored: "
            f"Clarity={metrics.clarity_score:.2f}, "
            f"Coherence={metrics.logical_coherence:.2f}, "
            f"Novelty={metrics.novelty_score:.2f}"
        )

        return metrics

    def _calculate_coherence(self, thought: EnhancedThought, history: List[EnhancedThought], content: str) -> float:
        """
        Calculate coherence with parent thought using cosine similarity.
        
        Coherence measures how well the current thought logically connects to its parent.
        
        Algorithm:
        1. Find parent thought in history
        2. Calculate cosine similarity between current and parent content
        3. Map similarity to coherence score using heuristic thresholds:
           - 0.3 < similarity < 0.8: High coherence (0.9) - optimal balance of relatedness and novelty
           - similarity > 0.9: Low coherence (0.4) - too repetitive, lacks novelty
           - similarity < 0.3: Low coherence (0.5) - too disconnected, lacks continuity
           - No parent: Moderate coherence (0.7) - root thought assumption
           - Parent not found: Low coherence (0.5) - broken link assumption
        
        Args:
            thought: Current thought to evaluate
            history: List of previous thoughts for context
            content: Current thought content string
        
        Returns:
            Coherence score between 0.0 and 1.0
        """
        if not thought.parent_id:
            return 0.7

        parent = next((t for t in history if t.id == thought.parent_id), None)
        if not parent:
            return 0.5

        sim = cosine_similarity(content, parent.content)

        if 0.3 < sim < 0.8:
            return 0.9
        elif sim > 0.9:
            return 0.4
        else:
            return 0.5

    def _calculate_novelty(self, content: str, history: List[EnhancedThought]) -> float:
        """
        Calculate novelty score based on similarity to previous thoughts.
        
        Novelty measures how unique the current thought is compared to history.
        Higher novelty indicates more original content.
        
        Algorithm:
        1. If no history, maximum novelty (1.0)
        2. For large histories with sampling enabled:
           - Sample subset of history for efficiency
           - Use sample_based_novelty for statistical estimation
        3. For small histories or sampling disabled:
           - Calculate cosine similarity with all previous thoughts
           - Find maximum similarity (closest match)
           - Novelty = 1 - max_similarity (inverted similarity)
        
        Args:
            content: Current thought content string
            history: List of previous thoughts for comparison
        
        Returns:
            Novelty score between 0.0 (duplicate) and 1.0 (completely novel)
        """
        if not history:
            return 1.0

        if self.config.enable_novelty_sampling and len(history) > self.config.novelty_sample_size:
            history_contents = [t.content for t in history]
            return sample_based_novelty(content, history_contents, self.config.novelty_sample_size)
        else:
            max_sim = 0.0
            for prev in history:
                if prev.content == content:
                    continue
                sim = cosine_similarity(content, prev.content)
                max_sim = max(max_sim, sim)
            return 1.0 - max_sim

    def _calculate_density(self, content: str) -> float:
        """
        Calculate information density using token analysis.
        
        Density measures the ratio of unique tokens to total tokens.
        Higher density indicates more information-rich content.
        
        Algorithm:
        1. Tokenize content using cached tokenizer for efficiency
        2. Extract unique tokens (set removes duplicates)
        3. Calculate ratio: unique_tokens / total_tokens
        4. Return 0.0 if content is empty
        
        Interpretation:
        - 1.0: All tokens unique (maximum information density)
        - 0.5: Half tokens unique (moderate density)
        - 0.0: No unique tokens (minimum density, all repetition)
        
        Args:
            content: Thought content string to analyze
        
        Returns:
            Density score between 0.0 and 1.0
        """
        tokens = _cached_tokenize(content)
        unique_tokens = set(tokens)
        return len(unique_tokens) / len(tokens) if tokens else 0.0

    def _calculate_evidence(self, content: str) -> float:
        """
        Calculate evidence strength based on keyword presence.
        
        Evidence strength measures how well-supported the thought is
        by concrete examples, data, or reasoning indicators.
        
        Algorithm:
        1. Define evidence keywords that indicate support:
           - "example": Concrete illustration
           - "data": Empirical support
           - "code": Implementation detail
           - "specifically": Specific instance
           - "because": Causal reasoning
           - "result": Outcome-based reasoning
           - "evidence": Explicit citation
        2. Tokenize content
        3. Count occurrences of evidence keywords
        4. Calculate score: min(1.0, evidence_count / 3.0)
           - 3+ keywords = maximum evidence (1.0)
           - 0 keywords = minimum evidence (0.0)
        
        Args:
            content: Thought content string to analyze
        
        Returns:
            Evidence strength score between 0.0 and 1.0
        """
        evidence_keywords = ["example", "data", "code", "specifically", "because", "result", "evidence"]
        tokens = _cached_tokenize(content)
        evidence_count = sum(1 for word in tokens if word in evidence_keywords)
        return min(1.0, evidence_count / 3.0)

    @staticmethod
    def generate_summary(content: str, max_length: int = 150) -> str:
        """
        Token-efficient summary generation.
        """
        content = content.strip()
        if not content:
            return ""

        if len(content) <= max_length:
            return content

        sentences = re.split(r'(?<=[.!?]) +', content)
        summary_parts = []
        current_len = 0

        for sent in sentences[:3]:
            if current_len + len(sent) > max_length:
                break
            summary_parts.append(sent)
            current_len += len(sent)

        summary = " ".join(summary_parts)
        if len(summary) > max_length:
            return summary[:max_length-3] + "..."

        return summary

    def clear_cache(self) -> None:
        """Clear metrics cache to free memory."""
        self._metrics_cache.clear()
        logger.info("ScoringService cache cleared")


class IncrementalSessionAnalyzer:
    """
    Analyzes session metrics incrementally to avoid re-processing all thoughts.
    """

    def __init__(self):
        self._running_clarity_sum = 0.0
        self._running_clarity_count = 0
        self._bias_flags: set[str] = set()
        self._last_consistency = 1.0
        self._prev_text: Optional[str] = None

    def add_thought(self, text: str) -> Dict[str, Any]:
        """
        Incrementally update session metrics with new thought.
        Avoids O(n) recalculation.
        """
        clarity = clarity_score(text)
        self._running_clarity_sum += clarity
        self._running_clarity_count += 1

        new_flags = detect_bias_flags(text)
        self._bias_flags.update(new_flags)

        if self._prev_text:
            consistency = cosine_similarity(text, self._prev_text)
            self._last_consistency = 0.7 * self._last_consistency + 0.3 * consistency
        else:
            consistency = 1.0

        self._prev_text = text

        return {
            "clarity_avg": self._running_clarity_sum / self._running_clarity_count,
            "bias_flags": sorted(self._bias_flags),
            "consistency": round(self._last_consistency, 4),
            "thought_count": self._running_clarity_count
        }

    def get_final_metrics(self) -> Dict[str, Any]:
        """Get final aggregated metrics."""
        return {
            "clarity_score": round(self._running_clarity_sum / max(1, self._running_clarity_count), 4),
            "bias_flags": sorted(self._bias_flags),
            "consistency_score": round(self._last_consistency, 4),
        }
