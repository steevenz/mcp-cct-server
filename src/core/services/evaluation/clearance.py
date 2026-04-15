"""
Internal Clearance Service (Domain Service)

Implements the Internal Clearance mechanism from whitepaper section 1:
- AI instantiates a Veteran Architect persona (25+ years experience) to audit its own output
- If logic and consistency scores meet defined thresholds, the AI grants itself "Internal Clearance" to proceed to implementation

This service enables autonomous self-auditing before execution, ensuring quality standards are met.
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.core.models.domain import EnhancedThought
from src.core.services.analysis.scoring import ScoringService

logger = logging.getLogger(__name__)


@dataclass
class ClearanceDecision:
    """Result of internal clearance decision."""
    granted: bool
    rationale: str
    threshold_met: bool
    logic_score: float
    consistency_score: float
    required_threshold: float
    recommendations: list[str]


class ClearanceService:
    """
    Internal Clearance Service for autonomous self-auditing.
    
    Implements the Veteran Architect persona instantiation for self-audit,
    ensuring the AI grants itself clearance only when quality thresholds are met.
    """
    
    # Default thresholds for internal clearance
    DEFAULT_LOGIC_THRESHOLD = 0.85
    DEFAULT_CONSISTENCY_THRESHOLD = 0.80
    DEFAULT_EVIDENCE_THRESHOLD = 0.75
    
    def __init__(
        self, 
        scoring_service: ScoringService,
        logic_threshold: float = DEFAULT_LOGIC_THRESHOLD,
        consistency_threshold: float = DEFAULT_CONSISTENCY_THRESHOLD,
        evidence_threshold: float = DEFAULT_EVIDENCE_THRESHOLD
    ):
        self.scoring = scoring_service
        self.logic_threshold = logic_threshold
        self.consistency_threshold = consistency_threshold
        self.evidence_threshold = evidence_threshold
        
        logger.info(
            f"[INTERNAL_CLEARANCE] Service initialized with thresholds: "
            f"logic={logic_threshold}, consistency={consistency_threshold}, evidence={evidence_threshold}"
        )
    
    def evaluate_clearance(
        self,
        thought: EnhancedThought,
        history: list[EnhancedThought],
        model_id: str = "claude-3-5-sonnet-20240620"
    ) -> ClearanceDecision:
        """
        Evaluates whether to grant internal clearance for a thought.
        
        Instantiates the Veteran Architect persona to audit the thought's quality
        against defined thresholds before granting clearance.
        
        Args:
            thought: The thought to evaluate for clearance
            history: Previous thoughts for context and consistency analysis
            model_id: The model ID for token counting
            
        Returns:
            ClearanceDecision with grant status and rationale
        """
        logger.info(f"[INTERNAL_CLEARANCE] Evaluating thought {thought.id} for internal clearance")
        
        # Ensure thought has metrics
        if not thought.metrics:
            logger.warning(f"[INTERNAL_CLEARANCE] Thought {thought.id} has no metrics. Scoring now.")
            thought.metrics = self.scoring.analyze_thought(thought, history, model_id=model_id)
        
        metrics = thought.metrics
        
        # Extract key metrics
        logic_score = metrics.logical_coherence
        consistency_score = metrics.clarity_score  # Using clarity as proxy for internal consistency
        evidence_score = metrics.evidence_strength
        
        logger.debug(
            f"[INTERNAL_CLEARANCE] Thought {thought.id} metrics: "
            f"logic={logic_score:.3f}, consistency={consistency_score:.3f}, evidence={evidence_score:.3f}"
        )
        
        # Evaluate against thresholds
        logic_pass = logic_score >= self.logic_threshold
        consistency_pass = consistency_score >= self.consistency_threshold
        evidence_pass = evidence_score >= self.evidence_threshold
        
        # Overall decision: ALL thresholds must be met
        threshold_met = logic_pass and consistency_pass and evidence_pass
        granted = threshold_met
        
        # Build rationale
        rationale_parts = []
        recommendations = []
        
        if not logic_pass:
            rationale_parts.append(f"Logic coherence ({logic_score:.3f}) below threshold ({self.logic_threshold})")
            recommendations.append("Improve logical flow and argument structure")
        
        if not consistency_pass:
            rationale_parts.append(f"Consistency score ({consistency_score:.3f}) below threshold ({self.consistency_threshold})")
            recommendations.append("Enhance clarity and reduce ambiguity")
        
        if not evidence_pass:
            rationale_parts.append(f"Evidence strength ({evidence_score:.3f}) below threshold ({self.evidence_threshold})")
            recommendations.append("Add specific examples, data, or code to support claims")
        
        if threshold_met:
            rationale = (
                f"Internal clearance GRANTED. All thresholds met: "
                f"logic={logic_score:.3f} >= {self.logic_threshold}, "
                f"consistency={consistency_score:.3f} >= {self.consistency_threshold}, "
                f"evidence={evidence_score:.3f} >= {self.evidence_threshold}"
            )
            logger.info(f"[INTERNAL_CLEARANCE] Thought {thought.id} GRANTED internal clearance")
        else:
            rationale = f"Internal clearance DENIED. " + "; ".join(rationale_parts)
            logger.warning(f"[INTERNAL_CLEARANCE] Thought {thought.id} DENIED internal clearance: {rationale}")
        
        return ClearanceDecision(
            granted=granted,
            rationale=rationale,
            threshold_met=threshold_met,
            logic_score=logic_score,
            consistency_score=consistency_score,
            required_threshold=min(self.logic_threshold, self.consistency_threshold, self.evidence_threshold),
            recommendations=recommendations
        )
    
    def evaluate_session_clearance(
        self,
        session_id: str,
        history: list[EnhancedThought],
        model_id: str = "claude-3-5-sonnet-20240620"
    ) -> Dict[str, Any]:
        """
        Evaluates clearance for an entire session based on aggregate metrics.
        
        Used to determine if a session has met quality standards for conclusion.
        
        Args:
            session_id: The session ID
            history: All thoughts in the session
            model_id: The model ID for token counting
            
        Returns:
            Dict with clearance decision and session-level metrics
        """
        if not history:
            return {
                "granted": False,
                "rationale": "No thoughts to evaluate",
                "session_id": session_id,
                "thought_count": 0
            }
        
        logger.info(f"[INTERNAL_CLEARANCE] Evaluating session {session_id} with {len(history)} thoughts")
        
        # Calculate aggregate metrics
        avg_logic = sum(t.metrics.logical_coherence for t in history if t.metrics) / len(history)
        avg_consistency = sum(t.metrics.clarity_score for t in history if t.metrics) / len(history)
        avg_evidence = sum(t.metrics.evidence_strength for t in history if t.metrics) / len(history)
        
        # Evaluate against thresholds (slightly relaxed for session-level)
        session_logic_threshold = self.logic_threshold * 0.95  # 5% relaxation
        session_consistency_threshold = self.consistency_threshold * 0.95
        session_evidence_threshold = self.evidence_threshold * 0.95
        
        logic_pass = avg_logic >= session_logic_threshold
        consistency_pass = avg_consistency >= session_consistency_threshold
        evidence_pass = avg_evidence >= session_evidence_threshold
        
        threshold_met = logic_pass and consistency_pass and evidence_pass
        granted = threshold_met
        
        rationale = (
            f"Session clearance {'GRANTED' if granted else 'DENIED'}. "
            f"Avg logic={avg_logic:.3f} (threshold={session_logic_threshold}), "
            f"avg consistency={avg_consistency:.3f} (threshold={session_consistency_threshold}), "
            f"avg evidence={avg_evidence:.3f} (threshold={session_evidence_threshold})"
        )
        
        logger.info(f"[INTERNAL_CLEARANCE] Session {session_id} {'GRANTED' if granted else 'DENIED'} clearance")
        
        return {
            "granted": granted,
            "rationale": rationale,
            "session_id": session_id,
            "thought_count": len(history),
            "avg_logic_score": avg_logic,
            "avg_consistency_score": avg_consistency,
            "avg_evidence_score": avg_evidence,
            "thresholds": {
                "logic": session_logic_threshold,
                "consistency": session_consistency_threshold,
                "evidence": session_evidence_threshold
            }
        }
    
    def adjust_thresholds(
        self,
        logic_threshold: Optional[float] = None,
        consistency_threshold: Optional[float] = None,
        evidence_threshold: Optional[float] = None
    ) -> None:
        """
        Adjust clearance thresholds dynamically.
        
        Allows for adaptive quality standards based on context or user preferences.
        
        Args:
            logic_threshold: New logic threshold (0.0-1.0)
            consistency_threshold: New consistency threshold (0.0-1.0)
            evidence_threshold: New evidence threshold (0.0-1.0)
        """
        if logic_threshold is not None:
            self.logic_threshold = max(0.0, min(1.0, logic_threshold))
            logger.info(f"[INTERNAL_CLEARANCE] Logic threshold adjusted to {self.logic_threshold}")
        
        if consistency_threshold is not None:
            self.consistency_threshold = max(0.0, min(1.0, consistency_threshold))
            logger.info(f"[INTERNAL_CLEARANCE] Consistency threshold adjusted to {self.consistency_threshold}")
        
        if evidence_threshold is not None:
            self.evidence_threshold = max(0.0, min(1.0, evidence_threshold))
            logger.info(f"[INTERNAL_CLEARANCE] Evidence threshold adjusted to {self.evidence_threshold}")
