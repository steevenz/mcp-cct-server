"""
Bias detection domain models.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List


class BiasSeverity(Enum):
    """Severity levels for detected biases."""
    LOW = "low"          # Minor phrasing issues
    MEDIUM = "medium"    # Significant bias detected
    HIGH = "high"        # Critical bias, requires rewrite
    CRITICAL = "critical"  # Severe bias, block content


@dataclass
class BiasCheckResult:
    """Result of a bias check operation."""
    has_bias: bool
    flags: List[str]
    severity: BiasSeverity
    confidence: float  # 0.0 to 1.0
    suggestions: List[str]
    original_snippets: List[str]  # Text snippets that triggered flags


@dataclass
class BiasEnforcementResult:
    """Result of bias enforcement action."""
    action: str  # "allowed", "flagged", "rewritten", "blocked"
    original_text: str
    final_text: str
    bias_result: BiasCheckResult
    enforcement_message: str
