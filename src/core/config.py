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


def _parse_int(value: str, *, min_value: int, max_value: int, field_name: str) -> int:
    try:
        parsed = int(value)
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
    if transport not in {"stdio", "http"}:
        raise ValueError("Invalid transport")

    host = os.getenv("CCT_HOST", "0.0.0.0").strip()
    if not host:
        raise ValueError("Invalid host")

    port_raw = os.getenv("CCT_PORT", "8000").strip()
    port = _parse_int(port_raw, min_value=1, max_value=65535, field_name="port")

    max_sessions_raw = os.getenv("CCT_MAX_SESSIONS", "128").strip()
    max_sessions = _parse_int(max_sessions_raw, min_value=1, max_value=100000, field_name="max sessions")

    return Settings(
        server_name=server_name,
        transport=transport,
        host=host,
        port=port,
        max_sessions=max_sessions,
    )
