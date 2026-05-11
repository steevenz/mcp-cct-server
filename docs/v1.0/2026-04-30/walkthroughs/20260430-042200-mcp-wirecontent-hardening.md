# Walkthrough - 20260430-042200-mcp-wirecontent-hardening

Based on walkthrough from `docs/v1.0/2026-04-30/walkthroughs/20260430-040100-mcp-tools-call-wirecontent.md`.

## Why this patch exists
- Some MCP clients (notably Go implementations) strictly decode `tools/call` results and require `result.content` to be a flat `wireContent[]`.

## What changed
- `src/main.py` now:
  - Recursively flattens any nested lists/tuples returned from tool handlers.
  - Coerces invalid/missing `type` into `text`.
  - Uses constant-time API key comparison.
  - Stops emitting raw exception strings in `/status` payloads.

## How to verify
- Run the server in HTTP mode and call `POST /cognitive-api/v1/sync` with `tools/call`.
- Confirm:
  - `result.content` is a list
  - each item is an object with string `type`
  - `/status.global_usage` has no `error` field

