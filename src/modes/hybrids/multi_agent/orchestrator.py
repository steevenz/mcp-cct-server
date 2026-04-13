import logging
from typing import Dict, Any

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.modes.base import BaseCognitiveEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from .schemas import MultiAgentFusionInput

logger = logging.getLogger(__name__)

class MultiAgentFusionEngine(BaseCognitiveEngine):
    """
    Orchestrates the Multi-Agent cognitive fusion process.
    Simulates a collaborative 'war room' where multiple expert personas 
    evaluate a base thought and their insights are fused into a master conclusion.
    """

    def __init__(self, memory_manager: Any, sequential_engine: Any, fusion_orchestrator: FusionOrchestrator):
        super().__init__(memory_manager, sequential_engine)
        self.fusion = fusion_orchestrator

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return ThinkingStrategy.MULTI_AGENT_FUSION

    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # 1. PHASE: Divergent Perspectives (Persona Insights)
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
            # Logic still simulates persona perspective, but now it's destined for Fusion
            content = f"[MULTI-AGENT FUSION] Expert Insight ({persona}): Analyze '{target_thought.content}' from your specific domain expertise."

            p_thought = EnhancedThought(
                id=p_id,
                content=content,
                thought_type=ThoughtType.ANALYSIS,
                strategy=ThinkingStrategy.CRITICAL,
                parent_id=target_thought.id,
                sequential_context=seq_context,
                tags=["multi_agent_fusion", "persona_insight", persona.lower()]
            )
            self.memory.save_thought(session_id, p_thought)
            persona_nodes.append(p_thought)
            # Link to parent
            target_thought.children_ids.append(p_thought.id)

            # Update session thought number for next iteration
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
