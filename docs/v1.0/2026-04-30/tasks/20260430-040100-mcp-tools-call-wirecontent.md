# Tasks - 20260430-040100-mcp-tools-call-wirecontent

Based on tasks from `docs/v1.0/2026-04-28/tasks/20260428-220000-multi-ide-shared-proxy.md`.

## Debug
- [x] Reproduce client-side decode failure context (Go unmarshal error on `tools/call`).
- [x] Locate response construction in `src/main.py` `tools/call` branch.

## Patch
- [x] Normalize `tools/call` result to a flat `wireContent[]` list.
- [x] Ensure non-wire objects become `{type:\"text\", text:\"...\"}`.
- [x] Fix pipeline selection call sites missing `complexity` arg (`routing.py`, `session.py`).

## Verification
- [x] Start HTTP server and verify `tools/call` response shape is Go-safe.
- [ ] Validate from IDE MCP client: `tools/call` no longer crashes/unmarshals.

