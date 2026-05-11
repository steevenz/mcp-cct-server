# Implementation Plan - 20260428-220000-multi-ide-shared-proxy

Based on plan from `implementation-plans/20260428-194800-npm-wrapper-process-manager.md`.

## System Context
- Subsystem: Node MCP STDIO wrapper.
- `prd_id`: `20260428-220000-multi-ide-shared-proxy`.
- Goal: support multiple IDEs sharing one underlying CCT server without breaking MCP STDIO constraints.

## Design
- Convert wrapper to a per-IDE STDIO JSON-RPC proxy.
- Ensure a single shared HTTP/SSE backend server exists (discover or spawn).
- Validate server identity via `GET /status` (must return JSON signature `server`, `transport`).
- Validate auth via `POST /cognitive-api/v1/sync` `ping` using `X-API-KEY`.
- Maintain shared backend state in `database/config/cct_shared_server.json` with a ref counter.

## Security
- Wrapper logs to stderr only.
- Proxy never prints API keys.
- API key loaded from `.env` or process env (`CCT_DASHBOARD_API_KEY`).

## Rollback
- Revert `scripts/server/js/index.js` to direct-stdio child launch.
- Keep existing HTTP/SSE server flows managed by Python scripts.
