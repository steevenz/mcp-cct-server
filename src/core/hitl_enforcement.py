"""
Human-in-the-Loop (HITL) Enforcement Module

Provides hard STOP mechanism for mission-critical operations.
When a session is in HUMAN_IN_THE_LOOP profile and reaches Phase 7,
execution is blocked until explicit human clearance is granted.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.core.models.enums import CCTProfile, SessionStatus
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class HITLEnforcer:
    """
    Enforces Human-in-the-Loop protocol for mission-critical sessions.
    
    Implements hard STOP at Phase 7 (Clearance Checkpoint) when profile
    is HUMAN_IN_THE_LOOP. Blocks all tool execution until human grants
    explicit clearance via grant_human_clearance().
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        
    def is_hitl_enforced(self, session_id: str) -> bool:
        """
        Check if session requires HITL enforcement.
        
        Returns True if:
        - Session profile is HUMAN_IN_THE_LOOP
        - Status is AWAITING_HUMAN_CLEARANCE (hard STOP active)
        """
        session = self.memory.get_session(session_id)
        if not session:
            return False
            
        profile = getattr(session, 'profile', None)
        status = getattr(session, 'status', None)
        
        # Check if HITL profile and awaiting clearance
        is_hitl_profile = profile == CCTProfile.HUMAN_IN_THE_LOOP
        is_awaiting = status == SessionStatus.AWAITING_HUMAN_CLEARANCE
        
        return is_hitl_profile and is_awaiting
    
    def trigger_human_stop(
        self, 
        session_id: str, 
        executive_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger hard STOP at Phase 7 for HITL sessions.
        
        Changes session status to AWAITING_HUMAN_CLEARANCE and blocks
        further execution until clearance is granted.
        
        Args:
            session_id: The session to block
            executive_summary: Summary of findings for human review
            
        Returns:
            Dict with stop status and summary
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {
                "status": "error",
                "error": "Session not found",
                "code": 404
            }
        
        # Only apply to HITL profiles
        if session.profile != CCTProfile.HUMAN_IN_THE_LOOP:
            logger.info(f"Session {session_id} not HITL profile, skipping STOP")
            return {
                "status": "not_applicable",
                "message": "Session not in HITL mode",
                "profile": session.profile.value
            }
        
        # Set hard STOP status
        session.status = SessionStatus.AWAITING_HUMAN_CLEARANCE
        session.hitl_triggered_at = datetime.now(timezone.utc).isoformat()
        session.executive_summary = executive_summary
        
        self.memory.update_session(session)
        
        logger.warning(
            f"[HITL] HARD STOP triggered for session {session_id}. "
            f"Awaiting human clearance."
        )
        
        return {
            "status": "human_stop_triggered",
            "code": 403,
            "message": "🛑 HUMAN STOP: Execution paused awaiting clearance",
            "session_id": session_id,
            "hitl_status": "awaiting_clearance",
            "executive_summary": executive_summary,
            "clearance_required": True,
            "instructions": "Call grant_human_clearance() to proceed"
        }
    
    def grant_clearance(
        self, 
        session_id: str, 
        authorized_by: str,
        authorization_note: str = ""
    ) -> Dict[str, Any]:
        """
        Grant human clearance for HITL-blocked session.
        
        Changes session status from AWAITING_HUMAN_CLEARANCE to CLEARED,
        allowing execution to proceed.
        
        Args:
            session_id: The session to clear
            authorized_by: Identifier of the human granting clearance
            authorization_note: Optional notes about the authorization
            
        Returns:
            Dict with clearance status
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {
                "status": "error",
                "error": "Session not found",
                "code": 404
            }
        
        # Check if actually awaiting clearance
        if session.status != SessionStatus.AWAITING_HUMAN_CLEARANCE:
            return {
                "status": "error",
                "error": f"Session not awaiting clearance (status: {session.status})",
                "code": 400
            }
        
        # Grant clearance
        session.status = SessionStatus.CLEARED
        session.cleared_at = datetime.now(timezone.utc).isoformat()
        session.authorized_by = authorized_by
        session.authorization_note = authorization_note
        
        self.memory.update_session(session)
        
        logger.info(
            f"[HITL] CLEARANCE GRANTED for session {session_id} "
            f"by {authorized_by}"
        )
        
        return {
            "status": "cleared",
            "code": 200,
            "message": "✅ Human clearance granted. Execution may proceed.",
            "session_id": session_id,
            "authorized_by": authorized_by,
            "authorization_note": authorization_note,
            "cleared_at": session.cleared_at
        }
    
    def check_execution_allowed(self, session_id: str) -> Dict[str, Any]:
        """
        Check if tool execution is allowed for session.
        
        Called by orchestrator before executing any tool. Returns block
        response if HITL STOP is active.
        
        Returns:
            Dict with "allowed" boolean and optional block message
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {"allowed": False, "error": "Session not found", "code": 404}
        
        # Not HITL profile - allow
        if session.profile != CCTProfile.HUMAN_IN_THE_LOOP:
            return {"allowed": True}
        
        # HITL profile - check status
        if session.status == SessionStatus.AWAITING_HUMAN_CLEARANCE:
            summary = getattr(session, 'executive_summary', {})
            return {
                "allowed": False,
                "blocked_by": "HITL_ENFORCEMENT",
                "code": 403,
                "error": "🛑 EXECUTION BLOCKED: Human clearance required",
                "status": "awaiting_human_clearance",
                "executive_summary": summary,
                "instructions": "Call grant_human_clearance() to proceed"
            }
        
        # Cleared or other status - allow
        return {"allowed": True}
    
    def get_hitl_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current HITL status for session.
        
        Returns detailed status information for dashboard/monitoring.
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        is_hitl = session.profile == CCTProfile.HUMAN_IN_THE_LOOP
        
        return {
            "session_id": session_id,
            "is_hitl_profile": is_hitl,
            "profile": session.profile.value,
            "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
            "hitl_active": is_hitl and session.status == SessionStatus.AWAITING_HUMAN_CLEARANCE,
            "cleared": session.status == SessionStatus.CLEARED if is_hitl else None,
            "executive_summary": getattr(session, 'executive_summary', None),
            "triggered_at": getattr(session, 'hitl_triggered_at', None),
            "cleared_at": getattr(session, 'cleared_at', None),
            "authorized_by": getattr(session, 'authorized_by', None)
        }
