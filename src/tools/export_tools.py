from __future__ import annotations
import logging
from mcp.server.fastmcp import FastMCP

from src.analysis.scoring_engine import IncrementalSessionAnalyzer
from src.analysis.quality import clarity_score
from src.analysis.metrics import cosine_similarity
from src.analysis.bias import detect_bias_flags
from src.core.models.domain import SessionMetrics

from src.engines.orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)

def register_export_tools(mcp: FastMCP, orchestrator: CognitiveOrchestrator) -> None:
    """Registers session export and analysis tools."""

    @mcp.tool()
    def export_thinking_session(session_id: str, session_token: str = "") -> dict[str, object]:
        """
        Retrieves all thoughts for a session in a serializable format.

        SECURITY: Requires the session_token issued at session creation.
        """
        # [SECURITY H2] Validate session ownership via bearer token
        if not orchestrator.memory.validate_session_token(session_id, session_token):
            logger.warning(f"[SECURITY H2] Unauthorized export attempt on session {session_id}")
            return {
                "status": "error",
                "code": 403,
                "error": "Invalid or missing session_token. Access denied."
            }

        history = orchestrator.memory.get_session_history(session_id)
        if not history:
            return {"error": "session_not_found_or_empty"}

        return {"steps": [h.model_dump(mode="json") for h in history]}

    @mcp.tool()
    def analyze_session(session_id: str, session_token: str = "") -> dict[str, object]:
        """
        Analyzes a thinking session for quality, consistency, and cognitive biases.
        Provides a holistic metric score for the entire cognitive process.

        SECURITY: Requires the session_token issued at session creation.
        """
        # [SECURITY H2] Validate session ownership via bearer token
        if not orchestrator.memory.validate_session_token(session_id, session_token):
            logger.warning(f"[SECURITY H2] Unauthorized analysis attempt on session {session_id}")
            return {
                "status": "error",
                "code": 403,
                "error": "Invalid or missing session_token. Access denied."
            }

        session = orchestrator.memory.get_session(session_id)
        if session is None:
            return {"error": "session_not_found"}

        history = orchestrator.memory.get_session_history(session_id)
        if not history:
            metrics = SessionMetrics(clarity_score=0.0, bias_flags=[], consistency_score=0.0)
            return {"session_id": session_id, "metrics": metrics.model_dump(mode="json")}

        # Use incremental analyzer for token-efficient session analysis
        analyzer = IncrementalSessionAnalyzer()
        for thought in history:
            analyzer.add_thought(thought.content)

        final_metrics = analyzer.get_final_metrics()

        metrics = SessionMetrics(
            clarity_score=round(final_metrics["clarity_score"], 4),
            bias_flags=final_metrics["bias_flags"],
            consistency_score=round(final_metrics["consistency_score"], 4),
        )

        return {
            "session_id": session_id, 
            "problem_statement": session.problem_statement,
            "metrics": metrics.model_dump(mode="json")
        }
