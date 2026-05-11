# Change Log - 20260428-182350-mcp-startup-fetch-fix

Based on change-log from `change-logs/20260428-165217-windows-service-tls-hardening.md`.

## Semantic Changes
- `fix(discovery):` require valid CCT `/status` JSON signature before marking server healthy.
- `fix(setup):` select active base URL via `/status` signature to avoid frontend false positives.
- `fix(mcp-http):` return MCP JSON-RPC payloads for `initialize`, `ping`, `tools/list`, and `tools/call`.
- `chore(config):` add `CCT_DASHBOARD_API_KEY` in `.env` for local deterministic startup/auth alignment.
- `chore(context):` update `WORKING-CONTEXT.md` with new runtime truth and queue.

## Files Updated
- `scripts/server/discover.py`
- `scripts/server/setup.py`
- `src/main.py`
- `.env`
- `WORKING-CONTEXT.md`

## Verification Evidence
- `python -m py_compile scripts/server/discover.py scripts/server/setup.py src/main.py` -> PASS.
- `python scripts/server/setup.py --skip-deps` -> generated config URL on `:8000`.
- Authenticated JSON-RPC call `tools/list` -> HTTP 200, `result.tools` present, count=20.
