from pydantic import BaseModel, Field

class ActorCriticDialogInput(BaseModel):
    """Schema for triggering the automated Actor-Critic loop."""
    target_thought_id: str = Field(..., description="The ID of the thought to be stress-tested")
    critic_persona: str = Field(default="Security Expert", description="The persona lens for the critic (e.g., Performance Optimizer)")
