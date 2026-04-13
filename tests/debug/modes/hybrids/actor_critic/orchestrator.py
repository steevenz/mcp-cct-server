import logging
from typing import Dict, Any

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought

# Base contract
from src.modes.base import BaseCognitiveEngine

# Local schema
from .schemas import ActorCriticDialogInput

logger = logging.getLogger(__name__)

class ActorCriticEngine(BaseCognitiveEngine):
    """
    Orchestrates the Actor-Critic cognitive loop.
    Automates a two-phase process: Criticism (Attacking a proposal) 
    and Synthesis (Resolving the flaws).
    """

    @property
    def strategy_type(self) -> ThinkingStrategy:
        """Binds this engine to the ACTOR_CRITIC_LOOP strategy."""
        return ThinkingStrategy.ACTOR_CRITIC_LOOP

    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the two-phase Actor-Critic refinement process.
        Converts the raw dictionary payload into a validated Pydantic schema first.
        """
        # 1. Pre-validate session ID
        self._validate_session_id(session_id)

        # 2. Validate payload using base class helper
        validated_input = self._validate_payload(input_payload, ActorCriticDialogInput)

        # 3. Fetch Session and Target Thought using base class helpers
        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated_input.target_thought_id)

        logger.info(f"Initiating Actor-Critic loop for target thought: {target_thought.id}")

        # =====================================================================
        # PHASE 1: THE CRITIC (Evaluation)
        # =====================================================================
        # Simulate LLM step increment for the automated critic node
        critic_simulated_step = session.current_thought_number + 1
        
        critic_seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=critic_simulated_step,
            llm_estimated_total=session.estimated_total_thoughts,
            next_thought_needed=True,
            branch_from_id=target_thought.id,
            branch_id="critic_branch"
        )
        
        critic_thought_id = self._generate_thought_id("critic")
        critic_prompt = (
            f"[INTERNAL AUTOMATION] As a {validated_input.critic_persona}, critically evaluate this proposal: "
            f"'{target_thought.content}'. Identify architectural flaws, security vulnerabilities, "
            f"or scalability bottlenecks. Do not solve them yet, only attack the weaknesses."
        )

        critic_thought = EnhancedThought(
            id=critic_thought_id,
            content=critic_prompt,
            thought_type=ThoughtType.EVALUATION,
            strategy=ThinkingStrategy.CRITICAL,
            parent_id=target_thought.id,
            contradicts=[target_thought.id],
            sequential_context=critic_seq_context,
            tags=["actor_critic_loop", "critic_phase", "vulnerability_scan"]
        )
        
        history = self.memory.get_session_history(session_id)
        self._score_and_save(session_id, critic_thought, history, model_id=session.model_id)

        # =====================================================================
        # PHASE 2: THE SYNTHESIS (Resolution)
        # =====================================================================
        # We flag is_revision=True to dynamically expand the thought limit
        synth_simulated_step = session.current_thought_number + 1
        
        synthesis_seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=synth_simulated_step,
            llm_estimated_total=session.estimated_total_thoughts,
            next_thought_needed=False,
            is_revision=True,
            revises_id=target_thought.id
        )

        synthesis_thought_id = self._generate_thought_id("synth")
        synthesis_prompt = (
            f"[INTERNAL AUTOMATION] Synthesize the original proposal ({target_thought.id}) with the identified "
            f"criticisms ({critic_thought.id}). Resolve the conflicts to formulate a "
            f"robust, production-ready implementation."
        )

        synthesis_thought = EnhancedThought(
            id=synthesis_thought_id,
            content=synthesis_prompt,
            thought_type=ThoughtType.SYNTHESIS,
            strategy=ThinkingStrategy.DIALECTICAL,
            parent_id=critic_thought.id,
            builds_on=[target_thought.id, critic_thought.id],
            sequential_context=synthesis_seq_context,
            tags=["actor_critic_loop", "synthesis_phase", "resolution"]
        )

        history = self.memory.get_session_history(session_id)
        self._score_and_save(session_id, synthesis_thought, history, model_id=session.model_id)

        logger.info(f"Actor-Critic loop completed. Synthesis ID: {synthesis_thought.id}")

        return {
            "status": "success",
            "orchestration_mode": self.strategy_type.value,
            "target_thought_id": target_thought.id,
            "critic_phase": {
                "generated_id": critic_thought.id,
                "strategy": critic_thought.strategy.value
            },
            "synthesis_phase": {
                "generated_id": synthesis_thought.id,
                "strategy": synthesis_thought.strategy.value,
                "is_revision": synthesis_seq_context.is_revision
            },
            "current_step": synthesis_seq_context.thought_number
        }
