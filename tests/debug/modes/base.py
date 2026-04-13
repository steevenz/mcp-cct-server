from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Type, TypeVar, Optional

from pydantic import BaseModel, ValidationError

from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.analysis.scoring_engine import ScoringEngine
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.models.enums import ThinkingStrategy
from src.core.validators import validate_session_id
import uuid
import logging

T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)

class BaseCognitiveEngine(ABC):
    """
    The strict contract for all 25+ Cognitive Engines.
    Enforces architectural consistency across primitive and hybrid modes.
    """

    def __init__(self, memory_manager: MemoryManager, sequential_engine: SequentialEngine):
        self.memory = memory_manager
        self.sequential = sequential_engine
        self.scoring = ScoringEngine()

    @property
    @abstractmethod
    def strategy_type(self) -> ThinkingStrategy:
        """
        Defines the specific ThinkingStrategy this engine handles.
        Must return an enum value (e.g., ThinkingStrategy.SYSTEMIC).
        """
        pass

    @abstractmethod
    def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        The core execution block for the cognitive strategy.

        Args:
            session_id: The ID of the active CCT Session.
            input_payload: Engine-specific parameters (DTOs converted to Dict).

        Returns:
            Dict containing execution results and generated thought IDs.
        """
        pass

    def _generate_thought_id(self, prefix: str) -> str:
        """
        Generates a unique identifier for thought nodes.
        Format: {prefix}_{timestamp_ms}_{short_uuid}
        """
        timestamp = datetime.now().strftime('%H%M%S%f')[:-3]  # Include milliseconds
        short_uuid = uuid.uuid4().hex[:6]
        return f"{prefix}_{timestamp}_{short_uuid}"

    def _get_session_or_raise(self, session_id: str) -> CCTSessionState:
        """
        Retrieves a session or raises ValueError if not found.
        Centralizes session validation to reduce code duplication.
        """
        session = self.memory.get_session(session_id)
        if not session:
            raise ValueError(f"Active session '{session_id}' not found.")
        return session

    def _get_thought_or_raise(self, thought_id: str) -> EnhancedThought:
        """
        Retrieves a thought or raises ValueError if not found.
        Centralizes thought validation to reduce code duplication.
        """
        thought = self.memory.get_thought(thought_id)
        if not thought:
            raise ValueError(f"Thought '{thought_id}' not found.")
        return thought

    def _validate_session_id(self, session_id: str) -> None:
        """
        Validates session ID format using core validators.
        Raises ValueError if invalid.
        """
        if error := validate_session_id(session_id):
            raise ValueError(error)

    def _validate_payload(self, input_payload: Dict[str, Any], schema_class: Type[BaseModel]) -> BaseModel:
        """
        Validates input payload against a Pydantic schema.
        Centralizes validation logic to reduce code duplication in hybrid engines.
        
        Args:
            input_payload: Raw dictionary payload
            schema_class: Pydantic BaseModel class to validate against
            
        Returns:
            Validated schema instance
            
        Raises:
            ValueError: If validation fails
        """
        try:
            return schema_class(**input_payload)
        except ValidationError as e:
            engine_name = self.__class__.__name__
            raise ValueError(f"Invalid payload for {engine_name}: {e.errors()}")

    def _link_thought_to_parent(self, session_id: str, thought: EnhancedThought) -> None:
        """
        Links a thought to its parent by adding the child's ID to the parent's children_ids list.
        If the parent is not found, logs a warning instead of raising an exception.
        """
        if not thought.parent_id:
            return
            
        try:
            parent = self._get_thought_or_raise(thought.parent_id)
            if thought.id not in parent.children_ids:
                parent.children_ids.append(thought.id)
                try:
                    self.memory.update_thought(session_id, parent)
                except Exception as e:
                    logger.warning(
                        f"Failed to update parent {thought.parent_id}: {e}"
                    )
        except ValueError:
            # Parent not found - log warning but don't fail
            logger.warning(
                f"Parent thought {thought.parent_id} not found for linking thought {thought.id}"
            )

    def _score_and_save(
        self, 
        session_id: str, 
        thought: EnhancedThought, 
        history: list[EnhancedThought],
        model_id: str
    ) -> None:
        """
        Calculates cognitive metrics and persists the thought node.
        Includes token-optimized scoring and cost transparency.
        Now uses manual 'transaction' logic via MemoryManager.
        """
        # 1. Metacognitive Analysis
        thought.metrics = self.scoring.analyze_thought(thought, history, model_id=model_id)
        thought.summary = self.scoring.generate_summary(thought.content)

        # 2. Transactional Persistence
        try:
            # First, save the actual thought
            self.memory.save_thought(session_id, thought)
            
            # Second, update the parent's children list
            self._link_thought_to_parent(session_id, thought)
            
            # (In a full DB, we'd wrap these in a real BEGIN/COMMIT)
            logger.debug(f"Thought {thought.id} persisted successfully in session {session_id}")
            
        except Exception as e:
            logger.exception(f"Failed to persist thought {thought.id}: {e}")
            raise RuntimeError(f"Data integrity error: could not save thought node {thought.id}") from e