"""
LLM Domain Models for Cognitive Task Processing.

Contains domain entities, value objects, and enums related to LLM operations
following DDD principles. These models represent the core domain concepts
for language model interactions within the CCT cognitive system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReasoningDepth(Enum):
    """Reasoning depth levels for cognitive tasks."""
    FAST = "fast"        # Quick, low-cost responses
    BALANCED = "balanced"  # Standard reasoning capability
    DEEP = "deep"        # Complex, deep reasoning


@dataclass
class ModelSelection:
    """Result of model selection decision.
    
    Value object representing the outcome of the intelligent model selection
    strategy, containing provider, model, depth, and performance estimates.
    """
    provider: str
    model: str
    depth: ReasoningDepth
    estimated_cost_per_1k: float
    estimated_latency_ms: int
    selection_rationale: str


@dataclass
class CognitiveTaskContext:
    """Context for cognitive task model selection.
    
    Value object containing all necessary information to determine the appropriate
    model selection for a given cognitive task, including complexity, requirements,
    and constraints.
    """
    complexity: str  # "simple", "moderate", "complex", "sovereign"
    requires_reasoning: bool
    requires_code: bool
    token_estimate: int
    latency_preference: str  # "fast", "balanced", "quality"
    cost_budget: Optional[float] = None  # USD per request


@dataclass
class ReviewOutcome:
    """Structured outcome from adversarial review.
    
    Value object representing the result of an adversarial review operation,
    including the review content, source, caching information, and latency metrics.
    """
    content: str
    source: str  # 'external', 'primary', 'persona'
    cached: bool = False
    latency_ms: float = 0.0
