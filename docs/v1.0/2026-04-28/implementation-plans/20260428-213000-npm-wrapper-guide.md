# Implementation Plan - 20260428-213000-npm-wrapper-guide

Based on plan from `implementation-plans/20260428-194800-npm-wrapper-process-manager.md`.

## System Context
- Subsystem: developer documentation for npm/npx wrapper execution.
- `prd_id`: `20260428-213000-npm-wrapper-guide`.
- Goal: provide step-by-step guide for running `scripts/server/js/index.js` safely with npm/npx, including verification and troubleshooting.

## Scope
- Add a dedicated guide in `docs/guides/` focused on STDIO wrapper usage.
- Ensure examples cover both repo-root invocation and absolute-path `npx --package` invocation.

## Security and DX constraints
- Document stdout/stderr separation clearly to avoid IDE MCP crashes.
- Document required `.env` variables, especially `CCT_DASHBOARD_API_KEY`.

## Rollback Strategy
- Remove the new guide file if docs need to be reverted.
- No runtime behavior rollback required.
