from __future__ import annotations
from typing import Any, Dict, Optional
import logging
from mcp.server.fastmcp import FastMCP

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.engines.orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)

# [SECURITY C1] Hard limits on free-text MCP inputs to block prompt injection
# and cognitive poisoning of the Thinking Pattern archive.
MAX_THOUGHT_CONTENT_LEN: int = 8_000   # characters
MAX_PARADIGM_LEN: int = 2_000
MAX_SESSION_ID_LEN: int = 64
MAX_THOUGHT_ID_LEN: int = 64


def _guard_string(value: str, field_name: str, max_len: int) -> Optional[str]:
    """
    Validates that a free-text input does not exceed the allowed character limit.
    Returns an error message string if invalid, or None if the input is safe.
    """
    if len(value) > max_len:
        msg = (
            f"[SECURITY C1] Field '{field_name}' exceeds maximum allowed length "
            f"({len(value)} > {max_len} chars). Request rejected."
        )
        logger.warning(msg)
        return msg
    return None


def register_cognitive_tools(mcp: FastMCP, orchestrator: CognitiveOrchestrator):
    """
    Registrasi semua tool kognitif ke server MCP.
    """

    @mcp.tool()
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
        """
        # [SECURITY C1] Validate all free-text inputs at the MCP boundary
        for field, value, limit in [
            ("session_id",       session_id,       MAX_SESSION_ID_LEN),
            ("thought_content",  thought_content,  MAX_THOUGHT_CONTENT_LEN),
        ]:
            err = _guard_string(value, field, limit)
            if err:
                return {"status": "error", "error": err}

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

    @mcp.tool()
    async def actor_critic_dialog(
        session_id: str,
        target_thought_id: str,
        critic_persona: str = "Security Expert"
    ) -> Dict[str, Any]:
        """
        [HYBRID] Automated Actor-Critic stress-testing loop.
        Triggers a debate between the core architect and a specialized critic lens.
        """
        payload = {"target_thought_id": target_thought_id, "critic_persona": critic_persona}
        return orchestrator.execute_strategy(session_id, ThinkingStrategy.ACTOR_CRITIC_LOOP, payload)

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

    logger.info("Cognitive Tools registered successfully.")
