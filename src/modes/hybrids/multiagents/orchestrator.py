import logging
from typing import Dict, Any

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.modes.base import BaseCognitiveEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from .schemas import MultiAgentFusionInput

# New Services
from src.core.services.orchestration.autonomous import AutonomousService
from src.core.services.llm.client import ClientService as ThoughtGenerationService
from src.core.services.guidance.guidance import GuidanceService
from src.core.services.user.identity import UserIdentityService as IdentityService
from src.core.services.analysis.scoring import ScoringService

logger = logging.getLogger(__name__)

class MultiAgentFusionEngine(BaseCognitiveEngine):
    """
    Simulated Multi-Agent Council using the Fusion Orchestrator.
    Divergent generation followed by convergent fusion.
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        sequential: SequentialEngine,
        fusion: FusionOrchestrator,
        autonomous: AutonomousService,
        thought_service: ThoughtGenerationService,
        guidance: GuidanceService,
        identity: IdentityService,
        scoring: ScoringService
    ):
        super().__init__(memory, sequential, identity, scoring)
        self.fusion = fusion
        self.autonomous = autonomous
        self.thought_service = thought_service
        self.guidance = guidance

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return ThinkingStrategy.MULTI_AGENT_FUSION

    async def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a multi-agent dialogue and fusion orchestration.
        Uses the specialized FusionEngine for the convergent phase.
        """
        try:
            validated_input = MultiAgentFusionInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload for Multi-Agent Fusion: {e.errors()}")

        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated_input.target_thought_id)

        persona_nodes = []
        
        mode = self.autonomous.get_execution_mode(session.complexity)
        
        # 1. PHASE: Divergent Perspectives (Persona Insights)
        if mode == "autonomous":
            logger.info(f"[MULTI-AGENT] Executing autonomous persona generation for session {session_id}")
            for persona in validated_input.personas:
                thought_number = session.current_thought_number + 1
                seq_context = self.sequential.process_sequence_step(
                    session_id=session_id,
                    llm_thought_number=thought_number,
                    llm_estimated_total=session.estimated_total_thoughts,
                    next_thought_needed=True,
                    branch_from_id=target_thought.id,
                    branch_id=f"persona_{persona.lower().replace(' ', '_')}"
                )

                p_id = self._generate_thought_id("persona")
                
                # ACTUAL LLM CALL for persona insight
                prompt = (
                    f"CONTEXT: {target_thought.content}\n"
                    f"PERSONA: {persona}\n"
                    f"INSTRUCTION: Provide a deep technical analysis from your specific expertise."
                )
                persona_sys_prompt = f"You are a {persona} expert participating in a cognitive war room."
                content = await self.thought_service.generate_thought(
                    prompt=prompt,
                    system_prompt=self._get_identity_decorated_system_prompt(session_id, persona_sys_prompt)
                )

                p_thought = EnhancedThought(
                    id=p_id,
                    content=content,
                    thought_type=ThoughtType.ANALYSIS,
                    strategy=ThinkingStrategy.CRITICAL,
                    parent_id=target_thought.id,
                    sequential_context=seq_context,
                    tags=["multi_agent_fusion", "persona_insight", persona.lower(), "autonomous"]
                )
                self.memory.save_thought(session_id, p_thought)
                persona_nodes.append(p_thought)
                target_thought.children_ids.append(p_thought.id)
                session.current_thought_number += 1
        else:
            logger.info(f"[MULTI-AGENT] Providing guidance for manual personas in session {session_id}")
            # In Guided mode, we create ONE guidance thought instead of multiple mock ones
            thought_number = session.current_thought_number + 1
            seq_context = self.sequential.process_sequence_step(
                session_id=session_id,
                llm_thought_number=thought_number,
                llm_estimated_total=session.estimated_total_thoughts,
                next_thought_needed=True
            )
            
            p_id = self._generate_thought_id("guidance")
            guidance_msg = self.guidance.format_guidance_message(ThinkingStrategy.MULTI_AGENT_FUSION)
            guidance_msg += f"\nSUGGESTED PERSONAS: {', '.join(validated_input.personas)}"
            
            p_thought = EnhancedThought(
                id=p_id,
                content=guidance_msg,
                thought_type=ThoughtType.PROTOCOL,
                strategy=ThinkingStrategy.MULTI_AGENT_FUSION,
                parent_id=target_thought.id,
                sequential_context=seq_context,
                tags=["multi_agent_fusion", "guidance", "guided"]
            )
            self.memory.save_thought(session_id, p_thought)
            persona_nodes.append(p_thought) # Guidance node for manual persona generation in guided mode
            target_thought.children_ids.append(p_thought.id)
            session.current_thought_number += 1

        # Save updated target with all persona children
        self.memory.update_thought(session_id, target_thought)
        self.memory.update_session(session)

        # 2. PHASE: Convergent Synthesis (The Fusion)
        logger.debug(f"Handing off {len(persona_nodes)} perspectives to Fusion Engine.")
        
        synthesis_goal = f"Synthesize expert perspectives on: {target_thought.content[:100]}..."
        fusion_thought = self.fusion.fuse_thoughts(
            session_id=session_id,
            thought_ids=[n.id for n in persona_nodes],
            synthesis_goal=synthesis_goal,
            model_id=session.model_id,
            model_tier="efficiency" # [CHEAP/FAST] logic applied here
        )

        # Update session with the fusion step
        session.current_thought_number += 1
        self.memory.update_session(session)

        return {
            "status": "success",
            "orchestration_mode": "multi_agent_fusion",
            "persona_insights": [n.id for n in persona_nodes],
            "fusion_thought_id": fusion_thought.id,
            "next_step": fusion_thought.sequential_context.thought_number,
            "fusion_metrics": fusion_thought.metrics.model_dump() if fusion_thought.metrics else None
        }
