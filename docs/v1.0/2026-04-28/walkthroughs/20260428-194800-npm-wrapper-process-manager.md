# Walkthrough - 20260428-194800-npm-wrapper-process-manager

Based on walkthrough from `walkthroughs/20260428-182350-mcp-startup-fetch-fix.md`.

## Runtime Flow
1. User executes `npx cct-mcp` (or alias `npx cct-server`).
2. Node wrapper resolves project root from `scripts/server/js/index.js`.
3. Wrapper checks `venv` directory.
4. If missing, wrapper synchronously runs:
   - `python -m venv venv`
   - `venv python -m pip install -r requirements.txt`
5. Wrapper starts Python with `-m src.main` and `CCT_TRANSPORT=stdio`.
6. Wrapper forwards child stdio directly and only writes internal logs to stderr.
7. On wrapper termination (`SIGINT`, `SIGTERM`, `exit`), wrapper kills child process explicitly.

## Expected Outcome
- IDE sees MCP JSON-RPC only on stdout.
- Setup and diagnostic text does not contaminate protocol stream.
- No orphaned Python process remains after IDE disconnects.
