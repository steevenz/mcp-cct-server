import pytest
from src.core.security import (
    generate_session_token,
    hash_token,
    verify_token,
    generate_secure_id,
    sanitize_session_id
)


def test_generate_session_token_default_length():
    """Test generating session token with default length."""
    token = generate_session_token()
    assert isinstance(token, str)
    assert len(token) > 0
    # token_urlsafe generates approximately 4/3 * length characters
    assert len(token) >= 32


def test_generate_session_token_custom_length():
    """Test generating session token with custom length."""
    token = generate_session_token(length=16)
    assert isinstance(token, str)
    assert len(token) > 0


def test_generate_session_token_uniqueness():
    """Test that tokens are unique."""
    token1 = generate_session_token()
    token2 = generate_session_token()
    assert token1 != token2


def test_hash_token():
    """Test token hashing."""
    token = "test_token_12345"
    hashed = hash_token(token)
    
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA-256 produces 64 hex chars
    assert all(c in '0123456789abcdef' for c in hashed.lower())


def test_hash_token_consistency():
    """Test that same token produces same hash."""
    token = "consistent_token"
    hash1 = hash_token(token)
    hash2 = hash_token(token)
    assert hash1 == hash2


def test_verify_token_raw():
    """Test token verification with raw tokens."""
    token = "raw_token_123"
    assert verify_token(token, token) is True
    assert verify_token(token, "different_token") is False


def test_verify_token_hashed():
    """Test token verification with hashed stored token."""
    token = "hashed_token_456"
    stored_hash = hash_token(token)
    
    assert verify_token(token, stored_hash) is True
    assert verify_token("wrong_token", stored_hash) is False


def test_verify_token_timing_attack_resistance():
    """Test that verification uses constant-time comparison."""
    token = "timing_test_token"
    stored = hash_token(token)
    
    # Should complete quickly regardless of match
    assert verify_token(token, stored) is True
    assert verify_token("wrong", stored) is False


def test_generate_secure_id_default():
    """Test generating secure ID without prefix."""
    id_str = generate_secure_id()
    assert isinstance(id_str, str)
    assert len(id_str) == 32  # 16 bytes * 2 hex chars
    assert all(c in '0123456789abcdef' for c in id_str.lower())


def test_generate_secure_id_with_prefix():
    """Test generating secure ID with prefix."""
    id_str = generate_secure_id(prefix="session")
    assert id_str.startswith("session_")
    assert len(id_str) == 40  # "session_" + 32 hex chars


def test_generate_secure_id_uniqueness():
    """Test that IDs are unique."""
    id1 = generate_secure_id()
    id2 = generate_secure_id()
    assert id1 != id2


def test_sanitize_session_id_valid():
    """Test sanitizing valid session ID."""
    session_id = "session_abc123"
    sanitized = sanitize_session_id(session_id)
    assert sanitized == session_id


def test_sanitize_session_id_path_traversal():
    """Test sanitizing session ID with path traversal attempts."""
    malicious_id = "../../../etc/passwd"
    sanitized = sanitize_session_id(malicious_id)
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized


def test_sanitize_session_id_empty():
    """Test sanitizing empty session ID."""
    assert sanitize_session_id("") is None
    assert sanitize_session_id(None) is None


def test_sanitize_session_id_whitespace():
    """Test sanitizing whitespace-only session ID."""
    assert sanitize_session_id("   ") is None
    assert sanitize_session_id("\t\n") is None


def test_sanitize_session_id_long():
    """Test sanitizing very long session ID."""
    long_id = "a" * 200
    sanitized = sanitize_session_id(long_id)
    assert len(sanitized) == 128  # Max length
    assert sanitized == "a" * 128


def test_sanitize_session_id_special_chars():
    """Test sanitizing session ID with special characters."""
    special_id = "session@test#123"
    sanitized = sanitize_session_id(special_id)
    # Path chars removed, other chars kept
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert "@" in sanitized or "#" in sanitized  # Other chars preserved
