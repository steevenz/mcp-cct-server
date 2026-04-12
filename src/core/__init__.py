"""
Core domain module - aggregate root for CCT system.
Exports all core domain components for unified access.
"""
from __future__ import annotations

# Configuration
from src.core.config import Settings, load_settings

# Constants
from src.core.constants import (
    MAX_THOUGHTS_PER_SESSION,
    MAX_SESSION_ID_LENGTH,
    MAX_THOUGHT_ID_LENGTH,
    MAX_THOUGHT_CONTENT_LENGTH,
    DEFAULT_MAX_CONTEXT_TOKENS,
    DEFAULT_CONTEXT_STRATEGY,
    DEFAULT_MODEL,
    DEFAULT_DB_PATH,
    DEFAULT_SERVER_NAME,
    DEFAULT_TRANSPORT,
    DEFAULT_HOST,
    DEFAULT_PORT,
)

# Security
from src.core.security import (
    generate_session_token,
    hash_token,
    verify_token,
    generate_secure_id,
    sanitize_session_id,
)

# Validators
from src.core.validators import (
    validate_session_id,
    validate_thought_id,
    validate_thought_content,
    validate_problem_statement,
    validate_transport_mode,
    validate_context_strategy,
    sanitize_string,
)

# Localization
from src.core.localization import (
    Language,
    get_message,
    get_language_from_code,
    DEFAULT_LANGUAGE,
)

# Models (re-export for convenience)
from src.core.models import (
    ThinkingStrategy,
    ThoughtType,
    ConfidenceLevel,
    CCTProfile,
    EnhancedThought,
    CCTSessionState,
    SessionMetrics,
    ThoughtMetrics,
    GoldenThinkingPattern,
    AntiPattern,
    SequentialContext,
    StartCCTSessionInput,
    CCTThinkStepInput,
    utc_now,
)

__all__ = [
    # Config
    "Settings",
    "load_settings",
    # Constants
    "MAX_THOUGHTS_PER_SESSION",
    "MAX_SESSION_ID_LENGTH",
    "MAX_THOUGHT_ID_LENGTH",
    "MAX_THOUGHT_CONTENT_LENGTH",
    "DEFAULT_MAX_CONTEXT_TOKENS",
    "DEFAULT_CONTEXT_STRATEGY",
    "DEFAULT_MODEL",
    "DEFAULT_DB_PATH",
    "DEFAULT_SERVER_NAME",
    "DEFAULT_TRANSPORT",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    # Security
    "generate_session_token",
    "hash_token",
    "verify_token",
    "generate_secure_id",
    "sanitize_session_id",
    # Validators
    "validate_session_id",
    "validate_thought_id",
    "validate_thought_content",
    "validate_problem_statement",
    "validate_transport_mode",
    "validate_context_strategy",
    "sanitize_string",
    # Localization
    "Language",
    "get_message",
    "get_language_from_code",
    "DEFAULT_LANGUAGE",
    # Models
    "ThinkingStrategy",
    "ThoughtType",
    "ConfidenceLevel",
    "CCTProfile",
    "EnhancedThought",
    "CCTSessionState",
    "SessionMetrics",
    "ThoughtMetrics",
    "GoldenThinkingPattern",
    "AntiPattern",
    "SequentialContext",
    "StartCCTSessionInput",
    "CCTThinkStepInput",
    "utc_now",
]
