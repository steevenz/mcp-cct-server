from __future__ import annotations
from typing import Any, Dict, Optional
import logging
from mcp.server.fastmcp import FastMCP

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.constants import (
    MAX_THOUGHT_CONTENT_LENGTH,
    MAX_PARADIGM_LENGTH,
    MAX_SESSION_ID_LENGTH,
    MAX_THOUGHT_ID_LENGTH,
)
from src.core.validators import validate_session_id, validate_thought_content
from src.core.rate_limiter import rate_limited
from src.engines.orchestrator import CognitiveOrchestrator
from src.core.config import load_settings

logger = logging.getLogger(__name__)

# Re-export constants for backward compatibility
MAX_THOUGHT_CONTENT_LEN = MAX_THOUGHT_CONTENT_LENGTH
MAX_PARADIGM_LEN = MAX_PARADIGM_LENGTH
MAX_SESSION_ID_LEN = MAX_SESSION_ID_LENGTH
MAX_THOUGHT_ID_LEN = MAX_THOUGHT_ID_LENGTH


def _guard_string(value: str, field_name: str, max_len: int) -> Optional[str]:
    """
    [DEPRECATED] Use core.validators functions instead.
    Kept for backward compatibility.
    """
    if len(value) > max_len:
        msg = (
            f"[SECURITY C1] Field '{field_name}' exceeds maximum allowed length "
            f"({len(value)} > {max_len} chars). Request rejected."
        )
        logger.warning(msg)
        return msg
    return None


def register_cognitive_tools(mcp: FastMCP, orchestrator: CognitiveOrchestrator, settings: Any | None = None):
    """
    Registrasi semua tool kognitif ke server MCP berdasarkan konfigurasi grup.
    """
    if settings is None:
        enabled = {"primitive", "hybrid", "hitl"}
    else:
        enabled = settings.enabled_tool_groups

    if "primitive" in enabled:
        @mcp.tool()
        @rate_limited(max_requests=120, window_seconds=60)  # 2 requests per second average
        async def cct_think_step(
            session_id: str,
            thought_content: str,
            strategy: str,
            thought_type: str = "analysis",
            thought_number: int = 1,
            estimated_total_thoughts: int = 5,
            next_thought_needed: bool = True,
            is_revision: bool = False,
            revises_thought_id: Optional[str] = None,
            branch_from_id: Optional[str] = None,
            branch_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            [PRIMITIVE] Unified tool for individual thought steps.
            Supports 22+ strategies (linear, analytical, systemic, lateral, first_principles, etc).
            Ensures strict tree-based tracking and sequential integrity.
            
            Rate Limit: 120 requests per 60 seconds per session.
            """
            # [SECURITY C1] Validate all free-text inputs at the MCP boundary using core validators
            if error := validate_session_id(session_id):
                return {"status": "error", "error": error}
            
            if error := validate_thought_content(thought_content):
                return {"status": "error", "error": error}

            try:
                strat_enum = ThinkingStrategy(strategy.lower())
            except ValueError:
                return {"error": f"Strategy '{strategy}' is not supported. Use primitives like 'linear', 'systemic', or 'dialectical'."}

            payload = {
                "thought_content": thought_content,
                "thought_type": ThoughtType(thought_type),
                "strategy": strat_enum,
                "thought_number": thought_number,
                "estimated_total_thoughts": estimated_total_thoughts,
                "next_thought_needed": next_thought_needed,
                "is_revision": is_revision,
                "revises_thought_id": revises_thought_id,
                "branch_from_id": branch_from_id,
                "branch_id": branch_id,
            }

            return orchestrator.execute_strategy(session_id, strat_enum, payload)

    if "hybrid" in enabled:
        @mcp.tool()
        @rate_limited(max_requests=30, window_seconds=60)  # Expensive operation, stricter limit
        async def actor_critic_dialog(
            session_id: str,
            target_thought_id: str,
            critic_persona: str = "Security Expert"
        ) -> Dict[str, Any]:
            """
            [HYBRID] Automated Actor-Critic stress-testing loop.
            Triggers a debate between the core architect and a specialized critic lens.
            
            Rate Limit: 30 requests per 60 seconds per session (computationally expensive).
            """
            payload = {"target_thought_id": target_thought_id, "critic_persona": critic_persona}
            return orchestrator.execute_strategy(session_id, ThinkingStrategy.ACTOR_CRITIC_LOOP, payload)

        @mcp.tool()
        async def council_of_critics_debate(
            session_id: str,
            target_thought_id: str,
            specialized_personas: list[str] = ["Security Expert", "Performance Engineer", "Principal Architect"]
        ) -> Dict[str, Any]:
            """
            [HYBRID] Multi-Agent Council of Critics Debate.
            Spawns multiple specialized critics to evaluate a proposal, followed by a unified synthesis.
            """
            payload = {"target_thought_id": target_thought_id, "personas": specialized_personas}
            return orchestrator.execute_strategy(session_id, ThinkingStrategy.COUNCIL_OF_CRITICS, payload)

        @mcp.tool()
        async def lateral_pivot_brainstorm(
            session_id: str,
            current_paradigm: str,
            provocation_method: str = "REVERSE_ASSUMPTION"
        ) -> Dict[str, Any]:
            """
            [HYBRID] Unconventional Pivot Brainstorming.
            Forces high-level paradigm shifts and lateral provocations to break deadlocks.
            """
            payload = {"current_paradigm": current_paradigm, "provocation_method": provocation_method}
            return orchestrator.execute_strategy(session_id, ThinkingStrategy.UNCONVENTIONAL_PIVOT, payload)

        @mcp.tool()
        async def temporal_horizon_projection(
            session_id: str,
            target_thought_id: str,
            projection_scale: str = "LONG_TERM"
        ) -> Dict[str, Any]:
            """
            [HYBRID] Temporal Projection and Future-Proofing.
            Forces the AI to evaluate an architecture across NOW, NEXT, and LATER timeframes.
            """
            payload = {"target_thought_id": target_thought_id, "projection_scale": projection_scale}
            return orchestrator.execute_strategy(session_id, ThinkingStrategy.LONG_TERM_HORIZON, payload)

    if "core" in enabled:
        @mcp.tool()
        async def cct_log_failure(
            session_id: str,
            thought_id: str,
            category: str,
            failure_reason: str,
            corrective_action: str
        ) -> Dict[str, Any]:
            """
            [SELF-IMPROVEMENT] Record a terminal cognitive failure or anti-pattern.
            Blacklists a pattern in global memory to prevent recurrence in future missions.
            """
            return orchestrator.log_failure(
                session_id, 
                thought_id, 
                category, 
                failure_reason, 
                corrective_action
            )

    logger.info("Cognitive Tools registered successfully (filtered).")
