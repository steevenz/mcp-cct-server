# Change Log - 20260430-040100-mcp-tools-call-wirecontent

Based on change log from `docs/v1.0/2026-04-28/change-logs/20260428-220000-multi-ide-shared-proxy.md`.

## Fixed
- `tools/call` now returns `result.content` as a flat `wireContent[]` list to satisfy strict MCP clients (Go decode).

## Changed
- Normalized FastMCP tool-call return shapes in `src/main.py` (object/dict/list/tuple handling).
- Fixed pipeline selection call sites to pass required `complexity`.

## Files
- `src/main.py`
- `src/core/services/orchestration/routing.py`
- `src/tools/session.py`
- `.agents/state.yaml`
- `.agents/contexts/working.md`
- `.agents/contexts/soul.md`

