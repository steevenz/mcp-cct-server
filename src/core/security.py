"""
Security utilities for session management and token handling.
Provides cryptographic functions for bearer token generation and validation.
"""
from __future__ import annotations

import hashlib
import secrets
import hmac
from typing import Optional

from src.core.constants import SESSION_TOKEN_LENGTH


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
    
    Args:
        session_id: Raw session ID string
        
    Returns:
        Sanitized ID or None if invalid
    """
    if not session_id:
        return None
    
    # Remove any path traversal attempts
    sanitized = session_id.replace("..", "").replace("/", "").replace("\\", "")
    
    # Limit length
    max_len = 128  # Generous limit for session IDs
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
    
    # Ensure still has content
    if not sanitized or sanitized.isspace():
        return None
        
    return sanitized
