"""
Security utilities for session management and token handling.
Provides cryptographic functions for bearer token generation and validation.
"""
from __future__ import annotations

import hashlib
import secrets
import hmac
import logging
import os
from pathlib import Path
from typing import Optional

from src.core.constants import SESSION_TOKEN_LENGTH

PRD_ID = "20260428-x-api-key-resolution"
logger = logging.getLogger("cct-security")


def generate_session_token(length: int = SESSION_TOKEN_LENGTH) -> str:
    """
    Generate cryptographically secure URL-safe session token.

    Uses secrets.token_urlsafe for CSPRNG quality randomness.
    Suitable for bearer tokens in [SECURITY H2] implementation.

    Args:
        length: Length of token in bytes (default: 32)

    Returns:
        URL-safe base64-encoded token string
    """
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """
    Hash token for secure storage comparison.
    Uses SHA-256 for one-way hashing.

    Args:
        token: Raw token string

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_token(provided: str, stored: str) -> bool:
    """
    Constant-time token comparison to prevent timing attacks.

    Uses hmac.compare_digest for timing-attack resistant comparison.

    Args:
        provided: Token provided by client
        stored: Token stored in database (can be raw or hashed)

    Returns:
        True if tokens match, False otherwise
    """
    # If stored token looks like a hash (64 hex chars), hash the provided token
    if len(stored) == 64 and all(c in '0123456789abcdef' for c in stored.lower()):
        provided_hash = hash_token(provided)
        return hmac.compare_digest(provided_hash, stored)

    # Direct comparison for raw tokens
    return hmac.compare_digest(provided, stored)


def generate_secure_id(prefix: str = "", length: int = 16) -> str:
    """
    Generate cryptographically secure random ID.

    Args:
        prefix: Optional prefix for the ID
        length: Length of random portion in bytes

    Returns:
        Secure random ID string
    """
    random_part = secrets.token_hex(length)
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def sanitize_session_id(session_id: str) -> Optional[str]:
    """
    Validate and sanitize session ID to prevent injection attacks.
    
    Uses strict regex pattern matching only allowing:
    - Alphanumeric (a-z, A-Z, 0-9)
    - Hyphens and underscores
    - Strict length limits (32-64 chars)
    
    Args:
        session_id: Raw session ID string
    
    Returns:
        Sanitized ID or None if invalid
    """
    if not session_id:
        return None
    
    import re
    # Strict pattern: only alphanumeric, hyphens, underscores, length 32-64
    pattern = r'^[a-zA-Z0-9\-_]{32,64}$'
    
    if not re.fullmatch(pattern, session_id):
        logger.warning(f"Invalid session ID format: {session_id[:16]}... (truncated)")
        return None
    # Additional length check for safety
    if len(session_id) < 32 or len(session_id) > 64:
        return None
    
    return session_id


class ApiKeyResolutionError(RuntimeError):
    """Raised when X-API-KEY cannot be resolved from expected sources (PRD: 20260428-x-api-key-resolution)."""


def _parse_env_file_value(env_file: Path, key: str) -> Optional[str]:
    """
    Parse a single key from dotenv-like file.

    Supports lines in form:
      KEY=value
      export KEY=value
    """
    if not env_file.exists():
        return None

    if not env_file.is_file():
        raise ApiKeyResolutionError(f"Configured env path is not a file: {env_file}")

    if not os.access(env_file, os.R_OK):
        raise ApiKeyResolutionError(f"Env file is not readable: {env_file}")

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        candidate = value.strip().strip('"').strip("'")
        return candidate or None

    return None


def resolve_bootstrap_api_key(
    project_root: Optional[Path] = None,
    source: str = "auto",
    fail_on_mismatch: bool = True,
) -> str:
    """
    Resolve bootstrap API key used by FastAPI auth dependency.

    Authentication mechanism in this codebase:
    - No algorithmic key generation.
    - No encryption/derivation routine.
    - API expects exact value from `CCT_BOOTSTRAP_API_KEY`.

    Resolution behavior:
    - source="auto": compare env and .env, fail on mismatch by default.
    - source="env": use process env only.
    - source="dotenv": use .env only.
    """
    normalized_source = source.strip().lower()
    if normalized_source not in {"auto", "env", "dotenv"}:
        raise ApiKeyResolutionError("Invalid source. Expected one of: auto, env, dotenv")

    env_key = os.getenv("CCT_BOOTSTRAP_API_KEY", "").strip() or None
    legacy_env_key = os.getenv("CCT_DASHBOARD_API_KEY", "").strip() or None
    if env_key is None:
        if legacy_env_key:
            logger.warning(
                "DEPRECATED_ENV_VAR: CCT_DASHBOARD_API_KEY is deprecated. Use CCT_BOOTSTRAP_API_KEY instead."
            )
        env_key = legacy_env_key
    root = project_root.resolve() if project_root else Path.cwd()
    dotenv_bootstrap_key = _parse_env_file_value(root / ".env", "CCT_BOOTSTRAP_API_KEY") or None
    dotenv_legacy_key = _parse_env_file_value(root / ".env", "CCT_DASHBOARD_API_KEY") or None
    dotenv_key = dotenv_bootstrap_key
    if dotenv_key is None:
        if dotenv_legacy_key:
            logger.warning(
                "DEPRECATED_ENV_VAR: CCT_DASHBOARD_API_KEY in .env is deprecated. Use CCT_BOOTSTRAP_API_KEY instead."
            )
        dotenv_key = dotenv_legacy_key

    if normalized_source == "env":
        if env_key:
            return env_key
        raise ApiKeyResolutionError("CCT_BOOTSTRAP_API_KEY is not set in process environment.")

    if normalized_source == "dotenv":
        if dotenv_key:
            return dotenv_key
        raise ApiKeyResolutionError(f"CCT_BOOTSTRAP_API_KEY is not set in {root / '.env'}.")

    # auto mode
    if env_key and dotenv_key and env_key != dotenv_key and fail_on_mismatch:
        raise ApiKeyResolutionError(
            "CCT_BOOTSTRAP_API_KEY mismatch between process environment and .env. "
            "Specify source='env' or source='dotenv' explicitly."
        )
    if env_key:
        return env_key
    if dotenv_key:
        return dotenv_key

    raise ApiKeyResolutionError(
        "CCT_BOOTSTRAP_API_KEY is missing. This project does not generate API keys "
        "algorithmically; set CCT_BOOTSTRAP_API_KEY in environment or .env."
    )


def resolve_dashboard_api_key(
    project_root: Optional[Path] = None,
    source: str = "auto",
    fail_on_mismatch: bool = True,
) -> str:
    """Backward-compatible alias to avoid breaking existing callers."""
    return resolve_bootstrap_api_key(
        project_root=project_root,
        source=source,
        fail_on_mismatch=fail_on_mismatch,
    )


def build_x_api_key_header(
    project_root: Optional[Path] = None,
    source: str = "auto",
    fail_on_mismatch: bool = True,
) -> dict[str, str]:
    """Build outbound header dict for endpoints protected by `X-API-KEY`."""
    return {
        "X-API-KEY": resolve_bootstrap_api_key(
            project_root=project_root,
            source=source,
            fail_on_mismatch=fail_on_mismatch,
        )
    }
