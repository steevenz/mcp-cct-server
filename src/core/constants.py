"""
System-wide constants and configuration defaults.
Centralizes all hardcoded values for maintainability and DDD compliance.
"""
from __future__ import annotations

# =============================================================================
# Session Limits
# =============================================================================
MAX_THOUGHTS_PER_SESSION: int = 200
MAX_SESSION_ID_LENGTH: int = 64
MAX_THOUGHT_ID_LENGTH: int = 64

# =============================================================================
# Content Limits
# =============================================================================
MAX_THOUGHT_CONTENT_LENGTH: int = 8000
MAX_PARADIGM_LENGTH: int = 2000
MAX_PROBLEM_STATEMENT_LENGTH: int = 2000

# =============================================================================
# Token Economy
# =============================================================================
DEFAULT_MAX_CONTEXT_TOKENS: int = 4000
DEFAULT_CONTEXT_STRATEGY: str = "summarized"  # Options: full, sliding, summarized, branch_only
CONTEXT_STRATEGIES: set[str] = {"full", "sliding", "summarized", "branch_only"}

# =============================================================================
# Model Defaults
# =============================================================================
DEFAULT_MODEL: str = "claude-3-5-sonnet-20240620"
DEFAULT_ESTIMATED_THOUGHTS: int = 5

# =============================================================================
# Security
# =============================================================================
SESSION_TOKEN_LENGTH: int = 32  # bytes for secrets.token_urlsafe()

# =============================================================================
# Database
# =============================================================================
DEFAULT_DB_PATH: str = "cct_memory.db"
DB_TIMEOUT_SECONDS: float = 5.0

# =============================================================================
# Server Defaults
# =============================================================================
DEFAULT_SERVER_NAME: str = "cct-mcp-server"
DEFAULT_TRANSPORT: str = "stdio"  # Options: stdio, http
DEFAULT_HOST: str = "0.0.0.0"
DEFAULT_PORT: int = 8000
DEFAULT_MAX_SESSIONS: int = 128

TRANSPORT_MODES: set[str] = {"stdio", "http"}

# =============================================================================
# Analysis & Scoring
# =============================================================================
DEFAULT_TP_THRESHOLD: float = 0.9  # Golden Thinking Pattern threshold
DEFAULT_CLARITY_SHORT_THRESHOLD: int = 100  # chars
DEFAULT_NOVELTY_SAMPLE_SIZE: int = 10
MAX_ANALYSIS_TOKEN_BUDGET: int = 4000

# =============================================================================
# Pattern Archiver
# =============================================================================
DEFAULT_DOCS_ROOT: str = "docs/context-tree/Thinking-Patterns"
MIN_PATTERN_USAGE_COUNT: int = 1

# =============================================================================
# Pricing (USD per 1K tokens)
# =============================================================================
DEFAULT_PRICING_PATH: str = "datasets/pricing.json"
