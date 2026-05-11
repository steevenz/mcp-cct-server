# Working Context

## Current Truth
- MCP is executed via a Node STDIO wrapper (`cct-mcp`) that proxies JSON-RPC to a shared local HTTP/SSE backend.
- Some IDE/Go MCP clients fail decoding `tools/call` results because `result.content` was not a flat `wireContent[]` list.
- `.agents/state.yaml` and `.agents/contexts/*` were missing and are now introduced as the new context source of truth for workflow compliance.

## Context Gap
- No historical `task_id` existed because `.agents/state.yaml` was absent previously.
- No canonical `.agents/contexts/soul.md` existed; only `SOUL.md` in repo root.

## Done List
- Added `.agents/state.yaml` with an active task id for the current fix.
- Normalized `tools/call` response shape in `src/main.py` so `content` is always `wireContent[]` (flat objects).
- Documented IDE tool-name constraints earlier (server key must be regex-safe, e.g. `cct_mcp`).
- Fixed pipeline selection call sites to pass `complexity` (routing + session tools).
- Hardened `tools/call` normalization (recursive flatten + enforce string `type`), removed internal error string from `/status`, and switched API key check to constant-time compare.
- Added a regression test asserting `POST /cognitive-api/v1/sync` `tools/call` returns a flat `wireContent[]` list (and it passes).
- Hardened Docker runtime defaults for zero-manual startup: container now defaults to port `8010`, includes a default local dashboard API key for local docker use, and uses `/health` readiness probe.
- Fixed scripts reliability issues: undefined `MIN_PYTHON_VERSION` in `scripts/setup/setup.sh`, venv path fallback in `scripts/server/js/index.js`, unix service manager init-order bug in `scripts/setup/services/unix/service.py`, and dependency-install failure handling in `scripts/server/setup.py`.
- Updated Docker setup guide to a one-command run flow on `8010` with readiness verification and MCP sync probe example.
- Added `docker-compose.yml` with service `cct-server`, port `8010:8010`, persisted `./database` volume, `unless-stopped` restart policy, and readiness healthcheck against `/health`.
- Validated compose manifest structure with `docker compose -f docker-compose.yml config`.
- Implemented dual-mode authentication service with persisted handshake sessions, per-instance API keys, key rotation/revocation, rate limiting, and audit log persistence.
- Integrated auth service into API layer with scoped dependencies (`mcp:sync`, `mcp:sse`, `auth:rotate`, `admin:revoke`) and TLS policy (production hard-fail, local/dev warning mode).
- Added bootstrap key generator script `scripts/server/keygen.py` with `--install` flow for legacy client compatibility and `.env` automation.
- Updated Node wrapper API key resolution to prefer `CCT_CLIENT_API_KEY` then fallback to `CCT_DASHBOARD_API_KEY`.
- Added auth unit tests covering legacy validation, handshake issuance, scoped authorization, rotation, and rate limiting.

## Target Queue
1. Add wrapper-side automatic handshake + key rotation persistence (currently wrapper supports env-based key selection, no automatic handshake call yet).
2. Run Docker smoke deployment with new auth endpoints and verify handshake/rotate/revoke flow on `8010` once Docker daemon is available.
