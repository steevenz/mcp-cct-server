from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.constants import PIVOT_THRESHOLD_CLARITY, PIVOT_THRESHOLD_COHERENCE
from src.utils.pipelines import PipelineSelector

logger = logging.getLogger(__name__)

class AutomaticPipelineRouter:
    """
    AutomaticPipelineRouter: Dynamic Cognitive Strategy Decider.
    
    Implements the 'Automatic Pipeline' requirement where the AI determines
    the reasoning path dynamically based on:
    1. Initial Problem Statement (Categories)
    2. Real-time Scoring Engine feedback (Clarity, Coherence thresholds)
    3. Convergence detection from the Fusion module
    
    Enterprise-ready, scalable, and follows the DDD pattern.
    """

    # Low-quality thresholds that trigger an 'Unconventional Pivot'
    # Using constants from core for centralized configuration
    PIVOT_THRESHOLD_CLARITY = PIVOT_THRESHOLD_CLARITY
    PIVOT_THRESHOLD_COHERENCE = PIVOT_THRESHOLD_COHERENCE

    def __init__(self, scoring_engine: Any):
        self.scoring = scoring_engine

    def determine_initial_pipeline(self, problem_statement: str) -> List[ThinkingStrategy]:
        """
        Delegates initial pipeline selection to the static selector (or adds noise/variety).
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
            # Fallback if history list was empty
            return session.suggested_pipeline[0] if session.suggested_pipeline else ThinkingStrategy.LINEAR

        last_thought = recent_thoughts[-1]
        metrics = last_thought.metrics

        # 1. Check for Terminal Convergence (Time to Fuse)
        if len(recent_thoughts) >= 3:
            # Simple heuristic: if we have several persona insights, trigger fusion
            if any(t.strategy == ThinkingStrategy.MULTI_AGENT_FUSION for t in recent_thoughts):
                 # Don't loop infinitely into fusion
                 pass
            elif all("persona_insight" in t.tags for t in recent_thoughts[-2:]):
                logger.info("[ROUTER] Converging: High density persona insights detected. Routing to MULTI_AGENT_FUSION.")
                return ThinkingStrategy.MULTI_AGENT_FUSION

        # 2. Check for Quality Degradation (Pivot Logic)
        if (metrics.clarity_score < self.PIVOT_THRESHOLD_CLARITY or 
            metrics.logical_coherence < self.PIVOT_THRESHOLD_COHERENCE):
            logger.warning(f"[ROUTER] Quality Drop (Clarity {metrics.clarity_score}, Coherence {metrics.logical_coherence}). Triggering UNCONVENTIONAL_PIVOT.")
            return ThinkingStrategy.UNCONVENTIONAL_PIVOT

        # 3. Progressive Path: Follow the suggested pipeline or find next logical step
        current_index = session.current_thought_number
        pipeline = session.suggested_pipeline
        
        # Bounds checking for safe pipeline access
        if pipeline and 0 <= current_index < len(pipeline):
            next_strat = pipeline[current_index]
            logger.info(f"[ROUTER] Proceeding with planned pipeline. Next: {next_strat.value}")
            return next_strat

        # 4. Final Fallback: Integrative Synthesis
        return ThinkingStrategy.INTEGRATIVE

    def should_finish(self, session: CCTSessionState, recent_thoughts: List[EnhancedThought]) -> bool:
        """Determines if the thinking process has achieved its goal."""
        if not recent_thoughts:
            return False
            
        last = recent_thoughts[-1]
        # Finish if we hit a high-confidence conclusion
        if last.thought_type == "conclusion" and last.metrics.evidence_strength > 0.8:
            return True
            
        # Or if we've reached the estimated total and quality is acceptable
        if session.current_thought_number >= session.estimated_total_thoughts:
            return last.metrics.logical_coherence > 0.7

        return False
