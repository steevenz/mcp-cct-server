# Implementation Plan - 20260428-194800-npm-wrapper-process-manager

Based on plan from `implementation-plans/20260428-182350-mcp-startup-fetch-fix.md`.

## System Context
- Subsystem: npm DX wrapper for Python MCP server startup and lifecycle.
- `prd_id`: `20260428-194800-npm-wrapper-process-manager`.
- Goal: allow IDEs to summon CCT MCP via `npx cct-mcp` (alias: `cct-server`) with safe STDIO behavior.

## Design Decisions
- Wrapper entrypoint at `scripts/server/js/index.js` with shebang `#!/usr/bin/env node`.
- Project root resolved from `__dirname` (`scripts/server/js` -> root).
- Auto-bootstrap creates `venv` and installs `requirements.txt` only when `venv` is missing.
- All wrapper/setup logs are written to `stderr`; stdout remains reserved for MCP JSON-RPC stream.
- Runtime always forces `CCT_TRANSPORT=stdio` for IDE contract consistency.
- Child process lifecycle is managed with `SIGINT`, `SIGTERM`, and `exit` hooks to prevent orphan processes.

## Security and Stability
- No secrets printed to stdout.
- Setup command output is captured and redirected to stderr.
- Child process is terminated explicitly on wrapper shutdown.

## Rollback Strategy
1. Remove `scripts/server/js/index.js`.
2. Revert `package.json` bin mapping.
3. Continue using Python launch path (`.venv/Scripts/python src/main.py` or equivalent).
