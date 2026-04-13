import pytest
import os
from src.core.config import load_settings, _parse_int, _parse_float


def test_parse_int_valid():
    """Test valid integer parsing within range."""
    assert _parse_int("50", min_value=10, max_value=100, field_name="test") == 50


def test_parse_int_below_min():
    """Test integer parsing below minimum raises error."""
    with pytest.raises(ValueError, match="Invalid test"):
        _parse_int("5", min_value=10, max_value=100, field_name="test")


def test_parse_int_above_max():
    """Test integer parsing above maximum raises error."""
    with pytest.raises(ValueError, match="Invalid test"):
        _parse_int("150", min_value=10, max_value=100, field_name="test")


def test_parse_int_invalid_string():
    """Test invalid string raises error."""
    with pytest.raises(ValueError, match="Invalid test"):
        _parse_int("abc", min_value=10, max_value=100, field_name="test")


def test_parse_float_valid():
    """Test valid float parsing within range."""
    assert _parse_float("0.5", min_value=0.0, max_value=1.0, field_name="test") == 0.5


def test_parse_float_below_min():
    """Test float parsing below minimum raises error."""
    with pytest.raises(ValueError, match="Invalid test"):
        _parse_float("-0.1", min_value=0.0, max_value=1.0, field_name="test")


def test_parse_float_above_max():
    """Test float parsing above maximum raises error."""
    with pytest.raises(ValueError, match="Invalid test"):
        _parse_float("1.5", min_value=0.0, max_value=1.0, field_name="test")


def test_parse_float_invalid_string():
    """Test invalid string raises error."""
    with pytest.raises(ValueError, match="Invalid test"):
        _parse_float("abc", min_value=0.0, max_value=1.0, field_name="test")


def test_load_settings_defaults():
    """Test loading settings with default values."""
    # Clear environment to test defaults
    for key in list(os.environ.keys()):
        if key.startswith("CCT_"):
            del os.environ[key]
    
    settings = load_settings()
    
    assert settings.server_name == "cct-mcp-server"
    assert settings.transport == "stdio"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.max_sessions == 128
    assert settings.log_level == "INFO"


def test_load_settings_custom():
    """Test loading settings with custom environment variables."""
    os.environ["CCT_SERVER_NAME"] = "custom-server"
    os.environ["CCT_TRANSPORT"] = "http"
    os.environ["CCT_HOST"] = "127.0.0.1"
    os.environ["CCT_PORT"] = "9000"
    os.environ["CCT_MAX_SESSIONS"] = "256"
    os.environ["CCT_LOG_LEVEL"] = "DEBUG"
    
    settings = load_settings()
    
    assert settings.server_name == "custom-server"
    assert settings.transport == "http"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.max_sessions == 256
    assert settings.log_level == "DEBUG"
    
    # Cleanup
    del os.environ["CCT_SERVER_NAME"]
    del os.environ["CCT_TRANSPORT"]
    del os.environ["CCT_HOST"]
    del os.environ["CCT_PORT"]
    del os.environ["CCT_MAX_SESSIONS"]
    del os.environ["CCT_LOG_LEVEL"]


def test_load_settings_invalid_server_name():
    """Test empty server name raises error."""
    os.environ["CCT_SERVER_NAME"] = ""
    
    with pytest.raises(ValueError, match="Invalid server name"):
        load_settings()
    
    del os.environ["CCT_SERVER_NAME"]


def test_load_settings_invalid_transport():
    """Test invalid transport raises error."""
    os.environ["CCT_TRANSPORT"] = "invalid"
    
    with pytest.raises(ValueError, match="Invalid transport"):
        load_settings()
    
    del os.environ["CCT_TRANSPORT"]


def test_load_settings_invalid_log_level():
    """Test invalid log level raises error."""
    os.environ["CCT_LOG_LEVEL"] = "INVALID"
    
    with pytest.raises(ValueError, match="Invalid log level"):
        load_settings()
    
    del os.environ["CCT_LOG_LEVEL"]


def test_load_settings_user_preferences():
    """Test loading user operational preferences."""
    os.environ["CCT_MAX_THOUGHTS"] = "500"
    os.environ["CCT_MAX_CONTENT_LENGTH"] = "10000"
    os.environ["CCT_MAX_CONTEXT_TOKENS"] = "8000"
    os.environ["CCT_CONTEXT_STRATEGY"] = "full"
    os.environ["CCT_TP_THRESHOLD"] = "0.85"
    
    settings = load_settings()
    
    assert settings.max_thoughts == 500
    assert settings.max_content_length == 10000
    assert settings.max_context_tokens == 8000
    assert settings.context_strategy == "full"
    assert settings.tp_threshold == 0.85
    
    # Cleanup
    del os.environ["CCT_MAX_THOUGHTS"]
    del os.environ["CCT_MAX_CONTENT_LENGTH"]
    del os.environ["CCT_MAX_CONTEXT_TOKENS"]
    del os.environ["CCT_CONTEXT_STRATEGY"]
    del os.environ["CCT_TP_THRESHOLD"]


def test_load_settings_forex_config():
    """Test loading forex configuration."""
    os.environ["CCT_FOREX_CACHE_TTL"] = "3600"
    os.environ["CCT_FOREX_DEFAULT_RATE"] = "18000.0"
    os.environ["CCT_FOREX_API_URL"] = "https://api.example.com/rates"
    
    settings = load_settings()
    
    assert settings.forex_cache_ttl == 3600
    assert settings.forex_default_rate == 18000.0
    assert settings.forex_api_url == "https://api.example.com/rates"
    
    # Cleanup
    del os.environ["CCT_FOREX_CACHE_TTL"]
    del os.environ["CCT_FOREX_DEFAULT_RATE"]
    del os.environ["CCT_FOREX_API_URL"]


def test_load_settings_invalid_context_strategy():
    """Test invalid context strategy raises error."""
    os.environ["CCT_CONTEXT_STRATEGY"] = "invalid_strategy"
    
    with pytest.raises(ValueError, match="Invalid context strategy"):
        load_settings()
    
    del os.environ["CCT_CONTEXT_STRATEGY"]


def test_load_settings_invalid_max_thoughts():
    """Test max thoughts below minimum raises error."""
    os.environ["CCT_MAX_THOUGHTS"] = "5"  # Below min of 10
    
    with pytest.raises(ValueError, match="Invalid max thoughts"):
        load_settings()
    
    del os.environ["CCT_MAX_THOUGHTS"]


def test_load_settings_invalid_tp_threshold():
    """Test TP threshold above maximum raises error."""
    os.environ["CCT_TP_THRESHOLD"] = "1.5"  # Above max of 1.0
    
    with pytest.raises(ValueError, match="Invalid TP threshold"):
        load_settings()
    
    del os.environ["CCT_TP_THRESHOLD"]
