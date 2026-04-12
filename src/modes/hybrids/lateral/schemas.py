from pydantic import BaseModel, Field

class LateralPivotInput(BaseModel):
    """
    Payload required to trigger a lateral thinking pivot.
    Isolated within the lateral vertical slice domain.
    """
    current_paradigm: str = Field(..., description="The standard assumption or current architecture causing the roadblock")
    provocation_method: str = Field(default="REVERSE_ASSUMPTION", description="The provocation technique applied (e.g., EXTREME_EXAGGERATION, INVERSION)")