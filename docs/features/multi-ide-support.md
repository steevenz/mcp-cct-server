# Multi-IDE / Multi-LLM Support

**Feature ID**: `multi-ide-support` | **Version**: 1.1.0 | **PRD-ID**: `20260509-multi-ide-single-server`

---

## Overview

Enables concurrent access from multiple IDEs (VSCode, JetBrains, Cursor, Windsurf, GitHub Copilot) and LLM providers to a single CCT MCP server. Each IDE/LLM pair operates in an isolated context with its own sessions, thoughts, and rate limiting — all within one server process.

---

## Capabilities

### IDE Support Matrix

| IDE | Transport | Port | Isolated | Notes |
|-----|-----------|------|----------|-------|
| VSCode | STDIO | 8010 | Yes | Via NPX proxy |
| Cursor | STDIO | 8011 | Yes | Via NPX proxy |
| JetBrains | SSE | 8001 | Yes | Direct SSE |
| Windsurf | SSE | 8002 | Yes | Direct SSE |
| GitHub Copilot | SSE | 8003 | Yes | Direct SSE |

### LLM Provider Support

The server supports a broad spectrum of LLM providers for both main reasoning and cross-model validation:

- **Official Support**: Google Gemini, Anthropic Claude, OpenAI GPT
- **Extended Support**: DeepSeek, OpenRouter, NineRouter
- **Local Support**: Ollama (for fully offline reasoning)

Each LLM provider instance gets:

- **Isolated session space**: Sessions created by Provider A are invisible to Provider B
- **Independent rate limiting**: Rate limits are tracked per `llm_instance_id`
- **Per-LLM usage metrics**: Token counts and costs scoped to each instance
- **Audit trail**: All operations logged with `llm_instance_id` for forensic analysis

### OpenCode Framework Integration

The Multi-IDE architecture serves as the foundation for **OpenCode**, our framework for multi-agent collaboration:
- **Shared Cognitive Bus**: Multiple agents (architect, coder, reviewer) can share a single `session_id`.
- **Cross-Model Critique**: Use different providers (e.g., Claude for coding, DeepSeek for review) in the same session.
- **Role Scoping**: Agent roles are preserved in memory metadata for clear task attribution.

---

## Feature Components

### 1. Connection Registry

**File**: `database/config/mcp_server_registry.json`

Tracks all active IDE/LLM connections in real-time. Used for:
- Monitoring active connections
- Debugging connectivity issues
- Cleanup on connection loss

### 2. LLM Instance Registry

**Endpoint**: `GET /status/llms`

In-memory registry of authenticated LLM instances. Tracks:
- First seen timestamp
- Last active timestamp
- Authentication method
- Authorized scopes

### 3. Header Injection

Every MCP tool call receives:

```python
# Injected automatically by main.py
_llm_instance_id: str  # From X-LLM-INSTANCE-ID or X-IDE-ORIGIN
_ide_origin: str        # From X-IDE-ORIGIN header
```

Tool handlers use these for:
- Memory scoping (session/thought isolation)
- Audit logging
- Rate limiting

### 4. Memory Scoping

The `MemoryManager` now supports per-LLM queries:

```python
# Before (v1.0.0): Global scope
manager.list_sessions()  # Returns ALL sessions

# After (v1.1.0): Scoped by LLM
manager.list_sessions(llm_instance_id="vscode")  # Only vscode sessions
manager.get_aggregate_usage(llm_instance_id="jetbrains")  # JetBrains only
```

---

## API Changes

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status/llms` | GET | List all connected LLM instances |
| `/status/llm/{id}` | GET | Detail for specific LLM instance |

### Enhanced Endpoints

| Endpoint | Change |
|----------|--------|
| `/status` | Added `connected_llms` field, scoped usage by request LLM |
| `/cognitive-api/v1/sync` | Accepts `X-IDE-ORIGIN` and `X-LLM-INSTANCE-ID` headers |
| `/cognitive-api/v1/data` | Filters data by `llm_instance_id` when querying sessions |

---

## Performance Characteristics

| Metric | Single LLM | 5 Concurrent LLMs |
|--------|-----------|-------------------|
| Memory | ~50MB | ~55MB (+10%) |
| CPU | 1 core | 1.2 cores |
| DB connection | 1 | 1 (WAL mode) |
| Port usage | 1 | 1 |

The overhead of multi-LLM isolation is minimal because:
- All sessions share the same SQLite database (WAL mode)
- No process duplication
- Scoping is done at query level via indexed columns

---

## Related Configuration

| File | Purpose |
|------|---------|
| `database/config/mcp_client_multi_ide.json` | Complete multi-IDE setup reference |
| `database/config/mcp_client_stdio.json` | STDIO transport config |
| `database/config/mcp_client_sse.json` | SSE transport config |

---

## Future Roadmap

- **v1.2.0**: WebSocket transport for real-time streaming
- **v1.3.0**: Dynamic LLM instance registration (no restart required)
- **v2.0.0**: Redis-backed connection pool for horizontal scaling
