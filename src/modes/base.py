from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import CCTSessionState, EnhancedThought
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine

class BaseCognitiveEngine(ABC):
    """
    The strict contract for all 25+ Cognitive Engines.
    Enforces architectural consistency across primitive and hybrid modes.
    """

    def __init__(self, memory_manager: MemoryManager, sequential_engine: SequentialEngine):
        self.memory = memory_manager
        self.sequential = sequential_engine

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