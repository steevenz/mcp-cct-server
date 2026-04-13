from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from .enums import ThinkingStrategy, ThoughtType, ConfidenceLevel, CCTProfile, SessionStatus
from .contexts import SequentialContext

def utc_now() -> datetime:
    """Helper to get current UTC datetime."""
    return datetime.now(timezone.utc)

class ThoughtMetrics(BaseModel):
    """Granular performance and cost metrics for a single cognitive step."""
    # Quality metrics
    clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    logical_coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    novelty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    
    # Token & Cost Metrics (Transparency Layer)
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    input_cost_usd: float = Field(default=0.0)
    output_cost_usd: float = Field(default=0.0)
    input_cost_idr: float = Field(default=0.0)
    output_cost_idr: float = Field(default=0.0)
    
    # Audit: snapshot of the live exchange rate used at calculation time
    currency_rate_idr: float = Field(
        default=0.0,
        description="USD/IDR exchange rate used for this calculation (from live API / cache)"
    )

class EnhancedThought(BaseModel):
    """Main thought entity structure within the system (Universal Currency)."""
    id: str = Field(description="Unique identifier for the thought")
    content: str = Field(description="The actual content of the thought")
    summary: Optional[str] = Field(None, description="Condensed version of the thought for long-context compression")
    thought_type: ThoughtType
    strategy: ThinkingStrategy
    
    # Hierarchy & Relations (Tree Thinking)
    parent_id: Optional[str] = Field(None, description="ID of the parent thought in a tree structure")
    children_ids: List[str] = Field(default_factory=list, description="IDs of child thoughts")
    builds_on: List[str] = Field(default_factory=list, description="IDs of thoughts this thought builds upon")
    contradicts: List[str] = Field(default_factory=list, description="IDs of thoughts this thought contradicts")
    
    # State & Metrics
    sequential_context: SequentialContext
    metrics: ThoughtMetrics = Field(default_factory=ThoughtMetrics)
    cognitive_biases: List[str] = Field(default_factory=list, description="Identified cognitive biases in this thought")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Detailed token tracking for this specific step")
    is_thinking_pattern: bool = Field(default=False, description="Whether this thought has been archived as a Golden Thinking Pattern")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    timestamp: datetime = Field(default_factory=utc_now)

class ThinkingSession(BaseModel):
    """Represents a complete thinking session history."""
    session_id: str
    created_at: datetime = Field(default_factory=utc_now)
    steps: List[EnhancedThought] = Field(default_factory=list)

class SessionMetrics(BaseModel):
    """Overall metrics for a thinking session analysis."""
    clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    bias_flags: List[str] = Field(default_factory=list)
    consistency_score: float = Field(default=0.0, ge=0.0, le=1.0)

class CCTSessionState(BaseModel):
    """Represents the operational state of an ongoing cognitive session."""
    session_id: str
    problem_statement: str
    profile: CCTProfile
    current_thought_number: int = Field(default=0)
    estimated_total_thoughts: int = Field(default=5)
    history_ids: List[str] = Field(default_factory=list)
    requires_human_decision: bool = Field(default=False)
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    suggested_pipeline: List[ThinkingStrategy] = Field(default_factory=list)
    knowledge_injection: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    
    # Multi-Scenario Context
    detected_categories: Dict[str, float] = Field(
        default_factory=dict, 
        description="Weighted scores for applicable domains (e.g., {'ARCH': 0.8, 'SEC': 0.4})"
    )
    primary_category: str = Field(default="GENERIC")
    
    # [SECURITY H2] Bearer token for session ownership verification.
    # Issued on creation, must be passed on all subsequent read operations.
    # Prevents horizontal privilege escalation via session_id guessing/spoofing.
    session_token: str = Field(
        default="",
        description="Cryptographic bearer token issued at session creation. Required for history access."
    )

    # Token Economy Config
    context_strategy: str = Field(default="summarized") # full, sliding, summarized, branch_only
    max_context_tokens: int = Field(default=4000)
    
    # Cognitive Performance Harness (Telemetry)
    model_id: str = Field(default="claude-3-5-sonnet-20240620")
    total_prompt_tokens: int = Field(default=0)
    total_completion_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    total_cost_idr: float = Field(default=0.0)
    consistency_score: float = Field(default=0.0)
    complexity: str = Field(default="unknown")
    
    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

class GoldenThinkingPattern(BaseModel):
    """Archived high-quality cognitive patterns (Permanent Thinking Patterns)."""
    id: str = Field(description="Unique identifier for the thinking pattern")
    thought_id: str = Field(description="Reference to the originating thought")
    session_id: str = Field(description="Reference to the originating session")
    original_problem: str = Field(description="Problem being solved when the pattern emerged")
    summary: str = Field(description="Executive summary of the cognitive pattern")
    content: str = Field(description="Complete cognitive detail")
    metrics: ThoughtMetrics = Field(default_factory=ThoughtMetrics)
    tags: List[str] = Field(default_factory=list)
    usage_count: int = Field(default=1, description="Number of times this pattern has been referenced or reused")
    timestamp: datetime = Field(default_factory=utc_now)

class AntiPattern(BaseModel):
    """Archived cognitive failures and corrective actions."""
    id: str = Field(description="Unique identifier for the anti-pattern")
    thought_id: str = Field(description="Reference to the originating thought")
    session_id: str = Field(description="Reference to the originating session")
    category: str = Field(description="Category of the failure (e.g., Logic, Evidence, Bias)")
    failed_strategy: ThinkingStrategy = Field(description="Strategy that failed")
    problem_context: str = Field(description="Brief context of the problem")
    failure_reason: str = Field(description="Detailed reason for the failure")
    corrective_action: str = Field(description="Mandatory instruction for future avoidance")
    timestamp: datetime = Field(default_factory=utc_now)
