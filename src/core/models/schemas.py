from pydantic import BaseModel, Field
from typing import Optional
from .enums import ThinkingStrategy, ThoughtType, CCTProfile

class StartCCTSessionInput(BaseModel):
    """Schema for initializing a new CCT session."""
    problem_statement: str = Field(..., description="The main architectural problem to solve")
    thinking_profile: CCTProfile = Field(default=CCTProfile.BALANCED, description="The cognitive approach profile")
    estimated_total_thoughts: int = Field(default=5, ge=1, description="Initial estimation of thinking steps")

class CCTThinkStepInput(BaseModel):
    """Schema for a standard single thinking step."""
    thought_content: str = Field(..., description="The content of the thought or argument")
    thought_type: ThoughtType = Field(..., description="Classification of the thought (e.g., analysis, hypothesis)")
    strategy: ThinkingStrategy = Field(..., description="The strategy employed to generate this thought")
    
    # Sequential Trackers
    thought_number: int = Field(..., description="The step number you believe you are on")
    estimated_total_thoughts: int = Field(..., description="Total steps you believe are required")
    next_thought_needed: bool = Field(default=True, description="Set to False if convergence is reached")
    is_revision: bool = Field(default=False, description="Set to True if revising a flawed thought")
    revises_thought_id: Optional[str] = Field(None, description="Required if is_revision is True")
    
    # Branching Trackers
    branch_from_id: Optional[str] = Field(None, description="Target thought ID if branching into an alternative path")
    branch_id: Optional[str] = Field(None, description="Name identifier for the new branch")



