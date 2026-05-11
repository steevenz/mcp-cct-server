# Walkthrough - 20260430-040100-mcp-tools-call-wirecontent

Based on walkthrough from `docs/v1.0/2026-04-28/walkthroughs/20260428-220000-multi-ide-shared-proxy.md`.

## Symptom
- IDE/Go MCP client fails on `tools/call` with an unmarshal error complaining `content` is not `wireContent[]`.

## Root Cause
- `src/main.py` constructed `result.content` by iterating the raw FastMCP call return value without shape normalization.
- Depending on FastMCP version/tool return types, this produced nested arrays and/or non-wireContent objects inside `content`.

## Fix
- Added normalization for `tools/call` results in `src/main.py`:
  - flatten one level
  - coerce all items to valid wire content objects
  - preserve `isError` when available
- Fixed `select_pipeline` call sites that previously omitted `complexity` to prevent adjacent runtime errors.

## Verification
- Started HTTP server and executed `POST /cognitive-api/v1/sync` with `tools/call`.
- Confirmed `result.content` is a list of objects with `type` strings (e.g. `text`).

