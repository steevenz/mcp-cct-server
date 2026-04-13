from pydantic import BaseModel, Field
from typing import List

class CouncilOfCriticsInput(BaseModel):
    """
    Input schema for the Council of Critics hybrid engine.
    """
    target_thought_id: str = Field(..., description="The ID of the thought node to be critiqued by the council.")
    personas: List[str] = Field(
        default=["Security Expert", "Performance Engineer", "Principal Architect"],
        description="List of specialized personas that will participate in the council."
    )
