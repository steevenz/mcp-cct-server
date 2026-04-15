import logging
from typing import Optional, Dict, Any

from src.core.models.domain import CCTSessionState
from src.core.models import SequentialContext
from src.core.models.enums import SessionStatus
from src.core.constants import (
    MAX_THOUGHTS_PER_SESSION,
    REVISION_EXPANSION_INCREMENT,
    BOUNDARY_EXTENSION_INCREMENT,
)
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class RevisionTracker:
    """
    Tracks revision count per session for budget management.
    
    Implements the "Revision Penalty" concept from CCT v5.0:
    - Each revision costs +2 to the budget
    - Tracks total revisions for audit purposes
    """
    
    def __init__(self):
        self._session_revisions: Dict[str, int] = {}
        self._total_penalty_steps: Dict[str, int] = {}
    
    def record_revision(self, session_id: str) -> int:
        """Record a revision for a session. Returns new revision count."""
        if session_id not in self._session_revisions:
            self._session_revisions[session_id] = 0
            self._total_penalty_steps[session_id] = 0
        
        self._session_revisions[session_id] += 1
        self._total_penalty_steps[session_id] += REVISION_EXPANSION_INCREMENT
        
        logger.info(
            f"[REVISION TRACKER] Session {session_id}: "
            f"Revision #{self._session_revisions[session_id]} "
            f"(+{REVISION_EXPANSION_INCREMENT} steps, total penalty: {self._total_penalty_steps[session_id]})"
        )
        
        return self._session_revisions[session_id]
    
    def get_revision_count(self, session_id: str) -> int:
        """Get total revision count for a session."""
        return self._session_revisions.get(session_id, 0)
    
    def get_total_penalty(self, session_id: str) -> int:
        """Get total budget penalty from revisions."""
        return self._total_penalty_steps.get(session_id, 0)
    
    def reset_session(self, session_id: str) -> None:
        """Reset tracking for a session."""
        if session_id in self._session_revisions:
            del self._session_revisions[session_id]
            del self._total_penalty_steps[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall revision statistics."""
        total_revisions = sum(self._session_revisions.values())
        total_penalty = sum(self._total_penalty_steps.values())
        
        return {
            "tracked_sessions": len(self._session_revisions),
            "total_revisions": total_revisions,
            "total_penalty_steps": total_penalty,
            "avg_revisions_per_session": total_revisions / len(self._session_revisions) if self._session_revisions else 0,
            "session_breakdown": {
                sid: {"revisions": count, "penalty": self._total_penalty_steps.get(sid, 0)}
                for sid, count in self._session_revisions.items()
            }
        }


class SequentialEngine:
    """
    Controls the flow of time, thought limits, and branching logic (The Backbone).
    
    Enhanced with revision tracking and budget management per CCT v5.0 §6.C.
    """
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.revision_tracker = RevisionTracker()

    def process_sequence_step(
        self, 
        session_id: str, 
        llm_thought_number: int,
        llm_estimated_total: int,
        next_thought_needed: bool,
        is_revision: bool = False, 
        revises_id: Optional[str] = None,
        branch_from_id: Optional[str] = None,
        branch_id: Optional[str] = None
    ) -> SequentialContext:
        session = self.memory.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found. Cannot process sequence step.")

        # [SECURITY H1] Enforce per-session thought flood limit
        if session.current_thought_number >= MAX_THOUGHTS_PER_SESSION:
            raise PermissionError(
                f"[SECURITY] Session '{session_id}' has reached the maximum thought limit "
                f"({MAX_THOUGHTS_PER_SESSION}). Start a new session to continue."
            )

        # 1. SEQUENCE VALIDATION
        expected_thought_number = session.current_thought_number + 1
        
        if llm_thought_number != expected_thought_number:
            logger.warning(f"LLM Sequence Hallucination in {session_id}. Expected {expected_thought_number}. Auto-correcting.")
            validated_thought_number = expected_thought_number
        else:
            validated_thought_number = expected_thought_number

        session.current_thought_number = validated_thought_number

        # 2. DYNAMC EXPANSION LOGIC
        validated_total = max(session.estimated_total_thoughts, llm_estimated_total)

        if is_revision:
            # Record revision and apply penalty
            self.revision_tracker.record_revision(session_id)
            validated_total += REVISION_EXPANSION_INCREMENT
            logger.info(
                f"[SEQUENTIAL] Revision detected for {session_id}. "
                f"Expanding total steps to {validated_total} "
                f"(+{REVISION_EXPANSION_INCREMENT} penalty). "
                f"Total revisions: {self.revision_tracker.get_revision_count(session_id)}"
            )
            
        if next_thought_needed and validated_thought_number >= validated_total:
            validated_total = validated_thought_number + 1
            logger.debug(f"Boundary reached. Extending total to {validated_total}.")

        session.estimated_total_thoughts = validated_total

        # 3. BRANCHING VALIDATION
        if branch_from_id:
            parent_thought = self.memory.get_thought(branch_from_id)
            if not parent_thought:
                branch_from_id = None
            else:
                logger.info(f"Branching detected. Diverging from node {branch_from_id} into '{branch_id}'.")

        # ========================================================
        # CRITICAL DB UPDATE: Save mutated session back to SQLite
        # ========================================================
        self.memory.update_session(session)

        return SequentialContext(
            thought_number=validated_thought_number,
            estimated_total_thoughts=validated_total,
            is_revision=is_revision,
            revises_thought_id=revises_id,
            branch_from_id=branch_from_id,
            branch_id=branch_id,
            next_thought_needed=next_thought_needed
        )

    def evaluate_convergence(
        self, 
        session_id: str, 
        next_thought_needed: bool,
        metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        session = self.memory.get_session(session_id)
        if not session:
            return {"is_ready": False, "reason": "Session not found."}
            
        if next_thought_needed:
            return {"is_ready": False, "reason": "LLM explicitly requested continuation."}
            
        # [EARLY CONVERGENCE DETECTION] v5.0 Master Protocol
        # Check for elite coherence and evidence density to save tokens
        if metrics:
            coherence = metrics.get("logical_coherence", 0.0)
            evidence = metrics.get("evidence_strength", 0.0)
            
            # High bar for convergence: Coherence > 0.95 AND Evidence > 0.8
            if coherence >= 0.95 and evidence >= 0.8:
                logger.info(f"Early Convergence detected for {session_id} (Coherence: {coherence}, Evidence: {evidence}).")
                session.status = SessionStatus.COMPLETED
                self.memory.update_session(session)
                return {
                    "is_ready": True, 
                    "reason": "Elite convergence achieved (Metacognitive Audit success).",
                    "early_stop": True
                }

        minimum_depth = 3
        if len(session.history_ids) < minimum_depth:
            return {"is_ready": False, "reason": f"Minimum cognitive depth ({minimum_depth} steps) not reached."}
            
        if session.requires_human_decision:
            return {"is_ready": False, "reason": "Awaiting human architectural decision."}

        # Update status and save to DB
        session.status = SessionStatus.COMPLETED
        self.memory.update_session(session)
        
        return {
            "is_ready": True, 
            "reason": "Sequence limits met and no further thoughts required."
        }

    def format_sequence_prompt(self, session_id: str) -> str:
        session = self.memory.get_session(session_id)
        if not session:
            return ""
            
        return (
            f"[SYSTEM STATE] You are currently on Thought {session.current_thought_number} "
            f"of an estimated {session.estimated_total_thoughts}. "
            f"Please structure your next JSON output accordingly."
        )

    def extend_budget(self, session_id: str, additional_steps: int, reason: str = "") -> Dict[str, Any]:
        """
        Extend the thought budget for a session.
        
        Implements explicit budget management from CCT v5.0 §6.C:
        - Allows manual budget extension
        - Records reason for audit trail
        - Tracks total budget vs original estimate
        
        Args:
            session_id: The session to extend
            additional_steps: Number of steps to add
            reason: Audit reason for the extension
            
        Returns:
            Dict with new budget info
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        old_total = session.estimated_total_thoughts
        new_total = old_total + additional_steps
        
        # Enforce hard limit
        if new_total > MAX_THOUGHTS_PER_SESSION:
            return {
                "success": False,
                "error": f"Extension would exceed maximum ({MAX_THOUGHTS_PER_SESSION})",
                "requested": new_total,
                "maximum": MAX_THOUGHTS_PER_SESSION
            }
        
        session.estimated_total_thoughts = new_total
        self.memory.update_session(session)
        
        logger.info(
            f"[SEQUENTIAL] Budget extended for {session_id}: "
            f"{old_total} -> {new_total} (+{additional_steps}). Reason: {reason or 'Not specified'}"
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "previous_total": old_total,
            "new_total": new_total,
            "extension": additional_steps,
            "reason": reason,
            "revision_count": self.revision_tracker.get_revision_count(session_id),
            "revision_penalty": self.revision_tracker.get_total_penalty(session_id)
        }
    
    def get_session_budget_info(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive budget information for a session."""
        session = self.memory.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        current = session.current_thought_number
        total = session.estimated_total_thoughts
        revisions = self.revision_tracker.get_revision_count(session_id)
        penalty = self.revision_tracker.get_total_penalty(session_id)
        
        return {
            "session_id": session_id,
            "current_thought": current,
            "estimated_total": total,
            "remaining": max(0, total - current),
            "utilization_percent": round((current / total * 100), 1) if total > 0 else 0,
            "revision_count": revisions,
            "revision_penalty_steps": penalty,
            "is_extended": revisions > 0,
            "status": "critical" if current >= total else "warning" if current >= total * 0.8 else "ok"
        }
