# Tasks - 20260428-182350-mcp-startup-fetch-fix

Based on tasks from `tasks/20260428-165217-windows-service-tls-hardening.md`.

## Phase 1: Preparation
- [x] Reproduce MCP startup failure from logs (`listTools -> fetch failed`).
- [x] Confirm wrong target (`localhost:3000` returns HTML, not MCP JSON).
- DoD: Evidence captured from live requests to `:3000` and `:8000`.

## Phase 2: Core Logic
- [x] Update discovery probe to validate `/status` CCT JSON signature.
- [x] Update setup bootstrap URL detection to the same signature rule.
- DoD: Generated `database/config/mcp_client_sse.json` points to `http://localhost:8000/cognitive-api/v1/sync`.

## Phase 3: Integration
- [x] Implement MCP JSON-RPC compatibility in `src/main.py` for `initialize`, `ping`, `tools/list`, `tools/call`.
- [x] Add explicit `CCT_DASHBOARD_API_KEY` in `.env` for deterministic local auth.
- DoD: `POST tools/list` returns JSON-RPC `result.tools` list with HTTP 200.

## Phase 4: Validation
- [x] Run compile and diagnostics checks on modified files.
- [x] Verify runtime endpoint with generated config and authenticated requests.
- [ ] Re-check IDE MCP extension startup after config reload.
- DoD: IDE no longer shows `ExtHostMCPService#$start list tools failed`.
