import logging
from typing import Dict, Any

from pydantic import ValidationError

# Core domain & enums
from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought

# Base contract
from src.modes.base import BaseCognitiveEngine

# Local schema
from .schemas import TemporalHorizonInput

logger = logging.getLogger(__name__)

class LongTermHorizonEngine(BaseCognitiveEngine):
    """
    Engine for temporal reasoning and future-proofing.
    Forces the AI to evaluate a proposed architecture across three timelines:
    NOW (Immediate execution), NEXT (Scaling phase), and LATER (Long-term maintenance/debt).
    """

    @property
    def strategy_type(self) -> ThinkingStrategy:
        """Binds this engine to the LONG_TERM_HORIZON strategy."""
        return ThinkingStrategy.LONG_TERM_HORIZON

    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the temporal projection by creating a structured framework thought.
        """
        # 1. Pre-validate session ID
        self._validate_session_id(session_id)

        # 2. Validate payload using base class helper
        validated_input = self._validate_payload(input_payload, TemporalHorizonInput)

        # 3. Fetch Session and Target using base class helpers
        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated_input.target_thought_id)

        logger.info(f"Triggering Temporal Projection in session {session_id} for scale: {validated_input.projection_scale}")

        # 3. Process Sequence Step
        simulated_step = session.current_thought_number + 1
        
        # We branch off the target thought to analyze its future
        seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=simulated_step,
            llm_estimated_total=session.estimated_total_thoughts,
            next_thought_needed=True,
            branch_from_id=target_thought.id,
            branch_id="temporal_projection"
        )

        # 4. Construct the Temporal Prompt (Adapted from original temporal_frame logic)
        thought_id = self._generate_thought_id("tmp")
        temporal_prompt = (
            f"[TEMPORAL HORIZON TRIGGERED: {validated_input.projection_scale}]\n"
            f"Analyze the proposal ({target_thought.id}): '{target_thought.content}'.\n"
            f"Project this architecture strictly across these three temporal frames:\n"
            f"- NOW: Evaluate immediate implementation viability.\n"
            f"- NEXT: Define the next concrete step and a stop condition.\n"
            f"- LATER: Define how this scales, what breaks first, and potential technical debt."
        )

        temporal_thought = EnhancedThought(
            id=thought_id,
            content=temporal_prompt,
            thought_type=ThoughtType.EVALUATION,
            strategy=self.strategy_type,
            parent_id=target_thought.id,
            sequential_context=seq_context,
            tags=["temporal_analysis", "future_proofing", validated_input.projection_scale]
        )

        # 5. SCORING, SUMMARIZATION & PERSISTENCE (Unified Pipeline)
        history = self.memory.get_session_history(session_id)
        self._score_and_save(session_id, temporal_thought, history, model_id=session.model_id)

        logger.info(f"Temporal projection node {temporal_thought.id} created successfully.")
        
        return {
            "status": "success",
            "orchestration_mode": self.strategy_type.value,
            "projection_scale": validated_input.projection_scale,
            "generated_thought_id": temporal_thought.id,
            "current_step": seq_context.thought_number,
            "instruction": "LLM must now evaluate the target thought using the NOW, NEXT, LATER framework."
        }