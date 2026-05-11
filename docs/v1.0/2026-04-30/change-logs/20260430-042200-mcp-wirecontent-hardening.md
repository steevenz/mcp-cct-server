# Change Log - 20260430-042200-mcp-wirecontent-hardening

Based on change log from `docs/v1.0/2026-04-30/change-logs/20260430-040100-mcp-tools-call-wirecontent.md`.

## Fixed
- Go/strict MCP clients no longer fail decoding `tools/call` due to nested `content` arrays or non-string `type` fields.

## Security
- API key comparison uses constant-time comparison.
- `/status` no longer includes raw exception text in response payload.

## Files
- `src/main.py`
- `.agents/state.yaml`
- `.agents/contexts/working.md`

