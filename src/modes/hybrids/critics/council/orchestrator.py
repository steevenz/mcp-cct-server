import logging
from typing import Dict, Any, List

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.modes.base import BaseCognitiveEngine
from .schemas import CouncilOfCriticsInput

# New Services
from typing import Any
from src.core.services.orchestration.autonomous import AutonomousService
from src.core.services.llm.client import ClientService as ThoughtGenerationService
from src.core.services.llm.critic import CriticService as AdversarialReviewService
from src.core.services.guidance.guidance import GuidanceService
from src.core.services.user.identity import UserIdentityService as IdentityService
from src.core.services.analysis.scoring import ScoringService

logger = logging.getLogger(__name__)

class CouncilOfCriticsEngine(BaseCognitiveEngine):
    """
    CouncilOfCriticsEngine: Advanced Multi-Agent Recursive Debate.
    
    Orchestrates a panel of specialized critics to evaluate a proposal,
    followed by a consolidated synthesis phase.
    
    Supports both autonomous (LLM-powered) and guided modes.
    """

    def __init__(
        self,
        memory: MemoryManager,
        sequential: SequentialEngine,
        autonomous: AutonomousService,
        thought_service: ThoughtGenerationService,
        guidance: GuidanceService,
        identity: IdentityService,
        scoring: ScoringService,
        review_service: AdversarialReviewService = None
    ):
        super().__init__(memory, sequential, identity, scoring)
        self.autonomous = autonomous
        self.thought_service = thought_service
        self.guidance = guidance
        self.review_service = review_service

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return ThinkingStrategy.COUNCIL_OF_CRITICS

    async def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a multi-agent critique and synthesis session.
        """
        # 1. Validate payload using local schema
        try:
            validated_input = CouncilOfCriticsInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload for Council of Critics Engine: {e.errors()}")
        
        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated_input.target_thought_id)

        logger.info(f"Council of Critics convened for thought: {target_thought.id}")

        mode = self.autonomous.get_execution_mode(session.complexity)
        criticism_ids = []
        persona_nodes = []
        
        # =====================================================================
        # PHASE 1: THE COUNCIL (Multi-Specialist Evaluation)
        # =====================================================================
        if mode == "autonomous":
            logger.info(f"[COUNCIL] Executing autonomous critique for session {session_id}")
            
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
                
                # ACTUAL LLM CALL for persona critique
                critic_prompt = (
                    f"AUDIT TARGET: {target_thought.content}\n"
                    f"PERSONA: {persona}\n"
                    f"INSTRUCTION: Provide a high-fidelity critique from your specialized perspective. "
                    f"Focus on domain-specific weaknesses, risks, and improvement opportunities."
                )
                critic_sys_prompt = f"You are a {persona} expert participating in a cognitive war room. Critically analyze the proposal."
                critic_content = await self.thought_service.generate_thought(
                    prompt=critic_prompt,
                    system_prompt=self._get_identity_decorated_system_prompt(session_id, critic_sys_prompt)
                )
                
                critic_thought = EnhancedThought(
                    id=self._generate_thought_id("council_critic"),
                    content=critic_content,
                    thought_type=ThoughtType.EVALUATION,
                    strategy=ThinkingStrategy.CRITICAL,
                    parent_id=target_thought.id,
                    contradicts=[target_thought.id],
                    sequential_context=seq_context,
                    tags=["council_of_critics", "evaluation", persona.lower().replace(" ", "-"), "autonomous"]
                )
                
                history = self.memory.get_session_history(session_id)
                self._score_and_save(session_id, critic_thought, history, model_id=session.model_id)
                criticism_ids.append(critic_thought.id)
                persona_nodes.append(critic_thought)
                target_thought.children_ids.append(critic_thought.id)
                session.current_thought_number += 1
        else:
            logger.info(f"[COUNCIL] Providing guidance for manual critique in session {session_id}")
            # In Guided mode, create ONE guidance thought with all personas
            step_num = session.current_thought_number + 1
            
            seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=step_num,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=True
            )
            
            guidance_msg = self.guidance.format_guidance_message(ThinkingStrategy.COUNCIL_OF_CRITICS)
            guidance_msg += f"\nSUGGESTED PERSONAS: {', '.join(validated_input.personas)}"
            
            guidance_thought = EnhancedThought(
                id=self._generate_thought_id("council_guidance"),
                content=guidance_msg,
                thought_type=ThoughtType.PROTOCOL,
                strategy=ThinkingStrategy.COUNCIL_OF_CRITICS,
                parent_id=target_thought.id,
                sequential_context=seq_context,
                tags=["council_of_critics", "guidance", "guided"]
            )
            
            self.memory.save_thought(session_id, guidance_thought)
            criticism_ids.append(guidance_thought.id)
            persona_nodes.append(guidance_thought)
            target_thought.children_ids.append(guidance_thought.id)
            session.current_thought_number += 1

        # Save updated target with all persona children
        self.memory.update_thought(session_id, target_thought)

        # =====================================================================
        # PHASE 2: CONVERGENT SYNTHESIS (Consensus)
        # =====================================================================
        synth_step = session.current_thought_number + 1
        
        if mode == "autonomous":
            # Synthesis revises the original target thought based on the WHOLE council
            synthesis_seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=synth_step,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=False,  # End of this specific hybrid loop
                is_revision=True,
                revises_id=target_thought.id
            )
            
            # ACTUAL LLM CALL for synthesis
            source_context = "\n\n".join([
                f"--- {p.id} ({p.strategy.value}) ---\n{p.content}" 
                for p in persona_nodes
            ])
            
            synthesis_prompt = (
                f"ORIGINAL PROPOSAL: {target_thought.content}\n\n"
                f"COUNCIL CRITIQUES:\n{source_context}\n\n"
                f"INSTRUCTION: Aggregate all specialized criticisms into a singular, hardened implementation path. "
                f"Resolve contradictions, synthesize insights, and provide a consensus recommendation."
            )
            synthesis_sys_prompt = "You are a Principal Systems Architect. Synthesize the council's critiques into a unified solution."
            synthesis_content = await self.thought_service.generate_thought(
                prompt=synthesis_prompt,
                system_prompt=self._get_identity_decorated_system_prompt(session_id, synthesis_sys_prompt)
            )
            
            synthesis_thought = EnhancedThought(
                id=self._generate_thought_id("council_synth"),
                content=synthesis_content,
                thought_type=ThoughtType.SYNTHESIS,
                strategy=ThinkingStrategy.INTEGRATIVE,
                parent_id=criticism_ids[-1],  # Link to the last critic in logic chain
                builds_on=[target_thought.id] + criticism_ids,
                sequential_context=synthesis_seq_context,
                tags=["council_of_critics", "synthesis", "consensus", "autonomous"]
            )
            
            history = self.memory.get_session_history(session_id)
            self._score_and_save(session_id, synthesis_thought, history, model_id=session.model_id)
        else:
            # Guided mode: provide synthesis guidance for manual convergence
            synthesis_seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=synth_step,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=False,
                is_revision=True,
                revises_id=target_thought.id
            )
            
            guidance_msg = self.guidance.format_guidance_message(ThinkingStrategy.INTEGRATIVE)
            guidance_msg += f"\nSYNTHESIZE INPUTS: {', '.join(criticism_ids)}"
            
            synthesis_thought = EnhancedThought(
                id=self._generate_thought_id("council_synth"),
                content=guidance_msg,
                thought_type=ThoughtType.PROTOCOL,
                strategy=ThinkingStrategy.INTEGRATIVE,
                parent_id=criticism_ids[-1],
                builds_on=[target_thought.id] + criticism_ids,
                sequential_context=synthesis_seq_context,
                tags=["council_of_critics", "synthesis", "guided"]
            )
            
            self.memory.save_thought(session_id, synthesis_thought)

        # Update session state
        session.current_thought_number += 1
        self.memory.update_session(session)
        
        # Link children to maintain tree visualization
        self._link_thought_to_parent(session_id, target_thought)

        logger.info(f"Council debate finalized. Consensus reached at: {synthesis_thought.id}")

        return {
            "status": "success",
            "orchestration_mode": mode,
            "session_id": session_id,
            "council_size": len(validated_input.personas),
            "critic_ids": criticism_ids,
            "consensus_id": synthesis_thought.id,
            "current_step": synthesis_thought.sequential_context.thought_number
        }

    def _get_identity_decorated_system_prompt(self, session_id: str, base_system_prompt: str) -> str:
        """Helper to decorate prompts with identity context."""
        session = self.memory.get_session(session_id)
        if not session or not session.identity_layer:
            identity = self.identity.load_identity()
        else:
            identity = session.identity_layer
            
        prefix = self.identity.format_system_prefix(identity)
        return f"{prefix}\n\n{base_system_prompt}"
