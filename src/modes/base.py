from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Type
import uuid
from datetime import datetime

from pydantic import BaseModel, ValidationError
from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import CCTSessionState, EnhancedThought
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.core.services.analysis.scoring import ScoringService
from src.core.services.user.identity import UserIdentityService as IdentityService
from src.core.validators import validate_session_id

SchemaT = TypeVar("SchemaT", bound=BaseModel)

class BaseCognitiveEngine(ABC):
    """
    The strict contract for all 25+ Cognitive Engines.
    Enforces architectural consistency across primitive and hybrid modes.
    """

    def __init__(self, memory_manager: MemoryManager, sequential_engine: SequentialEngine, identity_service: IdentityService, scoring_engine: ScoringService):
        self.memory = memory_manager
        self.sequential = sequential_engine
        self.identity = identity_service
        self.scoring = scoring_engine

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
        Format: {prefix}_{timestamp}_{short_uuid}
        """
        timestamp = datetime.now().strftime('%H%M%S')
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
        error = validate_session_id(session_id)
        if error:
            raise ValueError(error)

    def _validate_payload(self, payload: Dict[str, Any], schema: Type[SchemaT]) -> SchemaT:
        try:
            return schema(**payload)
        except (ValidationError, TypeError) as exc:
            raise ValueError(f"Invalid payload for {self.__class__.__name__}: {exc}") from exc

    def _link_thought_to_parent(self, session_id: str, thought: EnhancedThought) -> None:
        if not thought.parent_id:
            return
        parent = self.memory.get_thought(thought.parent_id)
        if not parent:
            return
        if thought.id not in parent.children_ids:
            parent.children_ids.append(thought.id)
            self.memory.update_thought(session_id, parent)

    def _score_and_save(
        self,
        session_id: str,
        thought: EnhancedThought,
        history: list[EnhancedThought],
        model_id: str,
    ) -> None:
        thought.metrics = self.scoring.analyze_thought(thought, history, model_id=model_id)
        thought.summary = self.scoring.generate_summary(thought.content)
        self.memory.save_thought(session_id, thought)
        self._link_thought_to_parent(session_id, thought)

    def _get_identity_decorated_system_prompt(self, session_id: str, base_system_prompt: str) -> str:
        """
        Decorates a base system prompt with the session's Identity Layer (Mindset & Soul).
        Implements the 'Cognitive Rail' pattern.
        """
        session = self._get_session_or_raise(session_id)
        if not session.identity_layer:
            # Fallback to defaults if session somehow missing identity
            logger.warning(f"[IDENTITY_RAIL] Session {session_id} missing identity_layer. Loading from IdentityService fallback.")
            identity = self.identity.load_identity()
        else:
            identity = session.identity_layer
            logger.debug(f"[IDENTITY_RAIL] Using session identity_layer for {session_id}")
            
        prefix = self.identity.format_system_prefix(identity)
        return f"{prefix}\n\n{base_system_prompt}"
