# Walkthrough - 20260428-182350-mcp-startup-fetch-fix

Based on walkthrough from `walkthroughs/20260428-165217-windows-service-tls-hardening.md`.

## High-Level Flow
1. Setup scans candidate localhost ports.
2. Candidate is accepted only when `GET /status` returns JSON with `server` and `transport` keys.
3. Setup writes `database/config/mcp_client_sse.json` with selected URL and `X-API-KEY` header.
4. IDE MCP client calls `POST /cognitive-api/v1/sync` with JSON-RPC method `tools/list`.
5. Server validates API key, dispatches method, awaits `mcp_instance.list_tools()`, and returns JSON-RPC `result.tools`.

## Verification Matrix
- Rebuild config:
  - `python scripts/server/setup.py --skip-deps`
- Start API with deterministic key:
  - `$env:CCT_DASHBOARD_API_KEY='cct-secret-token-2026'; .\.venv\Scripts\python.exe src\main.py`
- Verify MCP tools list:
  - `python -c "import json,httpx;from pathlib import Path;c=json.loads(Path('database/config/mcp_client_sse.json').read_text());s=c['mcpServers']['Creative Critical Thinking'];r=httpx.post(s['url'],headers=s['headers'],json={'jsonrpc':'2.0','id':1,'method':'tools/list','params':{}},timeout=10.0);print(r.status_code,len(r.json().get('result',{}).get('tools',[])))"`
- Expected:
  - status `200`
  - JSON with keys `jsonrpc,id,result`
  - `result.tools` length > 0

Status: Ready for review
