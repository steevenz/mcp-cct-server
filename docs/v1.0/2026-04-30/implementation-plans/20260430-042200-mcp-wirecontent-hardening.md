# Implementation Plan - 20260430-042200-mcp-wirecontent-hardening

Based on plan from `docs/v1.0/2026-04-30/implementation-plans/20260430-040100-mcp-tools-call-wirecontent.md`.

## Objective
- Prevent recurring MCP client decode failures by hardening `tools/call` response normalization and reducing accidental information leakage.

## Changes
- `tools/call` response normalization:
  - Recursively flatten tool outputs into a single `content` list.
  - Enforce `content[i].type` is always a non-empty string (fallback to `text`).
- Authentication check:
  - Use constant-time comparison for `X-API-KEY`.
- `/status` response:
  - Stop returning raw exception strings inside `global_usage`.

## Verification
- Launch HTTP server and call `tools/call`.
- Assert `result.content` is a flat list of objects and each item has string `type`.
- Assert `/status` does not include `global_usage.error`.

