"""
Eval-First Service: Enforce "No Code Without Criteria" for Engineering Tasks

Implements the CCT v5.0 Engineering Domain requirement for validation before implementation.
Ensures that capability and regression evals are defined before any code generation occurs.

Reference: docs/context-tree/Engineering/Workflows/EvalFirst.md
"""
import logging
from typing import Dict, Any, Optional, List

from src.core.models.evaluation.eval import EvalStatus, EvalCriteria

logger = logging.getLogger(__name__)


class EvalService:
    """
    Service enforcing Eval-First protocol for engineering tasks.
    
    Ensures that evaluation criteria are defined before implementation begins.
    """
    
    def __init__(self):
        self._eval_store: Dict[str, EvalCriteria] = {}
    
    def check_eval_status(self, session_id: str) -> EvalStatus:
        """
        Check the evaluation criteria status for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            EvalStatus indicating the current state
        """
        criteria = self._eval_store.get(session_id)
        if not criteria:
            return EvalStatus.NOT_DEFINED
        
        if criteria.is_complete():
            return EvalStatus.COMPLETE
        
        # Partial if any criteria defined
        if (criteria.capability_evals or 
            criteria.regression_evals or 
            criteria.success_metrics):
            return EvalStatus.PARTIAL
        
        return EvalStatus.NOT_DEFINED
    
    def define_criteria(
        self,
        session_id: str,
        capability_evals: List[str],
        regression_evals: List[str],
        success_metrics: List[str],
        baseline_snapshot: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Define evaluation criteria for a session.
        
        Args:
            session_id: The session identifier
            capability_evals: List of capability evaluation statements
            regression_evals: List of regression evaluation statements
            success_metrics: List of success metric definitions
            baseline_snapshot: Optional baseline state snapshot
            
        Returns:
            Result dictionary with status and criteria
        """
        criteria = EvalCriteria(
            capability_evals=capability_evals,
            regression_evals=regression_evals,
            success_metrics=success_metrics,
            baseline_snapshot=baseline_snapshot
        )
        
        self._eval_store[session_id] = criteria
        
        logger.info(
            f"[EVAL-FIRST] Criteria defined for session {session_id}: "
            f"{len(capability_evals)} capability evals, "
            f"{len(regression_evals)} regression evals, "
            f"{len(success_metrics)} success metrics"
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "eval_status": EvalStatus.COMPLETE if criteria.is_complete() else EvalStatus.PARTIAL,
            "criteria": criteria.to_dict()
        }
    
    def validate_before_implementation(self, session_id: str) -> Dict[str, Any]:
        """
        Validate that criteria are met before allowing implementation.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Validation result with allow_implementation flag
        """
        status = self.check_eval_status(session_id)
        criteria = self._eval_store.get(session_id)
        
        if status == EvalStatus.COMPLETE:
            logger.info(f"[EVAL-FIRST] Session {session_id} validated for implementation")
            return {
                "allow_implementation": True,
                "status": "validated",
                "message": "Evaluation criteria complete. Implementation approved.",
                "criteria": criteria.to_dict() if criteria else None
            }
        
        elif status == EvalStatus.PARTIAL:
            logger.warning(
                f"[EVAL-FIRST] Session {session_id} has partial criteria. "
                "Implementation blocked until complete."
            )
            return {
                "allow_implementation": False,
                "status": "partial",
                "message": "Evaluation criteria incomplete. Please define all required criteria.",
                "missing": self._get_missing_criteria(criteria),
                "criteria": criteria.to_dict() if criteria else None
            }
        
        else:  # NOT_DEFINED
            logger.warning(
                f"[EVAL-FIRST] Session {session_id} has no evaluation criteria. "
                "Implementation blocked."
            )
            return {
                "allow_implementation": False,
                "status": "not_defined",
                "message": "No evaluation criteria defined. Please define capability evals, regression evals, and success metrics before implementation.",
                "required": [
                    "capability_evals: What must work?",
                    "regression_evals: What must not break?",
                    "success_metrics: How do we measure success?"
                ]
            }
    
    def _get_missing_criteria(self, criteria: EvalCriteria) -> List[str]:
        """Get list of missing criteria."""
        missing = []
        if not criteria.capability_evals:
            missing.append("capability_evals")
        if not criteria.regression_evals:
            missing.append("regression_evals")
        if not criteria.success_metrics:
            missing.append("success_metrics")
        return missing
    
    def get_criteria(self, session_id: str) -> Optional[EvalCriteria]:
        """Get evaluation criteria for a session."""
        return self._eval_store.get(session_id)
    
    def clear_session(self, session_id: str) -> None:
        """Clear evaluation criteria for a session."""
        if session_id in self._eval_store:
            del self._eval_store[session_id]
            logger.info(f"[EVAL-FIRST] Cleared criteria for session {session_id}")
    
    def generate_criteria_prompt(self, problem_statement: str) -> str:
        """
        Generate a prompt to help define evaluation criteria.
        
        Args:
            problem_statement: The problem statement to analyze
            
        Returns:
            Prompt text for criteria definition
        """
        return f"""
Based on the following task, please define evaluation criteria:

Task: {problem_statement}

Please provide:
1. CAPABILITY EVALS: What specific functionality must work? (Be specific and testable)
2. REGRESSION EVALS: What existing functionality must not break? (Identify dependencies)
3. SUCCESS METRICS: How will we measure successful implementation? (Quantitative where possible)

Format your response as a structured list for each category.
"""
