from __future__ import annotations

import os
from dataclasses import dataclass

PRD_ID = "20260412-000000-cct-mcp-scaffold"


@dataclass(frozen=True, slots=True)
class Settings:
    server_name: str
    transport: str
    host: str
    port: int
    max_sessions: int
    log_level: str
    db_path: str
    pricing_path: str
    default_model: str
    # User operational preferences
    max_thoughts: int
    max_content_length: int
    max_context_tokens: int
    context_strategy: str
    tp_threshold: float
    # Forex configuration
    forex_cache_ttl: int
    forex_default_rate: float
    forex_api_url: str
    enabled_tool_groups: set[str]


def _parse_int(value: str, *, min_value: int, max_value: int, field_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}") from exc

    if parsed < min_value or parsed > max_value:
        raise ValueError(f"Invalid {field_name}")

    return parsed


def _parse_float(value: str, *, min_value: float, max_value: float, field_name: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}") from exc

    if parsed < min_value or parsed > max_value:
        raise ValueError(f"Invalid {field_name}")

    return parsed


def load_settings() -> Settings:
    server_name = os.getenv("CCT_SERVER_NAME", "cct-mcp-server").strip()
    if not server_name:
        raise ValueError("Invalid server name")

    transport = os.getenv("CCT_TRANSPORT", "stdio").strip().lower()
    if transport == "http":
        transport = "sse"
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("Invalid transport")

    host = os.getenv("CCT_HOST", "0.0.0.0").strip()
    if not host:
        raise ValueError("Invalid host")

    port_raw = os.getenv("CCT_PORT", "8000").strip()
    port = _parse_int(port_raw, min_value=1, max_value=65535, field_name="port")

    max_sessions_raw = os.getenv("CCT_MAX_SESSIONS", "128").strip()
    max_sessions = _parse_int(max_sessions_raw, min_value=1, max_value=100000, field_name="max sessions")

    log_level = os.getenv("CCT_LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Invalid log level: {log_level}")

    # Optional paths and model with defaults from constants
    from src.core.constants import DEFAULT_DB_PATH, DEFAULT_PRICING_PATH, DEFAULT_MODEL
    
    db_path = os.getenv("CCT_DB_PATH", DEFAULT_DB_PATH).strip()
    if not db_path:
        raise ValueError("Invalid database path")
    
    pricing_path = os.getenv("CCT_PRICING_PATH", DEFAULT_PRICING_PATH).strip()
    if not pricing_path:
        raise ValueError("Invalid pricing path")
    
    default_model = os.getenv("CCT_DEFAULT_MODEL", DEFAULT_MODEL).strip()
    if not default_model:
        raise ValueError("Invalid default model")

    # User operational preferences with validation
    from src.core.constants import (
        MAX_THOUGHTS_PER_SESSION,
        MAX_THOUGHT_CONTENT_LENGTH,
        DEFAULT_MAX_CONTEXT_TOKENS,
        DEFAULT_CONTEXT_STRATEGY,
        CONTEXT_STRATEGIES,
        DEFAULT_TP_THRESHOLD,
        FOREX_CACHE_TTL,
        FOREX_DEFAULT_RATE,
        FOREX_API_URL,
    )
    
    max_thoughts_raw = os.getenv("CCT_MAX_THOUGHTS", str(MAX_THOUGHTS_PER_SESSION)).strip()
    max_thoughts = _parse_int(max_thoughts_raw, min_value=10, max_value=10000, field_name="max thoughts")
    
    max_content_length_raw = os.getenv("CCT_MAX_CONTENT_LENGTH", str(MAX_THOUGHT_CONTENT_LENGTH)).strip()
    max_content_length = _parse_int(max_content_length_raw, min_value=100, max_value=100000, field_name="max content length")
    
    max_context_tokens_raw = os.getenv("CCT_MAX_CONTEXT_TOKENS", str(DEFAULT_MAX_CONTEXT_TOKENS)).strip()
    max_context_tokens = _parse_int(max_context_tokens_raw, min_value=1000, max_value=128000, field_name="max context tokens")
    
    context_strategy = os.getenv("CCT_CONTEXT_STRATEGY", DEFAULT_CONTEXT_STRATEGY).strip().lower()
    if context_strategy not in CONTEXT_STRATEGIES:
        raise ValueError(f"Invalid context strategy: {context_strategy}. Options: {CONTEXT_STRATEGIES}")
    
    tp_threshold_raw = os.getenv("CCT_TP_THRESHOLD", str(DEFAULT_TP_THRESHOLD)).strip()
    tp_threshold = _parse_float(tp_threshold_raw, min_value=0.0, max_value=1.0, field_name="TP threshold")
    
    # Forex configuration
    forex_cache_ttl_raw = os.getenv("CCT_FOREX_CACHE_TTL", str(FOREX_CACHE_TTL)).strip()
    forex_cache_ttl = _parse_int(forex_cache_ttl_raw, min_value=60, max_value=604800, field_name="forex cache TTL")
    
    forex_default_rate_raw = os.getenv("CCT_FOREX_DEFAULT_RATE", str(FOREX_DEFAULT_RATE)).strip()
    forex_default_rate = _parse_float(forex_default_rate_raw, min_value=1000.0, max_value=50000.0, field_name="forex default rate")
    
    forex_api_url = os.getenv("CCT_FOREX_API_URL", FOREX_API_URL).strip()
    if not forex_api_url:
        raise ValueError("Invalid forex API URL")

    # Tool Group Configuration
    # Defaults to core, primitive, hybrid, and hitl tools. 
    # Metadata (session) and Auditor (export) tools are disabled by default for LLM interaction.
    default_groups = "core,primitive,hybrid,hitl"
    enabled_groups_raw = os.getenv("CCT_ENABLED_TOOL_GROUPS", default_groups).strip().lower()
    enabled_tool_groups = {g.strip() for g in enabled_groups_raw.split(",") if g.strip()}

    return Settings(
        server_name=server_name,
        transport=transport,
        host=host,
        port=port,
        max_sessions=max_sessions,
        log_level=log_level,
        db_path=db_path,
        pricing_path=pricing_path,
        default_model=default_model,
        max_thoughts=max_thoughts,
        max_content_length=max_content_length,
        max_context_tokens=max_context_tokens,
        context_strategy=context_strategy,
        tp_threshold=tp_threshold,
        forex_cache_ttl=forex_cache_ttl,
        forex_default_rate=forex_default_rate,
        forex_api_url=forex_api_url,
        enabled_tool_groups=enabled_tool_groups,
    )

