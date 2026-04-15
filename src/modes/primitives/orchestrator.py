import logging
from typing import Dict, Any

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import EnhancedThought
from src.core.models.schemas import CCTThinkStepInput
from src.core.constants import DEFAULT_TP_THRESHOLD, MAX_ANALYSIS_TOKEN_BUDGET

from src.modes.base import BaseCognitiveEngine
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.core.services.analysis.scoring import ScoringService
from src.core.models.analysis import AnalysisConfig
from src.engines.memory.thinking_patterns import PatternArchiver

logger = logging.getLogger(__name__)

class DynamicPrimitiveEngine(BaseCognitiveEngine):
    """
    A dynamic factory engine capable of processing all primitive cognitive strategies.
    Eliminates code duplication while maintaining strict architectural contracts.
    Uses token-optimized scoring for efficient analysis.

    ## 4-Stage Primitive Processing Lifecycle

    This engine implements the atomic cognitive processing lifecycle defined in CCT v5.0 §2.A:

    **Stage 1: Contextual Injection**
    - Retrieves state from SequentialEngine to understand position in branching "Tree of Thought"
    - Ensures the primitive worker has context of previous thoughts and branching structure
    - Implemented via `sequential.process_sequence_step()` at lines 44-53

    **Stage 2: Hardened Validation**
    - Every thought is immediately audited by ScoringService
    - Receives quantitative scores for: Clarity, Coherence, Novelty, and Evidence
    - Token-optimized with 4000 token budget for analysis
    - Implemented via `scoring.analyze_thought()` at lines 71-75

    **Stage 3: Cognitive Evolution**
    - PatternArchiver automatically promotes elite thoughts (logical_coherence > 0.9)
    - Elite thoughts become Golden Thinking Patterns for future reuse
    - Implements Long-Term Potentiation (LTP) - patterns strengthen with use
    - Implemented via `archiver.process_thought()` at line 90

    **Stage 4: Early Convergence Detection**
    - Detects "Breakthrough" thoughts that meet victory conditions
    - Triggers early stop to save tokens when solution is found
    - Uses dynamic threshold (DEFAULT_TP_THRESHOLD) for elite thought detection
    - Implemented via early_convergence logic at lines 92-96
    """

    def __init__(self, memory_manager: MemoryManager, sequential_engine: SequentialEngine, identity_service: IdentityService, scoring_engine: ScoringService, strategy: ThinkingStrategy):
        super().__init__(memory_manager, sequential_engine, identity_service, scoring_engine)
        self._dynamic_strategy = strategy
        self.archiver = PatternArchiver(memory_manager)

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return self._dynamic_strategy

    async def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated_input = CCTThinkStepInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload for Primitive Engine: {e.errors()}")

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

        # 4. SCORING & SUMMARIZATION (Hardening) - Token Optimized
        history = self.memory.get_session_history(session_id)
        # Use optimized scoring with 4000 token budget for analysis
        thought.metrics = self.scoring.analyze_thought(thought, history, token_budget=MAX_ANALYSIS_TOKEN_BUDGET)
        thought.summary = self.scoring.generate_summary(thought.content)

        if validated_input.is_revision and validated_input.revises_thought_id:
            thought.contradicts.append(validated_input.revises_thought_id)
        elif thought.parent_id:
            thought.builds_on.append(thought.parent_id)

        self.memory.save_thought(session_id, thought)
        if thought.parent_id:
            parent = self.memory.get_thought(thought.parent_id)
            if parent:
                parent.children_ids.append(thought.id)
                self.memory.update_thought(session_id, parent)

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
            }
        }
