import logging
from typing import Dict, Any

from pydantic import ValidationError

# Core domain & enums
from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought

# Base contract
from src.modes.base import BaseCognitiveEngine

# Local schema
from .schemas import LateralPivotInput

logger = logging.getLogger(__name__)
class LateralEngine(BaseCognitiveEngine):
    """
    Engine for Lateral Thinking and Provocation.
    Injects an 'unconventional pivot' into the thinking process to escape local optima.
    """
    def __init__(self, memory_manager: Any, sequential_engine: Any, identity_service: Any, scoring_engine: Any):
        super().__init__(memory_manager, sequential_engine, identity_service, scoring_engine)

    @property
    def strategy_type(self) -> ThinkingStrategy:
        """Binds this engine to the UNCONVENTIONAL_PIVOT strategy."""
        return ThinkingStrategy.UNCONVENTIONAL_PIVOT

    async def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the lateral pivot by injecting a provocation thought into the sequence.
        """
        # 1. Validate payload using local schema
        try:
            validated_input = LateralPivotInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload for Lateral Engine: {e.errors()}")

        # 2. Fetch Session using base class helper
        session = self._get_session_or_raise(session_id)

        logger.info(f"Triggering Lateral Pivot in session {session_id}. Method: {validated_input.provocation_method}")

        # 3. Process Sequence Step
        simulated_step = session.current_thought_number + 1
        
        # We flag is_revision=True implicitly because pivoting means the old path reached a deadlock
        seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=simulated_step,
            llm_estimated_total=session.estimated_total_thoughts,
            next_thought_needed=True,
            is_revision=True, 
            branch_id=f"lateral_{validated_input.provocation_method.lower()}"
        )

        # 4. Construct the Lateral Provocation Prompt
        thought_id = self._generate_thought_id("lat")
        provocation_prompt = (
            f"[LATERAL PIVOT TRIGGERED] The current paradigm '{validated_input.current_paradigm}' "
            f"is causing a deadlock. Apply the '{validated_input.provocation_method}' technique. "
            f"Generate a completely unconventional, unorthodox architectural solution that violates "
            f"the original assumptions. Do not write code yet, just the conceptual paradigm shift."
        )

        lateral_thought = EnhancedThought(
            id=thought_id,
            content=provocation_prompt,
            thought_type=ThoughtType.HYPOTHESIS,
            strategy=self.strategy_type,
            sequential_context=seq_context,
            tags=["lateral_pivot", "provocation", validated_input.provocation_method]
        )

        # 5. Save to memory
        self.memory.save_thought(session_id, lateral_thought)
        
        logger.info(f"Lateral pivot node {lateral_thought.id} created successfully.")
        
        return {
            "status": "success",
            "orchestration_mode": self.strategy_type.value,
            "provocation_applied": validated_input.provocation_method,
            "generated_thought_id": lateral_thought.id,
            "current_step": seq_context.thought_number,
            "instruction": "LLM must now read the generated thought and respond with a lateral solution."
        }