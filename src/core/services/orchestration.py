from typing import Tuple
from src.core.config import Settings
from src.core.services.complexity import TaskComplexity

class OrchestrationService:
    """
    Decides between Autonomous vs Guided execution for hybrid strategies.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_execution_mode(self, complexity: TaskComplexity) -> str:
        """
        Determines the mode based on settings and task complexity.
        Returns: 'autonomous' or 'guided'
        """
        # If no LLM configured, always guided
        if not self._has_llm_configured():
            return "guided"
        
        # Heuristic: Simple tasks are always guided to save context/tokens.
        # Sovereign tasks are always autonomous if possible for deep reasoning.
        if complexity == TaskComplexity.PRIMITIVE:
            return "guided"
            
        return "autonomous"

    def _has_llm_configured(self) -> bool:
        """Checks if any valid LLM provider is configured in settings."""
        if self.settings.gemini_api_key:
            return True
        if self.settings.openai_api_key:
            return True
        if self.settings.anthropic_api_key:
            return True
        if self.settings.ollama_base_url and self.settings.llm_provider == "ollama":
            return True
        return False
