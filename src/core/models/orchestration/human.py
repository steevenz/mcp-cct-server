"""
Human Orchestration Domain Models

Domain models for the Delegate-Review-Orchestration workflow.
"""
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class OrchestrationPhase(str, Enum):
    """Phase in the Delegate-Review-Own workflow."""
    DELEGATE = "delegate"
    REVIEW = "review"
    OWN = "own"


class ReviewStatus(str, Enum):
    """Status of human review."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


@dataclass
class OrchestrationSession:
    """A human orchestration session."""
    session_id: str
    task_description: str
    phase: OrchestrationPhase = OrchestrationPhase.DELEGATE
    review_status: ReviewStatus = ReviewStatus.PENDING
    delegate_output: Optional[Dict[str, Any]] = None
    review_feedback: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    final_decision: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "task_description": self.task_description,
            "phase": self.phase.value,
            "review_status": self.review_status.value,
            "delegate_output": self.delegate_output,
            "review_feedback": self.review_feedback,
            "review_timestamp": self.review_timestamp.isoformat() if self.review_timestamp else None,
            "final_decision": self.final_decision,
            "created_at": self.created_at.isoformat()
        }
