from __future__ import annotations

from src.core.models.analysis import TaskComplexity
from src.core.models.enums import ThinkingStrategy
from src.core.services.orchestration.policy import PolicyService

class PipelinePolicyManager(PolicyService):
    @classmethod
    def select_pipeline(cls, problem_statement: str, complexity: TaskComplexity | str) -> list[ThinkingStrategy]:
        complexity_value = complexity.value if isinstance(complexity, TaskComplexity) else str(complexity)
        return PolicyService.select_pipeline(cls(), problem_statement, complexity_value)


__all__ = ["PipelinePolicyManager"]
