from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.constants import PIVOT_THRESHOLD_CLARITY, PIVOT_THRESHOLD_COHERENCE
# [NEW IMPORT] Use the new domain policy location
from src.core.services.orchestration.policy import PolicyService
from src.core.services.analysis.metrics import get_metrics_summary, record_engine_execution

logger = logging.getLogger(__name__)

class RoutingService:
    """
    IntelligenceRouter: Dynamic Cognitive Strategy Decider (Domain Service).
    
    Implements the 'Automatic Pipeline' requirement where the AI determines
    the reasoning path dynamically based on:
    1. Initial Problem Statement (Categories)
    2. Real-time Scoring Engine feedback (Clarity, Coherence thresholds)
    3. Convergence detection from the Fusion module
    
    Enterprise-ready, follows the 'Lego' Principle and DDD.
    """

    # Low-quality thresholds that trigger an 'Unconventional Pivot'
    PIVOT_THRESHOLD_CLARITY = PIVOT_THRESHOLD_CLARITY
    PIVOT_THRESHOLD_COHERENCE = PIVOT_THRESHOLD_COHERENCE

    def __init__(self, scoring_engine: Any = None):
        # scoring_engine is optional for now, used for future deep diagnostics
        self.scoring = scoring_engine
        # Metrics collector for tracking routing performance
        self.metrics_enabled = True

    def determine_initial_pipeline(self, problem_statement: str) -> List[ThinkingStrategy]:
        """
        Delegates initial pipeline selection to the Domain Policy Manager.
        """
        return PipelineSelector.select_pipeline(problem_statement)

    def next_strategy(
        self, 
        session: CCTSessionState, 
        recent_thoughts: List[EnhancedThought]
    ) -> ThinkingStrategy:
        """
        Main routing logic for the 'Automatic Pipeline'.
        Decides if we should follow the current pipeline, pivot, or trigger fusion.
        """
        if not recent_thoughts:
            # Fallback to planned pipeline
            return session.suggested_pipeline[0] if session.suggested_pipeline else ThinkingStrategy.LINEAR

        last_thought = recent_thoughts[-1]
        metrics = last_thought.metrics

        # 1. [COGNITIVE CONVERGENCE] Check for Terminal Convergence
        if len(recent_thoughts) >= 3:
            if any(t.strategy == ThinkingStrategy.MULTI_AGENT_FUSION for t in recent_thoughts):
                 pass
            elif all("persona_insight" in t.tags for t in recent_thoughts[-2:]):
                logger.info(
                    f"[ROUTER] Converging: High density persona insights detected. Routing to MULTI_AGENT_FUSION | "
                    f"session={session.session_id} | "
                    f"persona_count={sum(1 for t in recent_thoughts if 'persona_insight' in t.tags)}"
                )
                return ThinkingStrategy.MULTI_AGENT_FUSION

        # 2. [QUALITY AUDIT] Check for Quality Degradation (Pivot Logic)
        if (metrics.clarity_score < self.PIVOT_THRESHOLD_CLARITY or 
            metrics.logical_coherence < self.PIVOT_THRESHOLD_COHERENCE):
            logger.warning(
                f"[ROUTER] Quality Drop Detected - Triggering UNCONVENTIONAL_PIVOT | "
                f"session={session.session_id} | "
                f"thought_count={session.current_thought_number} | "
                f"clarity={metrics.clarity_score:.3f} (threshold: {self.PIVOT_THRESHOLD_CLARITY}) | "
                f"coherence={metrics.logical_coherence:.3f} (threshold: {self.PIVOT_THRESHOLD_COHERENCE})"
            )
            # Record pivot trigger for metrics
            if self.metrics_enabled:
                record_engine_execution(
                    engine_name="IntelligenceRouter",
                    strategy="PIVOT_TRIGGER",
                    execution_time_ms=0.0,
                    input_tokens=metrics.input_tokens,
                    output_tokens=metrics.output_tokens,
                    clarity_score=metrics.clarity_score,
                    coherence_score=metrics.logical_coherence,
                    evidence_score=metrics.evidence_strength,
                    novelty_score=metrics.novelty_score,
                    session_id=session.session_id
                )
            return ThinkingStrategy.UNCONVENTIONAL_PIVOT

        # 3. [ORCHESTRATION PATH] Follow the suggested pipeline or next step
        current_index = session.current_thought_number
        pipeline = session.suggested_pipeline
        
        if pipeline and 0 <= current_index < len(pipeline):
            next_strat = pipeline[current_index]
            logger.info(
                f"[ROUTER] Proceeding with planned pipeline | "
                f"session={session.session_id} | "
                f"step={current_index}/{len(pipeline)} | "
                f"next_strategy={next_strat.value}"
            )
            # Record pipeline progression for metrics
            if self.metrics_enabled and last_thought.metrics:
                record_engine_execution(
                    engine_name="IntelligenceRouter",
                    strategy=next_strat.value,
                    execution_time_ms=0.0,
                    input_tokens=last_thought.metrics.input_tokens,
                    output_tokens=last_thought.metrics.output_tokens,
                    clarity_score=last_thought.metrics.clarity_score,
                    coherence_score=last_thought.metrics.logical_coherence,
                    evidence_score=last_thought.metrics.evidence_strength,
                    novelty_score=last_thought.metrics.novelty_score,
                    session_id=session.session_id
                )
            return next_strat

        # 4. [FALLBACK] Final Synthesis
        return ThinkingStrategy.INTEGRATIVE

    def _calculate_convergence_factors(self, recent_thoughts: List[EnhancedThought]) -> Dict[str, bool]:
        """
        Calculate individual convergence factors for multi-factor analysis.
        
        Returns dictionary with 5 boolean factors:
        - coherence_streak: High coherence for 2+ consecutive thoughts
        - strong_evidence: Evidence strength >= 0.8
        - high_persona_density: 2+ persona insights in recent thoughts
        - no_degradation: No quality degradation in last 3 steps
        - is_conclusion: Conclusion type with high evidence
        """
        last = recent_thoughts[-1]
        metrics = last.metrics
        
        # Get recent metrics for analysis
        recent_metrics = [t.metrics for t in recent_thoughts[-3:] if t.metrics]
        
        return {
            "coherence_streak": all(
                m.logical_coherence >= 0.95 for m in recent_metrics[-2:]
            ) if len(recent_metrics) >= 2 else False,
            "strong_evidence": metrics.evidence_strength >= 0.8,
            "high_persona_density": sum(
                1 for t in recent_thoughts[-3:] if "persona_insight" in t.tags
            ) >= 2,
            "no_degradation": all(
                m.clarity_score >= self.PIVOT_THRESHOLD_CLARITY and 
                m.logical_coherence >= self.PIVOT_THRESHOLD_COHERENCE
                for m in recent_metrics
            ),
            "is_conclusion": last.thought_type == "conclusion" and metrics.evidence_strength > 0.8
        }

    def _check_elite_convergence(self, session: CCTSessionState, metrics, factors: Dict[str, bool]) -> bool:
        """
        Check for elite convergence (score >= 4/5 factors).
        
        Elite convergence triggers early finish when multiple convergence
        factors are simultaneously satisfied.
        """
        convergence_score = sum(factors.values())
        
        if convergence_score >= 4:
            reasons = []
            if factors["coherence_streak"]: reasons.append("high_coherence_streak")
            if factors["strong_evidence"]: reasons.append("strong_evidence")
            if factors["high_persona_density"]: reasons.append("persona_insights")
            if factors["no_degradation"]: reasons.append("no_degradation")
            if factors["is_conclusion"]: reasons.append("conclusion_type")
            
            logger.info(
                f"[ROUTER] Early Convergence Detected (score={convergence_score}/5): {', '.join(reasons)} | "
                f"session={session.session_id} | "
                f"thought_count={session.current_thought_number} | "
                f"coherence={metrics.logical_coherence:.3f} | "
                f"evidence={metrics.evidence_strength:.3f} | "
                f"clarity={metrics.clarity_score:.3f}"
            )
            # Record convergence detection for metrics
            if self.metrics_enabled:
                record_engine_execution(
                    engine_name="IntelligenceRouter",
                    strategy="CONVERGENCE_DETECTION",
                    execution_time_ms=0.0,
                    input_tokens=metrics.input_tokens,
                    output_tokens=metrics.output_tokens,
                    clarity_score=metrics.clarity_score,
                    coherence_score=metrics.logical_coherence,
                    evidence_score=metrics.evidence_strength,
                    novelty_score=metrics.novelty_score,
                    session_id=session.session_id
                )
            return True
        return False

    def _check_standard_convergence(self, session: CCTSessionState, metrics, is_conclusion: bool) -> bool:
        """
        Check for standard convergence (conclusion type with high evidence).
        """
        if is_conclusion:
            logger.info(
                f"[ROUTER] Standard Convergence: Conclusion with high evidence strength | "
                f"session={session.session_id} | "
                f"thought_count={session.current_thought_number} | "
                f"evidence={metrics.evidence_strength:.3f}"
            )
            # Record standard convergence for metrics
            if self.metrics_enabled:
                record_engine_execution(
                    engine_name="IntelligenceRouter",
                    strategy="STANDARD_CONVERGENCE",
                    execution_time_ms=0.0,
                    input_tokens=metrics.input_tokens,
                    output_tokens=metrics.output_tokens,
                    clarity_score=metrics.clarity_score,
                    coherence_score=metrics.logical_coherence,
                    evidence_score=metrics.evidence_strength,
                    novelty_score=metrics.novelty_score,
                    session_id=session.session_id
                )
            return True
        return False

    def _check_timeout_convergence(self, session: CCTSessionState, metrics) -> bool:
        """
        Check for timeout convergence (reached estimated steps with acceptable quality).
        """
        if session.current_thought_number >= session.estimated_total_thoughts:
            if metrics.logical_coherence > 0.7:
                logger.info(
                    f"[ROUTER] Timeout Convergence: Estimated steps completed with acceptable coherence | "
                    f"session={session.session_id} | "
                    f"thought_count={session.current_thought_number}/{session.estimated_total_thoughts} | "
                    f"coherence={metrics.logical_coherence:.3f}"
                )
                # Record timeout convergence for metrics
                if self.metrics_enabled:
                    record_engine_execution(
                        engine_name="IntelligenceRouter",
                        strategy="TIMEOUT_CONVERGENCE",
                        execution_time_ms=0.0,
                        input_tokens=metrics.input_tokens,
                        output_tokens=metrics.output_tokens,
                        clarity_score=metrics.clarity_score,
                        coherence_score=metrics.logical_coherence,
                        evidence_score=metrics.evidence_strength,
                        novelty_score=metrics.novelty_score,
                        session_id=session.session_id
                    )
                return True
            else:
                logger.warning(
                    f"[ROUTER] Timeout reached but coherence too low, continuing... | "
                    f"session={session.session_id} | "
                    f"thought_count={session.current_thought_number}/{session.estimated_total_thoughts} | "
                    f"coherence={metrics.logical_coherence:.3f} (threshold: 0.700)"
                )
                return False
        return False

    def should_finish(self, session: CCTSessionState, recent_thoughts: List[EnhancedThought]) -> bool:
        """
        Enhanced Early Convergence Detection with multi-factor analysis.
        
        Convergence Criteria (from CCT v5.0 §6.D):
        1. Logical coherence >= 0.95 for 2+ consecutive thoughts
        2. Evidence strength >= 0.8
        3. High-density persona insights detected
        4. No quality degradation in last 3 steps
        5. Conclusion thought type with high confidence
        """
        if not recent_thoughts or len(recent_thoughts) < 2:
            return False
            
        last = recent_thoughts[-1]
        metrics = last.metrics
        
        # Calculate convergence factors
        factors = self._calculate_convergence_factors(recent_thoughts)
        
        # Check elite convergence (score >= 4/5)
        if self._check_elite_convergence(session, metrics, factors):
            return True
        
        # Check standard convergence (conclusion type)
        if self._check_standard_convergence(session, metrics, factors["is_conclusion"]):
            return True
        
        # Check timeout convergence (reached estimated steps)
        if self._check_timeout_convergence(session, metrics):
            return True
        
        return False

    def get_routing_metrics(self) -> Dict[str, Any]:
        """
        Get summary of routing performance metrics.
        
        Returns:
            Dictionary containing routing statistics including pivot triggers,
            convergence detections, and overall performance metrics.
        """
        from src.core.services.analysis.metrics import get_metrics_summary
        return get_metrics_summary()
