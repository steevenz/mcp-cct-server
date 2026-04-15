from pydantic import BaseModel, Field
from typing import List

class MultiAgentFusionInput(BaseModel):
    """Schema for triggering the Multi-Agent cognitive fusion."""
    target_thought_id: str = Field(..., description="The ID of the base thought to be expanded by multiple personas")
    personas: List[str] = Field(
        default=["Architect", "Security Analyst", "Product Manager"],
        description="The group of specialized personas to simulate for the fusion process"
    )
