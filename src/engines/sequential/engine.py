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

class SequentialEngine:
    """
    Controls the flow of time, thought limits, and branching logic (The Backbone).
    """
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

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
            validated_total += REVISION_EXPANSION_INCREMENT
            logger.info(f"Revision detected. Expanding total steps to {validated_total} (Increment: {REVISION_EXPANSION_INCREMENT}).")
            
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
