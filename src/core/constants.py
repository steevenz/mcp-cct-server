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
DEFAULT_DB_PATH: str = "database/cct_memory.db"
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
DEFAULT_MODEL_TIER: str = "efficiency"  # For fusion engine [CHEAP/FAST] logic
DEFAULT_CLARITY_SHORT_THRESHOLD: int = 100  # chars
DEFAULT_NOVELTY_SAMPLE_SIZE: int = 10
MAX_ANALYSIS_TOKEN_BUDGET: int = 4000

# =============================================================================
# Pipeline Routing Thresholds
# =============================================================================
PIVOT_THRESHOLD_CLARITY: float = 0.4  # Below this triggers unconventional pivot
PIVOT_THRESHOLD_COHERENCE: float = 0.3  # Below this triggers unconventional pivot

# =============================================================================
# Sequential Engine Constants
# =============================================================================
REVISION_EXPANSION_INCREMENT: int = 2  # How much to expand total when revision detected
BOUNDARY_EXTENSION_INCREMENT: int = 1  # How much to extend when boundary reached

# =============================================================================
# Context Pruner / Economy
# =============================================================================
DEFAULT_SLIDING_WINDOW_SIZE: int = 8  # Number of thoughts to keep in sliding window
DEFAULT_SUMMARY_DEPTH_THRESHOLD: int = 3  # Depth threshold for summarization

# =============================================================================
# Pattern Archiver
# =============================================================================
DEFAULT_DOCS_ROOT: str = "docs/context-tree/Thinking-Patterns"
MIN_PATTERN_USAGE_COUNT: int = 1

# =============================================================================
# Pricing (USD per 1M tokens)
# =============================================================================
DEFAULT_PRICING_PATH: str = "database/datasets"  # Directory containing per-model pricing files
FALLBACK_INPUT_PRICE_PER_1M: float = 3.0   # Default $3 per 1M input tokens
FALLBACK_OUTPUT_PRICE_PER_1M: float = 15.0  # Default $15 per 1M output tokens

# Supported AI Models for Pricing
SUPPORTED_PRICING_MODELS: set[str] = {
    # Anthropic
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet",
    "claude-3-opus-20240229",
    "claude-3-opus",
    "claude-3-haiku-20240307",
    "claude-3-haiku",
    "claude-4.5-haiku",
    "claude-4.6-sonnet",
    "claude-4.6-opus",
    "claude-5-sonnet",
    # Google
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "gemini-3.5-pro",
    "gemini-3.5-flash",
    "palm-2",
    # OpenAI
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo",
    "gpt-4.1",
    "gpt-5.2-pro",
    "gpt-5.4-pro",
    "gpt-6-preview",
    "o3",
    "o4-mini",
    # Others
    "grok-3",
    "deepseek-v3.2",
    "llama-4-maverick",
    "command-r-plus",
}

# =============================================================================
# Forex / Currency Conversion
# =============================================================================
FOREX_CACHE_TTL: int = 86400  # 24 hours in seconds
FOREX_DEFAULT_RATE: float = 17095.0  # USD to IDR fallback rate (April 2026 baseline)
FOREX_API_URL: str = "https://api.frankfurter.app/latest?from=USD&to=IDR"
