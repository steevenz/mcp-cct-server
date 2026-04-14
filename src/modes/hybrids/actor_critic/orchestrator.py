import logging
from typing import Dict, Any

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought

# Base contract
from src.modes.base import BaseCognitiveEngine

# Local schema
from .schemas import ActorCriticDialogInput

# New Services
from typing import Any
from src.core.services.orchestration import OrchestrationService
from src.infrastructure.llm.client import LLMClient
from src.core.services.guidance import GuidanceService

logger = logging.getLogger(__name__)

class ActorCriticEngine(BaseCognitiveEngine):
    """
    Orchestrates the Actor-Critic cognitive loop.
    Automates a two-phase process: Criticism (Attacking a proposal) 
    and Synthesis (Resolving the flaws).
    """

    def __init__(
        self,
        memory_manager: Any,
        sequential_engine: Any,
        orchestration: OrchestrationService,
        llm: LLMClient,
        guidance: GuidanceService
    ):
        super().__init__(memory_manager, sequential_engine)
        self.orchestration = orchestration
        self.llm = llm
        self.guidance = guidance

    @property
    def strategy_type(self) -> ThinkingStrategy:
        """Binds this engine to the ACTOR_CRITIC_LOOP strategy."""
        return ThinkingStrategy.ACTOR_CRITIC_LOOP

    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the two-phase Actor-Critic refinement process.
        Converts the raw dictionary payload into a validated Pydantic schema first.
        """
        # 1. Validate payload using local schema
        try:
            validated_input = ActorCriticDialogInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload for Actor-Critic Engine: {e.errors()}")

        # 2. Fetch Session and Target Thought using base class helpers
        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated_input.target_thought_id)

        logger.info(f"Initiating Actor-Critic loop for target thought: {target_thought.id}")

        mode = self.orchestration.get_execution_mode(session.complexity)

        if mode == "autonomous":
            logger.info(f"[ACTOR-CRITIC] Executing autonomous loop for session {session_id}")
            
            # PHASE 1: THE CRITIC
            critic_simulated_step = session.current_thought_number + 1
            critic_seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=critic_simulated_step,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=True,
                branch_from_id=target_thought.id,
                branch_id="critic_branch"
            )
            
            critic_prompt = (
                f"AUDIT TARGET: {target_thought.content}\n"
                f"PERSONA: {validated_input.critic_persona}\n"
                f"INSTRUCTION: Identify flaws, vulnerabilities, or bottlenecks."
            )
            critic_content = await self.llm.generate_thought(
                prompt=critic_prompt,
                system_prompt=f"You are a {validated_input.critic_persona} expert. Critically attack the provided proposal."
            )
            
            critic_thought = EnhancedThought(
                id=self._generate_thought_id("critic"),
                content=critic_content,
                thought_type=ThoughtType.EVALUATION,
                strategy=ThinkingStrategy.CRITICAL,
                parent_id=target_thought.id,
                contradicts=[target_thought.id],
                sequential_context=critic_seq_context,
                tags=["actor_critic_loop", "critic_phase", "autonomous"]
            )
            self.memory.save_thought(session_id, critic_thought)
            session.current_thought_number += 1
            
            # PHASE 2: THE SYNTHESIS
            synth_simulated_step = session.current_thought_number + 1
            synthesis_seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=synth_simulated_step,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=False,
                is_revision=True,
                revises_id=target_thought.id
            )
            
            synth_prompt = (
                f"ORIGINAL: {target_thought.content}\n"
                f"CRITIQUE: {critic_content}\n"
                f"INSTRUCTION: Resolve the conflicts and formulate a production-ready solution."
            )
            synthesis_content = await self.llm.generate_thought(
                prompt=synth_prompt,
                system_prompt="You are a Systems Architect. Synthesize the proposal with its criticisms."
            )
            
            synthesis_thought = EnhancedThought(
                id=self._generate_thought_id("synth"),
                content=synthesis_content,
                thought_type=ThoughtType.SYNTHESIS,
                strategy=ThinkingStrategy.DIALECTICAL,
                parent_id=critic_thought.id,
                builds_on=[target_thought.id, critic_thought.id],
                sequential_context=synthesis_seq_context,
                tags=["actor_critic_loop", "synthesis_phase", "autonomous"]
            )
            self.memory.save_thought(session_id, synthesis_thought)
            session.current_thought_number += 1
            
        else:
            logger.info(f"[ACTOR-CRITIC] Providing guided loop for session {session_id}")
            
            # Create ONE guidance thought instead of multi-step automation
            simulated_step = session.current_thought_number + 1
            seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=simulated_step,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=True
            )
            
            guidance_msg = self.guidance.format_guidance_message(ThinkingStrategy.ACTOR_CRITIC_LOOP)
            guidance_msg += f"\nSTAKEHOLDER: {validated_input.critic_persona}"
            
            synthesis_thought = EnhancedThought(
                id=self._generate_thought_id("guidance"),
                content=guidance_msg,
                thought_type=ThoughtType.PROTOCOL,
                strategy=ThinkingStrategy.ACTOR_CRITIC_LOOP,
                parent_id=target_thought.id,
                sequential_context=seq_context,
                tags=["actor_critic_loop", "guidance", "guided"]
            )
            self.memory.save_thought(session_id, synthesis_thought)
            session.current_thought_number += 1

        # Update the original thought's children to maintain tree integrity
        target_thought.children_ids.append(synthesis_thought.id)
        self.memory.update_thought(session_id, target_thought)
        self.memory.update_session(session)

        logger.info(f"Actor-Critic loop handled. Final Thought ID: {synthesis_thought.id} (Mode: {mode})")

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
