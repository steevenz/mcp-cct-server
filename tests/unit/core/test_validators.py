import pytest
from src.core.validators import (
    validate_session_id,
    validate_thought_id,
    validate_thought_content,
    validate_problem_statement,
    validate_paradigm,
    validate_transport_mode,
    validate_context_strategy,
    sanitize_string,
    is_valid_thought_number
)


def test_validate_session_id_valid():
    """Test validating valid session ID."""
    assert validate_session_id("session_abc123") is None
    assert validate_session_id("SESSION-123") is None
    assert validate_session_id("test_id-456") is None


def test_validate_session_id_empty():
    """Test validating empty session ID."""
    assert validate_session_id("") == "Session ID cannot be empty"
    assert validate_session_id(None) == "Session ID cannot be empty"


def test_validate_session_id_too_long():
    """Test validating session ID that's too long."""
    from src.core.constants import MAX_SESSION_ID_LENGTH
    long_id = "a" * (MAX_SESSION_ID_LENGTH + 1)
    error = validate_session_id(long_id)
    assert "too long" in error
    assert str(MAX_SESSION_ID_LENGTH) in error


def test_validate_session_id_invalid_chars():
    """Test validating session ID with invalid characters."""
    error = validate_session_id("session@123")
    assert "invalid characters" in error.lower()
    error = validate_session_id("session/123")
    assert "invalid characters" in error.lower()
    error = validate_session_id("session.123")
    assert "invalid characters" in error.lower()


def test_validate_thought_id_valid():
    """Test validating valid thought ID."""
    assert validate_thought_id("thought_abc123") is None
    assert validate_thought_id("THOUGHT-123") is None


def test_validate_thought_id_empty():
    """Test validating empty thought ID."""
    assert validate_thought_id("") == "Thought ID cannot be empty"
    assert validate_thought_id(None) == "Thought ID cannot be empty"


def test_validate_thought_id_too_long():
    """Test validating thought ID that's too long."""
    from src.core.constants import MAX_THOUGHT_ID_LENGTH
    long_id = "t" * (MAX_THOUGHT_ID_LENGTH + 1)
    error = validate_thought_id(long_id)
    assert "too long" in error
    assert str(MAX_THOUGHT_ID_LENGTH) in error


def test_validate_thought_id_invalid_chars():
    """Test validating thought ID with invalid characters."""
    error = validate_thought_id("thought@123")
    assert "invalid characters" in error.lower()


def test_validate_thought_content_valid():
    """Test validating valid thought content."""
    assert validate_thought_content("This is a valid thought") is None
    assert validate_thought_content("Valid content with numbers 123") is None


def test_validate_thought_content_empty():
    """Test validating empty thought content."""
    assert validate_thought_content("") == "Thought content cannot be empty"
    assert validate_thought_content("   ") == "Thought content cannot be empty"
    assert validate_thought_content(None) == "Thought content cannot be empty"


def test_validate_thought_content_too_long():
    """Test validating thought content that's too long."""
    from src.core.constants import MAX_THOUGHT_CONTENT_LENGTH
    long_content = "a" * (MAX_THOUGHT_CONTENT_LENGTH + 1)
    error = validate_thought_content(long_content)
    assert "too long" in error
    assert str(MAX_THOUGHT_CONTENT_LENGTH) in error


def test_validate_thought_content_control_chars():
    """Test validating thought content with control characters."""
    content_with_null = "Valid\x00content"
    error = validate_thought_content(content_with_null)
    assert "invalid control characters" in error


def test_validate_problem_statement_valid():
    """Test validating valid problem statement."""
    assert validate_problem_statement("Design a scalable system") is None
    assert validate_problem_statement("Fix the authentication bug") is None


def test_validate_problem_statement_empty():
    """Test validating empty problem statement."""
    assert validate_problem_statement("") == "Problem statement cannot be empty"
    assert validate_problem_statement("   ") == "Problem statement cannot be empty"
    assert validate_problem_statement(None) == "Problem statement cannot be empty"


def test_validate_problem_statement_too_long():
    """Test validating problem statement that's too long."""
    from src.core.constants import MAX_PROBLEM_STATEMENT_LENGTH
    long_problem = "a" * (MAX_PROBLEM_STATEMENT_LENGTH + 1)
    error = validate_problem_statement(long_problem)
    assert "too long" in error
    assert str(MAX_PROBLEM_STATEMENT_LENGTH) in error


def test_validate_paradigm_valid():
    """Test validating valid paradigm."""
    assert validate_paradigm("lateral thinking") is None
    assert validate_paradigm("systematic approach") is None


def test_validate_paradigm_empty():
    """Test validating empty paradigm."""
    assert validate_paradigm("") == "Paradigm cannot be empty"
    assert validate_paradigm("   ") == "Paradigm cannot be empty"
    assert validate_paradigm(None) == "Paradigm cannot be empty"


def test_validate_paradigm_too_long():
    """Test validating paradigm that's too long."""
    from src.core.constants import MAX_PARADIGM_LENGTH
    long_paradigm = "a" * (MAX_PARADIGM_LENGTH + 1)
    error = validate_paradigm(long_paradigm)
    assert "too long" in error
    assert str(MAX_PARADIGM_LENGTH) in error


def test_validate_transport_mode_valid():
    """Test validating valid transport modes."""
    from src.core.constants import TRANSPORT_MODES
    for mode in TRANSPORT_MODES:
        assert validate_transport_mode(mode) is None


def test_validate_transport_mode_invalid():
    """Test validating invalid transport mode."""
    error = validate_transport_mode("invalid_mode")
    assert "Invalid transport mode" in error
    assert "invalid_mode" in error


def test_validate_context_strategy_valid():
    """Test validating valid context strategies."""
    from src.core.constants import CONTEXT_STRATEGIES
    for strategy in CONTEXT_STRATEGIES:
        assert validate_context_strategy(strategy) is None


def test_validate_context_strategy_invalid():
    """Test validating invalid context strategy."""
    error = validate_context_strategy("invalid_strategy")
    assert "Invalid context strategy" in error
    assert "invalid_strategy" in error


def test_sanitize_string_default():
    """Test sanitizing string with default max length."""
    result = sanitize_string("Normal string")
    assert result == "Normal string"


def test_sanitize_string_control_chars():
    """Test sanitizing string with control characters."""
    result = sanitize_string("String\x00with\x01null")
    assert "\x00" not in result
    assert "\x01" not in result


def test_sanitize_string_newlines_preserved():
    """Test that newlines and tabs are preserved."""
    result = sanitize_string("Line1\nLine2\tTab")
    assert "\n" in result
    assert "\t" in result


def test_sanitize_string_truncation():
    """Test string truncation."""
    long_string = "a" * 2000
    result = sanitize_string(long_string, max_length=100)
    assert len(result) == 100


def test_sanitize_string_custom_max_length():
    """Test sanitizing with custom max length."""
    result = sanitize_string("test", max_length=2)
    assert result == "te"


def test_is_valid_thought_number_valid():
    """Test valid thought numbers."""
    assert is_valid_thought_number(1, 10) is True
    assert is_valid_thought_number(5, 10) is True
    assert is_valid_thought_number(10, 10) is True


def test_is_valid_thought_number_below_min():
    """Test thought number below minimum."""
    assert is_valid_thought_number(0, 10) is False
    assert is_valid_thought_number(-5, 10) is False


def test_is_valid_thought_number_above_max():
    """Test thought number above maximum."""
    assert is_valid_thought_number(11, 10) is False
    assert is_valid_thought_number(100, 10) is False


def test_is_valid_thought_number_edge_cases():
    """Test edge cases for thought number validation."""
    assert is_valid_thought_number(1, 1) is True  # Exactly min and max
    assert is_valid_thought_number(0, 1) is False  # Below min
    assert is_valid_thought_number(2, 1) is False  # Above max
