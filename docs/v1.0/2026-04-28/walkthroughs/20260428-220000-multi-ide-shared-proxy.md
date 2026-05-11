# Walkthrough - 20260428-220000-multi-ide-shared-proxy

Based on walkthrough from `walkthroughs/20260428-194800-npm-wrapper-process-manager.md`.

## Flow
1. IDE launches `npx ... cct-mcp` as an MCP STDIO server.
2. Wrapper ensures `venv/` exists (bootstraps if missing).
3. Wrapper loads `CCT_DASHBOARD_API_KEY` from `.env` or env.
4. Wrapper finds/starts a shared CCT backend server (HTTP/SSE) and validates auth.
5. Wrapper reads JSON-RPC lines from stdin and forwards them to `/cognitive-api/v1/sync`.
6. Wrapper writes JSON-RPC responses back to stdout.
7. Wrapper tracks shared backend refCount in `database/config/cct_shared_server.json`.
