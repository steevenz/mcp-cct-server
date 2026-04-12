from __future__ import annotations
import logging
from mcp.server.fastmcp import FastMCP

from src.engines.orchestrator import CognitiveOrchestrator
from src.utils.pipelines import PipelineSelector

logger = logging.getLogger(__name__)

def register_session_tools(mcp: FastMCP, orchestrator: CognitiveOrchestrator) -> None:
    """Registers basic session management tools."""

    @mcp.tool()
    def start_cct_session(problem_statement: str, profile: str = "balanced") -> dict[str, object]:
        """
        Initializes a new CCT session.
        This MUST be the first tool called in any cognitive workflow.
        """
        return orchestrator.start_session(problem_statement, profile)

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
