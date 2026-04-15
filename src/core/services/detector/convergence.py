"""
ConvergenceDetector: Standalone Domain Service for Cognitive Convergence.

Implements CCT v5.0 §6.D as a modular, DDD-compliant service.
Determines when thinking has achieved elite convergence based on multi-factor analysis.

This is a standalone service that can be used by:
- IntelligenceRouter (for routing decisions)
- SequentialEngine (for early stopping)
- Orchestrator (for session completion)

Follows the 'Lego Principle' - can be composed into any part of the system.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.models.domain import CCTSessionState, EnhancedThought

logger = logging.getLogger(__name__)


class ConvergenceLevel(Enum):
    """Level of cognitive convergence achieved."""
    NONE = "none"              # No convergence detected
    EMERGING = "emerging"      # Early signs of convergence
    PARTIAL = "partial"        # Partial convergence, more thought needed
    FULL = "full"                # Full convergence achieved
    ELITE = "elite"              # Elite convergence (high coherence + evidence)


@dataclass
class ConvergenceFactors:
    """Factors contributing to convergence detection."""
    coherence_streak: bool = False
    evidence_strength: bool = False
    persona_insight_density: bool = False
    no_quality_degradation: bool = False
    is_conclusion_type: bool = False
    revision_stability: bool = False  # No recent revisions
    
    def calculate_score(self) -> int:
        """Calculate convergence score (0-6)."""
        return sum([
            self.coherence_streak,
            self.evidence_strength,
            self.persona_insight_density,
            self.no_quality_degradation,
            self.is_conclusion_type,
            self.revision_stability
        ])


@dataclass
class ConvergenceResult:
    """Result of convergence detection."""
    has_converged: bool
    level: ConvergenceLevel
    score: int  # 0-6
    max_score: int = 6
    reasons: List[str]
    factors: ConvergenceFactors
    confidence: float  # 0.0 to 1.0
    recommendation: str
    
    @property
    def convergence_percentage(self) -> float:
        """Convergence as percentage (0-100)."""
        return (self.score / self.max_score) * 100


class ConvergenceService:
    """
    Standalone convergence detection service.
    
    Implements multi-factor convergence analysis from CCT v5.0 §6.D:
    1. Logical coherence >= 0.95 for 2+ consecutive thoughts
    2. Evidence strength >= 0.8
    3. High-density persona insights detected
    4. No quality degradation in last 3 steps
    5. Conclusion thought type with high confidence
    6. Revision stability (no recent revisions)
    
    Thresholds:
    - ELITE: Score >= 5/6
    - FULL: Score >= 4/6
    - PARTIAL: Score >= 3/6
    - EMERGING: Score >= 2/6
    - NONE: Score < 2/6
    """
    
    # Thresholds per CCT v5.0
    COHERENCE_THRESHOLD = 0.95
    EVIDENCE_THRESHOLD = 0.8
    CLARITY_THRESHOLD = 0.7
    PERSONA_DENSITY_MIN = 2  # At least 2 persona insights in last 3 thoughts
    
    def __init__(
        self,
        elite_threshold: int = 5,
        full_threshold: int = 4,
        partial_threshold: int = 3,
        emerging_threshold: int = 2
    ):
        self.elite_threshold = elite_threshold
        self.full_threshold = full_threshold
        self.partial_threshold = partial_threshold
        self.emerging_threshold = emerging_threshold
        
        self._stats = {
            "total_checks": 0,
            "elite_convergences": 0,
            "full_convergences": 0,
            "partial_convergences": 0,
            "false_positives": 0  # Convergence detected but session continued productively
        }
    
    def detect(
        self,
        session: CCTSessionState,
        recent_thoughts: List[EnhancedThought]
    ) -> ConvergenceResult:
        """
        Detect convergence level for a session based on recent thoughts.
        
        This is the main entry point for convergence detection.
        """
        self._stats["total_checks"] += 1
        
        if not recent_thoughts:
            return ConvergenceResult(
                has_converged=False,
                level=ConvergenceLevel.NONE,
                score=0,
                reasons=["No recent thoughts to analyze"],
                factors=ConvergenceFactors(),
                confidence=0.0,
                recommendation="Continue thinking process"
            )
        
        # Need at least 2 thoughts for convergence detection
        if len(recent_thoughts) < 2:
            return ConvergenceResult(
                has_converged=False,
                level=ConvergenceLevel.NONE,
                score=0,
                reasons=["Insufficient thought history (need 2+ thoughts)"],
                factors=ConvergenceFactors(),
                confidence=0.0,
                recommendation="Continue thinking process"
            )
        
        # Analyze convergence factors
        factors = self._analyze_factors(session, recent_thoughts)
        score = factors.calculate_score()
        
        # Determine level based on score
        level = self._score_to_level(score)
        has_converged = level in [ConvergenceLevel.ELITE, ConvergenceLevel.FULL]
        
        # Generate reasons and recommendations
        reasons = self._generate_reasons(factors, score)
        recommendation = self._generate_recommendation(level, score)
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(factors, len(recent_thoughts))
        
        # Update stats
        if level == ConvergenceLevel.ELITE:
            self._stats["elite_convergences"] += 1
        elif level == ConvergenceLevel.FULL:
            self._stats["full_convergences"] += 1
        elif level == ConvergenceLevel.PARTIAL:
            self._stats["partial_convergences"] += 1
        
        logger.info(
            f"[CONVERGENCE] {session.session_id}: {level.value} "
            f"(score={score}/6, confidence={confidence:.2f})"
        )
        
        return ConvergenceResult(
            has_converged=has_converged,
            level=level,
            score=score,
            reasons=reasons,
            factors=factors,
            confidence=confidence,
            recommendation=recommendation
        )
    
    def _analyze_factors(
        self,
        session: CCTSessionState,
        recent_thoughts: List[EnhancedThought]
    ) -> ConvergenceFactors:
        """Analyze all convergence factors."""
        factors = ConvergenceFactors()
        
        # Get last 3 thoughts for analysis
        last_3 = recent_thoughts[-3:] if len(recent_thoughts) >= 3 else recent_thoughts
        last_2 = recent_thoughts[-2:] if len(recent_thoughts) >= 2 else recent_thoughts
        last_thought = recent_thoughts[-1]
        
        # Factor 1: High coherence streak (0.95+ for 2+ thoughts)
        recent_metrics = [t.metrics for t in last_2 if t.metrics]
        factors.coherence_streak = all(
            m.logical_coherence >= self.COHERENCE_THRESHOLD 
            for m in recent_metrics
        ) if len(recent_metrics) >= 2 else False
        
        # Factor 2: Evidence strength >= 0.8
        if last_thought.metrics:
            factors.evidence_strength = last_thought.metrics.evidence_strength >= self.EVIDENCE_THRESHOLD
        
        # Factor 3: High-density persona insights
        persona_insight_count = sum(1 for t in last_3 if "persona_insight" in t.tags)
        factors.persona_insight_density = persona_insight_count >= self.PERSONA_DENSITY_MIN
        
        # Factor 4: No quality degradation in last 3 steps
        recent_metrics_3 = [t.metrics for t in last_3 if t.metrics]
        factors.no_quality_degradation = all(
            m.clarity_score >= self.CLARITY_THRESHOLD and 
            m.logical_coherence >= self.CLARITY_THRESHOLD
            for m in recent_metrics_3
        ) if len(recent_metrics_3) >= 2 else False
        
        # Factor 5: Conclusion type with high confidence
        if last_thought.metrics:
            factors.is_conclusion_type = (
                last_thought.thought_type == "conclusion" and 
                last_thought.metrics.evidence_strength > 0.8
            )
        
        # Factor 6: Revision stability (no is_revision flag in recent thoughts)
        factors.revision_stability = not any(
            getattr(t, 'is_revision', False) or 
            (t.sequential_context and t.sequential_context.is_revision)
            for t in last_3
        )
        
        return factors
    
    def _score_to_level(self, score: int) -> ConvergenceLevel:
        """Convert convergence score to level."""
        if score >= self.elite_threshold:
            return ConvergenceLevel.ELITE
        elif score >= self.full_threshold:
            return ConvergenceLevel.FULL
        elif score >= self.partial_threshold:
            return ConvergenceLevel.PARTIAL
        elif score >= self.emerging_threshold:
            return ConvergenceLevel.EMERGING
        else:
            return ConvergenceLevel.NONE
    
    def _generate_reasons(self, factors: ConvergenceFactors, score: int) -> List[str]:
        """Generate human-readable reasons for convergence assessment."""
        reasons = []
        
        if factors.coherence_streak:
            reasons.append(f"High coherence streak (≥{self.COHERENCE_THRESHOLD})")
        if factors.evidence_strength:
            reasons.append(f"Strong evidence (≥{self.EVIDENCE_THRESHOLD})")
        if factors.persona_insight_density:
            reasons.append(f"High persona insight density")
        if factors.no_quality_degradation:
            reasons.append("No quality degradation")
        if factors.is_conclusion_type:
            reasons.append("Conclusion type with high confidence")
        if factors.revision_stability:
            reasons.append("Revision stability (no recent revisions)")
        
        if not reasons:
            reasons.append("Insufficient convergence factors met")
        
        reasons.append(f"Overall convergence score: {score}/6")
        
        return reasons
    
    def _generate_recommendation(self, level: ConvergenceLevel, score: int) -> str:
        """Generate recommendation based on convergence level."""
        recommendations = {
            ConvergenceLevel.ELITE: "ELITE convergence achieved - Session can be completed early",
            ConvergenceLevel.FULL: "FULL convergence achieved - Session ready for completion",
            ConvergenceLevel.PARTIAL: "PARTIAL convergence - Consider 1-2 more thoughts",
            ConvergenceLevel.EMERGING: "EMERGING convergence - Continue current strategy",
            ConvergenceLevel.NONE: "No convergence - Continue thinking process"
        }
        
        return recommendations.get(level, "Continue thinking process")
    
    def _calculate_confidence(
        self,
        factors: ConvergenceFactors,
        thought_count: int
    ) -> float:
        """Calculate confidence score based on data quality."""
        # Base confidence on number of factors met
        factor_confidence = factors.calculate_score() / 6
        
        # Adjust for data quantity
        quantity_bonus = min(thought_count / 5, 0.2)  # Up to 0.2 bonus for more data
        
        # Adjust for coherence streak (strong signal)
        if factors.coherence_streak:
            coherence_bonus = 0.1
        else:
            coherence_bonus = 0
        
        confidence = factor_confidence + quantity_bonus + coherence_bonus
        return min(confidence, 1.0)  # Cap at 1.0
    
    def should_finish(
        self,
        session: CCTSessionState,
        recent_thoughts: List[EnhancedThought]
    ) -> bool:
        """
        Convenience method: Should the thinking process finish?
        
        Returns True if ELITE or FULL convergence achieved.
        """
        result = self.detect(session, recent_thoughts)
        return result.has_converged
    
    def get_stats(self) -> Dict[str, Any]:
        """Get convergence detection statistics."""
        stats = self._stats.copy()
        if stats["total_checks"] > 0:
            stats["elite_rate"] = round(stats["elite_convergences"] / stats["total_checks"] * 100, 2)
            stats["full_rate"] = round(stats["full_convergences"] / stats["total_checks"] * 100, 2)
        return stats
    
    def reset_stats(self) -> None:
        """Reset convergence detection statistics."""
        self._stats = {
            "total_checks": 0,
            "elite_convergences": 0,
            "full_convergences": 0,
            "partial_convergences": 0,
            "false_positives": 0
        }
