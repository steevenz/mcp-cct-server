import logging
from typing import Dict, Any

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import EnhancedThought
from src.core.models.schemas import CCTThinkStepInput
from src.core.constants import DEFAULT_TP_THRESHOLD, MAX_ANALYSIS_TOKEN_BUDGET
from src.core.validators import validate_session_id, validate_thought_content

from src.modes.base import BaseCognitiveEngine
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.analysis.scoring_engine import ScoringEngine
from src.engines.memory.thinking_patterns import PatternArchiver

logger = logging.getLogger(__name__)

class DynamicPrimitiveEngine(BaseCognitiveEngine):
    """
    A dynamic factory engine capable of processing all primitive cognitive strategies.
    Eliminates code duplication while maintaining strict architectural contracts.
    Uses token-optimized scoring for efficient analysis.
    """

    def __init__(self, memory_manager: MemoryManager, sequential_engine: SequentialEngine, strategy: ThinkingStrategy):
        super().__init__(memory_manager, sequential_engine)
        self._dynamic_strategy = strategy
        self.archiver = PatternArchiver(memory_manager)
        # Initialize token-optimized scoring engine
        self.scoring = ScoringEngine()

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return self._dynamic_strategy

    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        # Pre-validation using core validators
        if error := validate_session_id(session_id):
            raise ValueError(error)

        try:
            validated_input = CCTThinkStepInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload for Primitive Engine: {e.errors()}")

        # Validate thought content
        if error := validate_thought_content(validated_input.thought_content):
            raise ValueError(error)

        session = self._get_session_or_raise(session_id)
        logger.info(f"Processing primitive step in session {session_id} using strategy: {self.strategy_type.value}")

        seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=validated_input.thought_number,
            llm_estimated_total=validated_input.estimated_total_thoughts,
            next_thought_needed=validated_input.next_thought_needed,
            is_revision=validated_input.is_revision,
            revises_id=validated_input.revises_thought_id,
            branch_from_id=validated_input.branch_from_id,
            branch_id=validated_input.branch_id
        )

        determined_parent_id = validated_input.branch_from_id
        if not determined_parent_id and session.history_ids:
            determined_parent_id = session.history_ids[-1]

        prefix = self._dynamic_strategy.value[:3]
        thought_id = self._generate_thought_id(prefix)
        thought = EnhancedThought(
            id=thought_id,
            content=validated_input.thought_content,
            thought_type=validated_input.thought_type,
            strategy=self.strategy_type,
            parent_id=determined_parent_id,
            sequential_context=seq_context,
            tags=["primitive_step", self.strategy_type.value]
        )

        # 4. SCORING, SUMMARIZATION & PERSISTENCE (Unified Pipeline)
        history = self.memory.get_session_history(session_id)
        
        if validated_input.is_revision and validated_input.revises_thought_id:
            thought.contradicts.append(validated_input.revises_thought_id)
        elif thought.parent_id:
            thought.builds_on.append(thought.parent_id)

        self._score_and_save(session_id, thought, history, model_id=session.model_id)

        # 5. THINKING PATTERN ARCHIVING (Auto-Pilot)
        pattern = self.archiver.process_thought(session, thought)
        
        # 6. DYNAMIC THRESHOLDING (Early Convergence Detection)
        early_convergence = False
        if pattern and thought.metrics.logical_coherence > DEFAULT_TP_THRESHOLD:
            early_convergence = True
            logger.info("🚩 Dynamic Threshold Triggered: Elite thought detected. Problem potentially solved.")

        return {
            "status": "success",
            "orchestration_mode": self.strategy_type.value,
            "generated_thought_id": thought.id,
            "is_thinking_pattern": pattern is not None,
            "early_convergence_suggested": early_convergence,
            "current_step": seq_context.thought_number,
            "estimated_total": seq_context.estimated_total_thoughts,
            "metrics": {
                "clarity": thought.metrics.clarity_score,
                "coherence": thought.metrics.logical_coherence,
                "novelty": thought.metrics.novelty_score,
                "evidence": thought.metrics.evidence_strength,
                "cost_usd": {
                    "input": thought.metrics.input_cost_usd,
                    "output": thought.metrics.output_cost_usd,
                    "step_total": thought.metrics.input_cost_usd + thought.metrics.output_cost_usd
                },
                "cost_idr": {
                    "input": thought.metrics.input_cost_idr,
                    "output": thought.metrics.output_cost_idr,
                    "step_total": thought.metrics.input_cost_idr + thought.metrics.output_cost_idr
                }
            }
        }
