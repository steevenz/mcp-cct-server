from pydantic import BaseModel, Field

class TemporalHorizonInput(BaseModel):
    """
    Payload required to trigger a long-term temporal projection.
    Isolated within the temporal vertical slice domain.
    """
    target_thought_id: str = Field(..., description="The ID of the architectural decision to project into the future")
    projection_scale: str = Field(default="5_years", description="The timeframe scale to project against (e.g., 6_months, 5_years, enterprise_scale)")