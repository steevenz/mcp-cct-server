"""
Common validation utilities for input sanitization and validation.
Provides consistent validation logic across the codebase.
"""
from __future__ import annotations

import re
from typing import Optional

from src.core.constants import (
    MAX_SESSION_ID_LENGTH,
    MAX_THOUGHT_ID_LENGTH,
    MAX_THOUGHT_CONTENT_LENGTH,
    MAX_PROBLEM_STATEMENT_LENGTH,
    MAX_PARADIGM_LENGTH,
    TRANSPORT_MODES,
    CONTEXT_STRATEGIES,
)

# Pattern for valid IDs (alphanumeric, underscore, hyphen)
_VALID_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
# Pattern for safe strings (no control characters)
_SAFE_STRING_PATTERN = re.compile(r'^[\x20-\x7E\s]*$')


def validate_session_id(session_id: str) -> Optional[str]:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not session_id:
        return "Session ID cannot be empty"
    
    if len(session_id) > MAX_SESSION_ID_LENGTH:
        return f"Session ID too long (max {MAX_SESSION_ID_LENGTH} characters)"
    
    if not _VALID_ID_PATTERN.match(session_id):
        return "Session ID contains invalid characters (allowed: a-z, A-Z, 0-9, _, -)"
    
    return None


def validate_thought_id(thought_id: str) -> Optional[str]:
    """
    Validate thought ID format.
    
    Args:
        thought_id: Thought ID string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not thought_id:
        return "Thought ID cannot be empty"
    
    if len(thought_id) > MAX_THOUGHT_ID_LENGTH:
        return f"Thought ID too long (max {MAX_THOUGHT_ID_LENGTH} characters)"
    
    if not _VALID_ID_PATTERN.match(thought_id):
        return "Thought ID contains invalid characters (allowed: a-z, A-Z, 0-9, _, -)"
    
    return None


def validate_thought_content(content: str) -> Optional[str]:
    """
    Validate thought content.
    
    Args:
        content: Thought content string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not content or not content.strip():
        return "Thought content cannot be empty"
    
    if len(content) > MAX_THOUGHT_CONTENT_LENGTH:
        return f"Content too long (max {MAX_THOUGHT_CONTENT_LENGTH} characters)"
    
    if not _SAFE_STRING_PATTERN.match(content):
        return "Content contains invalid control characters"
    
    return None


def validate_problem_statement(problem: str) -> Optional[str]:
    """
    Validate problem statement.
    
    Args:
        problem: Problem statement string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not problem or not problem.strip():
        return "Problem statement cannot be empty"
    
    if len(problem) > MAX_PROBLEM_STATEMENT_LENGTH:
        return f"Problem statement too long (max {MAX_PROBLEM_STATEMENT_LENGTH} characters)"
    
    return None


def validate_paradigm(paradigm: str) -> Optional[str]:
    """
    Validate paradigm string (e.g., for lateral thinking).
    
    Args:
        paradigm: Paradigm string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not paradigm or not paradigm.strip():
        return "Paradigm cannot be empty"
    
    if len(paradigm) > MAX_PARADIGM_LENGTH:
        return f"Paradigm too long (max {MAX_PARADIGM_LENGTH} characters)"
    
    return None


def validate_transport_mode(transport: str) -> Optional[str]:
    """
    Validate transport mode.
    
    Args:
        transport: Transport mode string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if transport not in TRANSPORT_MODES:
        return f"Invalid transport mode '{transport}' (allowed: {', '.join(sorted(TRANSPORT_MODES))})"
    
    return None


def validate_context_strategy(strategy: str) -> Optional[str]:
    """
    Validate context strategy.
    
    Args:
        strategy: Context strategy string to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if strategy not in CONTEXT_STRATEGIES:
        return f"Invalid context strategy '{strategy}' (allowed: {', '.join(sorted(CONTEXT_STRATEGIES))})"
    
    return None


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string by removing control characters and truncating.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in value if char.isprintable() or char in '\n\r\t')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def is_valid_thought_number(number: int, max_thoughts: int) -> bool:
    """
    Check if thought number is within valid range.
    
    Args:
        number: Thought number to check
        max_thoughts: Maximum allowed thoughts
        
    Returns:
        True if valid, False otherwise
    """
    return 1 <= number <= max_thoughts
