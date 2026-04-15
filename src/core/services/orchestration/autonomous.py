"""
Autonomous & HITL Service (Domain Policy)

Manages the switch between Autonomous vs Guided execution 
and enforces Human-in-the-Loop (HITL) clearance checkpoints.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.core.config import Settings
from src.core.models.enums import CCTProfile, SessionStatus
from src.core.services.analysis.complexity import ComplexityService
from src.core.models.analysis import TaskComplexity
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

class AutonomousService:
    """
    Unified execution control service.
    
    1. LLM (Autonomous Mode): Decides if AI should run autonomously.
    2. HITL (Human Stop): Enforces hard stops and clearance.
    """
    
    def __init__(self, settings: Settings, memory: MemoryManager):
        self.settings = settings
        self.memory = memory
        self.complexity_service = ComplexityService()

    # =========================================================================
    # 1. LLM / AUTONOMOUS MODE SELECTION
    # =========================================================================

    def get_execution_mode(self, complexity: TaskComplexity) -> str:
        """
        Determines the mode based on settings and task complexity.
        Returns: 'autonomous' or 'guided'
        """
        # If no LLM configured, always guided
        if not self._has_llm_configured():
            return "guided"
        
        # Heuristic: Simple tasks are always guided to save context/tokens.
        # Sovereign tasks are always autonomous if possible for deep reasoning.
        if complexity == TaskComplexity.SIMPLE:
            return "guided"
            
        return "autonomous"

    def _has_llm_configured(self) -> bool:
        """Checks if any valid LLM provider is configured in settings."""
        if self.settings.gemini_api_key:
            return True
        if self.settings.openai_api_key:
            return True
        if self.settings.anthropic_api_key:
            return True
        if self.settings.ollama_base_url and self.settings.llm_provider == "ollama":
            return True
        return False

    # =========================================================================
    # 2. HITL / HUMAN STOP PROTECTION
    # =========================================================================

    def check_execution_allowed(self, session_id: str) -> Dict[str, Any]:
        """
        Check if tool execution is allowed for session.
        Called by orchestrator before executing any tool.
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {"allowed": False, "error": "Session not found", "code": 404}
        
        # Not HITL profile - allow
        if session.profile != CCTProfile.HUMAN_IN_THE_LOOP:
            return {"allowed": True}
        
        # HITL profile - check if hard STOP is active
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
        
        return {"allowed": True}

    def trigger_human_stop(
        self, 
        session_id: str, 
        executive_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Triggers a hard STOP for HITL sessions."""
        session = self.memory.get_session(session_id)
        if not session or session.profile != CCTProfile.HUMAN_IN_THE_LOOP:
            return {"status": "not_applicable"}

        session.status = SessionStatus.AWAITING_HUMAN_CLEARANCE
        session.hitl_triggered_at = datetime.now(timezone.utc).isoformat()
        session.executive_summary = executive_summary
        self.memory.update_session(session)

        logger.warning(f"[AUTONOMOUS] HITL STOP triggered for session {session_id}")
        
        return {
            "status": "human_stop_triggered",
            "code": 403,
            "message": "🛑 HUMAN STOP: Execution paused awaiting clearance",
            "executive_summary": executive_summary,
            "clearance_required": True
        }

    def grant_clearance(
        self, 
        session_id: str, 
        authorized_by: str,
        note: str = ""
    ) -> Dict[str, Any]:
        """Grants human clearance to a blocked session."""
        session = self.memory.get_session(session_id)
        if not session or session.status != SessionStatus.AWAITING_HUMAN_CLEARANCE:
            return {"status": "error", "message": "Session not awaiting clearance"}

        session.status = SessionStatus.CLEARED
        session.cleared_at = datetime.now(timezone.utc).isoformat()
        session.authorized_by = authorized_by
        session.authorization_note = note
        self.memory.update_session(session)

        logger.info(f"[AUTONOMOUS] HITL CLEARANCE granted for {session_id} by {authorized_by}")
        return {"status": "cleared", "session_id": session_id}

    def get_hitl_status(self, session_id: str) -> Dict[str, Any]:
        """Retrieves detailed HITL/Autonomous telemetry."""
        session = self.memory.get_session(session_id)
        if not session: return {"status": "error"}
        
        is_hitl = session.profile == CCTProfile.HUMAN_IN_THE_LOOP
        return {
            "session_id": session_id,
            "profile": session.profile.value,
            "hitl_active": is_hitl and session.status == SessionStatus.AWAITING_HUMAN_CLEARANCE,
            "cleared": session.status == SessionStatus.CLEARED if is_hitl else None,
            "triggered_at": getattr(session, 'hitl_triggered_at', None),
            "authorized_by": getattr(session, 'authorized_by', None)
        }

    def get_hitl_telemetry(self, session_id: str) -> Dict[str, Any]:
        """
        Gets HITL telemetry for a session.
        Returns telemetry including stops triggered and clearance status.
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {"session_id": session_id, "error": "session_not_found"}

        return {
            "session_id": session_id,
            "profile": session.profile.value,
            "stops_triggered": 1 if session.hitl_triggered_at else 0,
            "cleared": session.status == SessionStatus.CLEARED,
            "triggered_at": session.hitl_triggered_at,
            "authorized_by": session.authorized_by,
            "cleared_at": session.cleared_at
        }
