import logging
import uuid
from typing import Dict, Any, List

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.modes.base import BaseCognitiveEngine
from .schemas import CouncilOfCriticsInput

logger = logging.getLogger(__name__)

class CouncilOfCriticsEngine(BaseCognitiveEngine):
    """
    CouncilOfCriticsEngine: Advanced Multi-Agent Recursive Debate.
    
    Orchestrates a panel of specialized critics to evaluate a proposal,
    followed by a consolidated synthesis phase.
    """

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return ThinkingStrategy.COUNCIL_OF_CRITICS

    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a multi-agent critique and synthesis session.
        """
        self._validate_session_id(session_id)
        validated_input = self._validate_payload(input_payload, CouncilOfCriticsInput)
        
        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated_input.target_thought_id)

        logger.info(f"Council of Critics convened for thought: {target_thought.id}")

        criticism_ids = []
        
        # =====================================================================
        # PHASE 1: THE COUNCIL (Multi-Specialist Evaluation)
        # =====================================================================
        for persona in validated_input.personas:
            step_num = session.current_thought_number + 1
            
            # Each critic branches from the SAME target thought
            seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=step_num,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=True,
                branch_from_id=target_thought.id,
                branch_id=f"council_{persona.lower().replace(' ', '_')}"
            )
            
            critic_id = self._generate_thought_id("council_critic")
            critic_prompt = (
                f"[COUNCIL ACTION] Persona: {persona}\n"
                f"Evaluation Target: '{target_thought.content}'\n"
                f"Task: Provide a high-fidelity critique from your specialized perspective. "
                f"Focus on domain-specific weaknesses."
            )

            critic_thought = EnhancedThought(
                id=critic_id,
                content=critic_prompt,
                thought_type=ThoughtType.EVALUATION,
                strategy=ThinkingStrategy.CRITICAL,
                parent_id=target_thought.id,
                contradicts=[target_thought.id],
                sequential_context=seq_context,
                tags=["council_of_critics", "evaluation", persona.lower().replace(" ", "-")]
            )
            
            history = self.memory.get_session_history(session_id)
            self._score_and_save(session_id, critic_thought, history, model_id=session.model_id)
            criticism_ids.append(critic_id)

        # =====================================================================
        # PHASE 2: CONVERGENT SYNTHESIS (Consensus)
        # =====================================================================
        synth_step = session.current_thought_number + 1
        
        # Synthesis revises the original target thought based on the WHOLE council
        synthesis_seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=synth_step,
            llm_estimated_total=session.estimated_total_thoughts,
            next_thought_needed=False, # End of this specific hybrid loop
            is_revision=True,
            revises_id=target_thought.id
        )

        synthesis_id = self._generate_thought_id("council_synth")
        synthesis_prompt = (
            f"[COUNCIL ACTION] Multi-Agent Synthesis\n"
            f"Original Proposal: {target_thought.id}\n"
            f"Council Inputs: {', '.join(criticism_ids)}\n"
            f"Task: Aggregate all specialized criticisms into a singular, hardened implementation path."
        )

        synthesis_thought = EnhancedThought(
            id=synthesis_id,
            content=synthesis_prompt,
            thought_type=ThoughtType.SYNTHESIS,
            strategy=ThinkingStrategy.INTEGRATIVE,
            parent_id=criticism_ids[-1], # Link to the last critic in logic chain
            builds_on=[target_thought.id] + criticism_ids,
            sequential_context=synthesis_seq_context,
            tags=["council_of_critics", "synthesis", "consensus"]
        )

        history = self.memory.get_session_history(session_id)
        self._score_and_save(session_id, synthesis_thought, history, model_id=session.model_id)
        
        # Link children to maintain tree visualization
        self._link_thought_to_parent(session_id, target_thought)

        logger.info(f"Council debate finalized. Consensus reached at: {synthesis_id}")

        return {
            "status": "success",
            "session_id": session_id,
            "council_size": len(validated_input.personas),
            "critic_ids": criticism_ids,
            "consensus_id": synthesis_id,
            "current_step": synthesis_seq_context.thought_number
        }
