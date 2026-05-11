# Tasks - 20260430-042200-mcp-wirecontent-hardening

Based on tasks from `docs/v1.0/2026-04-30/tasks/20260430-040100-mcp-tools-call-wirecontent.md`.

## Patch
- [x] Enforce `X-API-KEY` comparison uses constant-time compare.
- [x] Harden `tools/call` normalization with recursive flattening.
- [x] Ensure `wireContent.type` is always a non-empty string (fallback to `text`).
- [x] Remove raw exception strings from `/status` `global_usage`.

## Tests
- [x] HTTP probe: `tools/call` returns flat `content[]` with string `type`.
- [x] HTTP probe: `/status` does not contain `global_usage.error`.

