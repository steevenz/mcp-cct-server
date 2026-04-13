from __future__ import annotations
from typing import Any
import logging
import sqlite3
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

from src.core.validators import validate_session_id, validate_problem_statement
from src.engines.orchestrator import CognitiveOrchestrator
from src.utils.pipelines import PipelineSelector
from src.core.rate_limiter import get_rate_limiter
from src.core.config import load_settings

logger = logging.getLogger(__name__)

def register_session_tools(mcp: FastMCP, orchestrator: CognitiveOrchestrator, settings: Any | None = None) -> None:
    """Registers session management tools based on configured groups."""
    if settings is None:
        enabled = {"core", "session", "hitl"}
    else:
        enabled = settings.enabled_tool_groups

    if "core" in enabled:
        @mcp.tool()
        def start_cct_session(problem_statement: str, profile: str = "balanced", model_id: str = "") -> dict[str, object]:
            """
            Initializes a new CCT session.
            This MUST be the first tool called in any cognitive workflow.
            
            IMPORTANT: For accurate token economy and cost tracking, you MUST pass your active model ID 
            in the 'model_id' parameter (e.g., 'gemini-1.5-flash', 'claude-3-5-sonnet', etc.).
            """
            # Pre-validate problem statement
            if error := validate_problem_statement(problem_statement):
                return {"status": "error", "error": error}
            if model_id:
                return orchestrator.start_session(problem_statement, profile, model_id)
            return orchestrator.start_session(problem_statement, profile)

    if "session" in enabled:
        @mcp.tool()
        def list_cct_sessions() -> dict[str, list[str]]:
            """Lists all active cognitive session IDs."""
            return {"sessions": orchestrator.memory.list_sessions()}

        @mcp.tool()
        def get_thinking_path(session_id: str, session_token: str = "") -> dict[str, object]:
            """
            Retrieves the complete sequential path of thoughts for a session.
            Use this to review the logic progression.

            SECURITY: Requires the session_token issued at session creation.
            Store the token from start_cct_session and pass it here.
            """
            # Pre-validate session ID format
            if error := validate_session_id(session_id):
                return {"status": "error", "error": error}
            
            session = orchestrator.memory.get_session(session_id)
            if session is None:
                return {"status": "error", "error": "session_not_found"}

            # [SECURITY H2] Validate session ownership via bearer token
            if not orchestrator.memory.validate_session_token(session_id, session_token):
                logger.warning(f"[SECURITY H2] Unauthorized access attempt on session {session_id}")
                return {
                    "status": "error",
                    "code": 403,
                    "error": "Invalid or missing session_token. Access denied."
                }

            history = orchestrator.memory.get_session_history(session_id)
            return {
                "session_id": session.session_id,
                "problem_statement": session.problem_statement,
                "profile": session.profile.value,
                "steps_count": len(history),
                "steps": [step.model_dump(mode="json") for step in history],
            }

        @mcp.tool()
        def suggest_cognitive_pipeline(problem_statement: str) -> dict[str, object]:
            """
            Suggests a heuristic cognitive pipeline based on the problem statement.
            Useful for clients that want to preview the recommended strategy sequence.
            """
            category = PipelineSelector.detect_category(problem_statement)
            pipeline = PipelineSelector.select_pipeline(problem_statement)
            return {
                "category": category,
                "pipeline": [s.value for s in pipeline],
                "estimated_total_thoughts": len(pipeline),
            }

        @mcp.tool()
        def health_check() -> dict[str, object]:
            """
            Health check endpoint for monitoring and Docker/Kubernetes health probes.
            
            Returns system status, active sessions count, database connectivity,
            and rate limiting information.
            """
            start_time = datetime.now(timezone.utc)
            
            # Check database connectivity
            db_status = "healthy"
            try:
                # Quick DB ping
                _ = orchestrator.memory.get_session("__health_check__")
            except Exception as e:
                db_status = f"degraded: {str(e)}"
                logger.warning(f"Health check DB warning: {e}")
            
            # Get active sessions count
            try:
                active_sessions = len(orchestrator.memory.list_sessions())
            except Exception as e:
                active_sessions = -1
                logger.warning(f"Health check sessions warning: {e}")
            
            # Calculate response time
            response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Get rate limiter stats
            rate_limiter = get_rate_limiter()
            
            # Determine overall status
            if db_status == "healthy":
                overall_status = "healthy"
            else:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": start_time.isoformat(),
                "version": "2026.04.12",
                "services": {
                    "database": db_status,
                    "memory_manager": "healthy" if active_sessions >= 0 else "error",
                },
                "metrics": {
                    "active_sessions": active_sessions,
                    "response_time_ms": round(response_time_ms, 2),
                    "rate_limit_window": rate_limiter.config.window_seconds,
                    "rate_limit_max": rate_limiter.config.max_requests,
                },
            }

        @mcp.tool()
        def get_hitl_status(session_id: str) -> dict[str, object]:
            """
            [HITL] Check Human-in-the-Loop status for a session.
            
            Returns detailed HITL status including whether a hard STOP
            is active, clearance status, and authorization history.
            """
            if error := validate_session_id(session_id):
                return {"status": "error", "error": error}
            
            return orchestrator.hitl_enforcer.get_hitl_status(session_id)

    if "hitl" in enabled:
        @mcp.tool()
        def grant_human_clearance(
            session_id: str,
            session_token: str,
            authorized_by: str,
            authorization_note: str = ""
        ) -> dict[str, object]:
            """
            [HITL] Grant human clearance for a blocked HITL session.
            
            Required for HUMAN_IN_THE_LOOP profile sessions that have triggered
            a hard STOP at Phase 7. Execution remains blocked until this tool
            is called with valid authorization.
            
            SECURITY: Requires the session_token issued at session creation.
            """
            # Validate session
            if error := validate_session_id(session_id):
                return {"status": "error", "error": error}
            
            session = orchestrator.memory.get_session(session_id)
            if not session:
                return {"status": "error", "error": "session_not_found"}
            
            # Validate ownership
            if not orchestrator.memory.validate_session_token(session_id, session_token):
                return {
                    "status": "error",
                    "code": 403,
                    "error": "Invalid session_token. Authorization denied."
                }
            
            # Grant clearance via HITL enforcer
            result = orchestrator.hitl_enforcer.grant_clearance(
                session_id=session_id,
                authorized_by=authorized_by,
                authorization_note=authorization_note
            )
            
            return result


    logger.info("Session Tools registered successfully (filtered).")
