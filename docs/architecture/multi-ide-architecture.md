# Multi-IDE / Multi-LLM Architecture

**Version**: 1.1.0 | **PRD-ID**: `20260509-multi-ide-single-server`

---

## 1. Design Philosophy

This architecture follows the **Lego Principle**: Modular Monolith design that enables **concurrent access from multiple IDEs and LLM providers** using a **single Python server process**. Isolation is achieved at the **application layer** through header-based routing and memory scoping — not by spawning redundant server instances.

The system is designed for **Zero-Config Onboarding**: automated setup scripts handle dependencies, model acquisition, and IDE registration.

```
IDE A (VSCode)     IDE B (JetBrains)    IDE C (Cursor)
    |                    |                    |
[STDIO Proxy]       [SSE Direct]        [STDIO Proxy]
    |                    |                    |
    +--------------------+--------------------+
                         |
            ONE Python Server (port 8010)
                         |
              +----------+----------+
              |                     |
    MemoryManager           ConnectionRegistry
    (per-LLM scoped)       (connection tracking)
```

---

## 2. Core Concepts

### 2.1 Single Server, Multi-Tenant

- **One port, one process**: The Python FastAPI server runs once (default port 8010)
- **All IDEs connect to same server**: STDIO mode proxies through NPX, SSE connects directly
- **Zero resource waste**: No memory duplication between IDE sessions. Especially critical for local LLM (Gemma) models.

### 2.2 Automated Lifecycle

The server is no longer just a listener; it manages its own environment:
- **Auto-Download**: Pre-fetches Gemma 2B & 9B models via `scripts/setup/download_models.py`.
- **Auto-Register**: Injects its own `npx` connection string into IDE config files via `scripts/setup/register_mcp.py`.

### 2.2 Header-Based Routing

Every request carries identity headers:

| Header | Purpose | Example |
|--------|---------|---------|
| `X-IDE-ORIGIN` | Identifies the IDE source | `vscode`, `jetbrains` |
| `X-LLM-INSTANCE-ID` | Identifies the LLM instance | `cct-assistant`, `bench-llm-3` |
| `X-API-KEY` | Authentication | `cct_live_abc123.xyz` |

### 2.3 Memory Scoping

The `MemoryManager` scopes all queries by `llm_instance_id`:

- `create_session(llm_instance_id=...)` — creates session tagged to LLM
- `list_sessions(llm_instance_id=...)` — returns only that LLM's sessions
- `get_aggregate_usage(llm_instance_id=...)` — reports per-LLM usage

---

## 3. Architecture Components

### 3.1 NPX Wrapper (`scripts/server/js/index.js`)

```
┌─────────────────────────────┐
│       NPX Wrapper           │
├─────────────────────────────┤
│  CLI Parser                 │
│  --ide <name>               │
│  --transport <stdio|sse>    │
│  --port <number>            │
├─────────────────────────────┤
│  Connection Registry        │
│  (tracks all active IDEs)   │
├─────────────────────────────┤
│  Auth Handshake             │
│  (API key management)       │
├─────────────────────────────┤
│  STDIO Proxy                │
│  (stdin/stdout ↔ HTTP)      │
└─────────────────────────────┘
```

**Modes of operation:**

| Mode | Transport | Description |
|------|-----------|-------------|
| `proxy` | `stdio` | Wrapper bridges stdin/stdout to shared HTTP server |
| `direct` | `sse` | IDE connects directly to HTTP SSE port |

### 3.2 Python Backend (`src/main.py`)

```
┌──────────────────────────────────────┐
│   FastAPI Application                │
├──────────────────────────────────────┤
│  GET  /status                        │
│  GET  /status/llms                   │
│  GET  /status/llm/{id}               │
│  GET  /cognitive-api/v1/data         │
│  POST /cognitive-api/v1/sync         │
│  POST /cognitive-api/v1/auth/*       │
├──────────────────────────────────────┤
│  LLM Instance Registry              │
│  (tracks active LLM connections)     │
├──────────────────────────────────────┤
│  MemoryManager (LLM-scoped)          │
│  (session, thought, pattern queries) │
└──────────────────────────────────────┘
```

### 3.3 Memory Manager (`src/engines/memory/manager.py`)

Key changes for multi-LLM support:

- **`sessions` table**: Added `llm_instance_id` column with index
- **`create_session()`**: Accepts `llm_instance_id` parameter
- **`list_sessions()`**: Filters by `llm_instance_id`, supports pagination
- **`get_session_history()`**: Accepts `limit` parameter (default 200, max 1000)
- **`get_aggregate_usage()`**: Filters by `llm_instance_id`

### 3.4 Connection Registry (`database/config/mcp_server_registry.json`)

Lightweight JSON file tracking active connections:

```json
{
  "prd_id": "20260509-multi-ide-single-server",
  "connections": [
    {
      "ide": "vscode",
      "transport": "stdio",
      "pid": 12345,
      "connectedAt": "2026-05-09T04:00:00.000Z"
    }
  ],
  "total": 1
}
```

---

## 4. Data Flow

### 4.1 Request Lifecycle

```
Client (IDE)
  │
  ├─ X-IDE-ORIGIN: vscode
  ├─ X-LLM-INSTANCE-ID: cct-abc
  │
  ▼
FastAPI Route
  │
  ├─ _llm_instance_id(request)     ← Extract header
  ├─ Auth check (validate_api_key)  ← Verify auth + rate limit
  │
  ▼
  ├─ Register in _llm_registry      ← Track connected LLM
  │
  ▼
MCP Endpoint
  │
  ├─ Inject _llm_instance_id into tool args
  │
  ▼
Tool Handler
  │
  ├─ MemoryManager scopes by llm_instance_id
  ├─ Session created/queries scoped to LLM
  │
  ▼
Response
```

### 4.2 Session Isolation

```
LLM Instance A (vscode)
  ├─ session_abc123 (llm_instance_id=vscode)
  ├─ session_def456 (llm_instance_id=vscode)

LLM Instance B (jetbrains)
  ├─ session_ghi789 (llm_instance_id=jetbrains)
  ├─ session_jkl012 (llm_instance_id=jetbrains)

MemoryManager.list_sessions("vscode") → [abc123, def456]
MemoryManager.list_sessions("jetbrains") → [ghi789, jkl012]
```

---

## 5. Configuration Files

| File | Purpose |
|------|---------|
| `database/config/mcp_client_multi_ide.json` | Central multi-IDE config |
| `database/config/mcp_client_stdio.json` | STDIO config for VSCode/Cursor |
| `database/config/mcp_client_sse.json` | SSE config for JetBrains/Copilot/Windsurf |
| `database/config/mcp_server_registry.json` | Live connection tracking |

---

## 6. Security Model

- **Per-LLM rate limiting**: Each `llm_instance_id` has independent rate limit window
- **Session isolation**: One LLM cannot access another LLM's sessions
- **Connection tracking**: Registry enables audit trail of active connections
- **Authentication**: X-API-KEY validated before LLM context is established

---

## 7. Upgrade from 1.0.0

See [docs/versions/v1.1.0/multi-ide-upgrade.md](../versions/v1.1.0/multi-ide-upgrade.md) for detailed migration guide.

**Summary of breaking changes:**

1. Database schema: `sessions` table gains `llm_instance_id` column (auto-migration)
2. NPX wrapper: New CLI args (`--ide`, `--host`)
3. Environment variable: `CCT_IDE` for IDE identification

---

## 8. Future Considerations

- **WebSocket transport**: For push-based realtime updates
- **LLM-specific tool registrations**: Different tools per LLM provider
- **Dynamic instances**: Allow registering new LLMs at runtime without restart
- **Redis connection pooling**: For horizontal scaling across machines
