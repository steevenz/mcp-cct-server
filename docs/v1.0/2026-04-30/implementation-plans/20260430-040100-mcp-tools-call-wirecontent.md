# Implementation Plan - 20260430-040100-mcp-tools-call-wirecontent

Based on plan from `docs/v1.0/2026-04-28/implementation-plans/20260428-220000-multi-ide-shared-proxy.md`.

## Objective
- Fix MCP `tools/call` HTTP JSON-RPC responses so `result.content` is always a flat `wireContent[]` list to satisfy strict Go clients.

## Current Bug
- Some clients fail decoding `tools/call` with an error similar to:
  - `json: cannot unmarshal [...] into ... wireContent`
- Root cause: `src/main.py` built `result.content` by iterating the raw FastMCP return value without normalizing its shape, producing nested arrays and/or non-wireContent objects.

## Plan
- Add a normalization layer in `src/main.py` for the `tools/call` method:
  - Accept multiple upstream shapes (`CallToolResult` object, dict, list/tuple).
  - Flatten one nesting level.
  - Convert any non-wireContent payloads to `{ "type": "text", "text": "<json>" }`.
  - Preserve `isError` where available.
- Fix any remaining call sites that invoke `PolicyService.select_pipeline()` without the required `complexity` argument.

## Verification
- Launch HTTP server and call `POST /cognitive-api/v1/sync` with a `tools/call` request.
- Assert:
  - Response is valid JSON-RPC.
  - `result.content` is an array.
  - Each element is an object with a string `type` field (e.g., `text`).

