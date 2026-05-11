# Upgrade Guide: v1.0.0 → v1.1.0

**Date**: 2026-05-09 | **PRD-ID**: `20260509-multi-ide-single-server`

---

## Summary

This upgrade introduces **multi-IDE / multi-LLM support** through a **single-server, header-based isolation** architecture. All IDEs now share one Python process instead of spawning separate instances.

---

## What Changed

### Architecture

```
Before (v1.0.0):                       After (v1.1.0):
                                         
NPX Wrapper ──→ Python Server           NPX Wrapper ──┐
(port 8001, single IDE)                 (any port)     ├──→ Shared Python Server
                                                     (port 8001, multi-IDE)
  ● One server per launch                                     
  ● No IDE isolation                     SSE Client ──┘
  ● Global session scope                 (direct, X-IDE-ORIGIN)
                                       
                                        ● One server for all IDEs
                                        ● Per-LLM session isolation
                                        ● Header-based routing
```

### Key Changes

| Area | v1.0.0 | v1.1.0 |
|------|--------|--------|
| Server instances | One per IDE launch | One shared instance |
| Session scope | Global | Per `llm_instance_id` |
| Memory queries | `list_sessions()` returns all | `list_sessions(llm_id=...)` scoped |
| NPX CLI args | None | `--ide`, `--transport`, `--port`, `--host` |
| HTTP headers | `X-API-KEY` only | `X-IDE-ORIGIN`, `X-LLM-INSTANCE-ID` |
| Status endpoint | Global stats only | Per-LLM stats + registry |
| Data endpoint | Unscoped queries | LLM-scoped session queries |
| Connection tracking | Lock file only | JSON registry file |
| Database schema | `sessions(data)` | `sessions(data, llm_instance_id)` |

---

## Migration Steps

### Step 1: Update NPX Wrapper

Replace `scripts/server/js/index.js` with the v1.1.0 version.

**What changed:**
- Added CLI argument parser (`--ide`, `--transport`, `--port`, `--host`)
- Added connection registry for tracking IDE connections
- Added `X-IDE-ORIGIN` header injection on forwarded requests
- Removed `TransportPool` — single server connectivity only
- Simplified `ensureSharedServer()` — auto-detect or start once

### Step 2: Update Python Backend

Replace `src/main.py` with v1.1.0 version.

**What changed:**
- Added `_llm_instance_id()` helper for header extraction
- Added `_llm_registry` — in-memory LLM connection tracking
- Added `/status/llms` and `/status/llm/{id}` endpoints
- Updated `/status` to show per-LLM usage and connected LLMs
- Updated `mcp_http_endpoint` to inject `_llm_instance_id` and `_ide_origin`
- Updated `get_all_data` to filter by `llm_instance_id`
- Added `import threading` for registry lock

### Step 3: Update Memory Manager

Replace `src/engines/memory/manager.py` with v1.1.0 version.

**What changed:**
- `__init__()` now accepts optional `llm_instance_id` parameter
- `_init_db()` adds `llm_instance_id` column to `sessions` table with auto-migration
- `create_session()` accepts `llm_instance_id` parameter, stores in DB
- `list_sessions()` now accepts `llm_instance_id`, `limit`, `offset` parameters
- `get_session_history()` now accepts `limit` parameter (default 200)
- `get_aggregate_usage()` now accepts `llm_instance_id` parameter

### Step 4: Update Config Files

Update `database/config/mcp_client_*.json` to include `X-IDE-ORIGIN` headers.

**Before (v1.0.0 SSE):**
```json
{
  "Creative Critical Thinking": {
    "url": "http://localhost:8001/cognitive-api/v1/sync",
    "headers": {
      "X-API-KEY": "cct-secret-token-2026"
    }
  }
}
```

**After (v1.1.0 SSE):**
```json
{
  "Creative Critical Thinking": {
    "url": "http://localhost:8001/cognitive-api/v1/sync",
    "headers": {
      "X-API-KEY": "cct-secret-token-2026",
      "X-IDE-ORIGIN": "jetbrains"
    }
  },
  "CCT Copilot": {
    "url": "http://localhost:8001/cognitive-api/v1/sync",
    "headers": {
      "X-API-KEY": "cct-secret-token-2026",
      "X-IDE-ORIGIN": "github_copilot"
    }
  }
}
```

### Step 5: Update Package Scripts

Update `package.json` with per-IDE npm scripts (see `package.json` section in README).

---

## Rollback Plan

If issues arise, revert to v1.0.0:

```bash
# 1. Restore original files
git checkout HEAD~1 -- scripts/server/js/index.js
git checkout HEAD~1 -- src/main.py
git checkout HEAD~1 -- src/engines/memory/manager.py

# 2. Revert config files
git checkout HEAD~1 -- database/config/

# 3. Kill any running servers
taskkill /F /IM python.exe 2>$null

# 4. Restart with v1.0.0
npm run cct-server
```

---

## Verification Checklist

After migration, verify:

- [ ] `curl http://localhost:8001/status` returns 200
- [ ] `curl http://localhost:8001/status/llms` lists connected LLMs
- [ ] VSCode STDIO connects and creates sessions
- [ ] JetBrains SSE connects and creates sessions (different port)
- [ ] Sessions from VSCode are not visible to JetBrains
- [ ] `X-IDE-ORIGIN` header appears in forwarded requests
- [ ] Rate limiting functions per-LLM independently
- [ ] Connection registry updates on startup/teardown

---

## Known Issues

1. **Database migration**: The `llm_instance_id` column is added via `ALTER TABLE ADD COLUMN` on first startup. Existing sessions will have `NULL` and default to `'default'`.
2. **Registry file**: If multiple instances are killed simultaneously, the registry may show stale entries. Run `del database\config\mcp_server_registry.json` to reset.
3. **STDIO proxy**: Each STDIO instance uses its own port (8010, 8011) for NPX process identification, but all proxy to the shared server on 8001.
