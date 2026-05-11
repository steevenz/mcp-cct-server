# Implementation Plan - 20260428-182350-mcp-startup-fetch-fix

Based on plan from `implementation-plans/20260428-165217-windows-service-tls-hardening.md`.

## System Context
- Subsystem: MCP bootstrap/discovery and HTTP compatibility endpoint.
- `prd_id`: `20260428-x-api-key-resolution` (auth/header alignment) and startup transport stabilization lane.
- Problem: MCP client startup failed with `fetch failed` because bootstrap selected a frontend port (`:3000`) and HTTP endpoint returned non-MCP payload.

## Architectural Justification
- Replace weak liveness checks with identity checks: `/status` must return CCT JSON signature (`server`, `transport`).
- Keep a compatibility JSON-RPC handler on `POST /cognitive-api/v1/sync` to support IDE clients expecting `initialize`, `ping`, and `tools/list`.
- Preserve zero-trust gate by keeping `X-API-KEY` validation on both SSE and HTTP endpoints.

## Dependencies and Security
- No new package dependencies.
- Security controls:
  - Fail closed for invalid API key (`403`).
  - Reject malformed request body (`400`) and invalid method (`-32601` JSON-RPC error).
  - Keep secrets in env/.env only; no key material in logs.

## Rollback Strategy
1. Revert `scripts/server/discover.py` and `scripts/server/setup.py` to prior endpoint detection logic.
2. Revert `src/main.py` MCP HTTP handler to previous behavior.
3. Regenerate config via `python scripts/server/setup.py --skip-deps`.
4. Restart service and verify with `python scripts/server/manage.py status`.
