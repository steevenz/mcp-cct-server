from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class SequentialContext(BaseModel):
    """
    State tracker for Sequential Thinking patterns.
    Validates and tracks the progression of steps, revisions, and branching.
    """
    thought_number: int = Field(default=1, description="Current step sequence number")
    estimated_total_thoughts: int = Field(default=5, description="Estimated total steps required")
    next_thought_needed: bool = Field(default=True, description="Indicates if the LLM requires more steps")
    
    # Revision Tracking
    is_revision: bool = Field(default=False, description="Indicates if this step is a revision of a previous one")
    revises_thought_id: Optional[str] = Field(None, description="ID of the thought being revised")
    
    # Branching Tracking
    branch_from_id: Optional[str] = Field(None, description="Target thought ID if branching into an alternative path")
    branch_id: Optional[str] = Field(None, description="Name identifier for the new branch")
