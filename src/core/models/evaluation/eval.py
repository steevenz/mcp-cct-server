"""
Eval-First Domain Models

Domain models for the Eval-First workflow enforcing "No Code Without Criteria".
"""
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field


class EvalStatus(str, Enum):
    """Status of evaluation criteria definition."""
    NOT_DEFINED = "not_defined"
    PARTIAL = "partial"
    COMPLETE = "complete"
    VALIDATED = "validated"


@dataclass
class EvalCriteria:
    """Evaluation criteria for a task."""
    capability_evals: List[str] = field(default_factory=list)
    regression_evals: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    baseline_snapshot: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Check if criteria are complete."""
        return (
            len(self.capability_evals) > 0 and
            len(self.regression_evals) > 0 and
            len(self.success_metrics) > 0
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "capability_evals": self.capability_evals,
            "regression_evals": self.regression_evals,
            "success_metrics": self.success_metrics,
            "baseline_snapshot": self.baseline_snapshot,
            "is_complete": self.is_complete()
        }
