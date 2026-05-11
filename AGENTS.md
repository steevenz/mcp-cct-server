# AGENTS.md - OpenCode Guidance

## OpenCode Session Orchestration
OpenCode is our framework for **Multi-Agent Collaborative Reasoning**. It uses the CCT MCP server as a **Cognitive Shared Bus**.

### Core Orchestration Rules:
1. **Shared Memory**: All agents in an OpenCode session MUST use the same `session_id` to share thought history.
2. **Role Attribution**: Use the `metadata` field in `start_thinking` to define the agent's role (e.g., `role: "architect"`, `role: "security-auditor"`).
3. **Cross-Model Verification**: Leverage the expanded LLM support (DeepSeek, OpenRouter) for cross-model critique using the `Actor-Critic` pattern.
4. **Context Hygiene**: Periodically use `consolidate_thinking` to prune irrelevant thoughts and keep the context lean.

## Supported LLM Providers (v1.1.0)
The CCT MCP Server now supports a wider range of providers for both main reasoning and critic roles:

| Provider | Config Key | Description |
|----------|------------|-------------|
| **Google Gemini** | `GEMINI_API_KEY` | Recommended for speed/cost balance |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | Best for complex architectural reasoning |
| **OpenAI GPT** | `OPENAI_API_KEY` | Industry standard reliability |
| **OpenRouter** | `OPENROUTER_API_KEY` | Access to 100+ models (Llama 3, Qwen, etc.) |
| **DeepSeek** | `DEEPSEEK_API_KEY` | High-quality reasoning for technical tasks |
| **NineRouter** | `NINEROUTER_API_KEY` | Specialized enterprise routing |
| **Ollama** | `OLLAMA_BASE_URL` | Local models (Llama 3, Mistral, etc.) |

## Core Commands
- Run server: `npm run cct-server` (defaults to SSE on :8001)
- Per-IDE launch:
  - `npm run cct-server:vscode` (STDIO :8010)
  - `npm run cct-server:cursor` (STDIO :8011)
  - `npm run cct-server:jetbrains` (SSE :8001)
  - `npm run cct-server:windsurf` (SSE :8002)
  - `npm run cct-server:copilot` (SSE :8003)
- Benchmark: `npm run cct-bench[:quick|:stress]`

## Multi-IDE / Multi-LLM Architecture
- **CLI args**: `--ide <name> --transport <stdio|sse> --port <port>`
- **Connection Registry**: `database/config/mcp_server_registry.json` tracks all active IDE/LLM connections
- **Transport Pool**: Each port+transport combo spawns an isolated Python server process
- **LLM Isolation**: Each request carries `X-IDE-ORIGIN` / `X-LLM-INSTANCE-ID` headers for session scoping
- **Memory scoping**: `MemoryManager.list_sessions()` and `get_aggregate_usage()` filter by `llm_instance_id`

## Configuration
- Auth keys: `.env` (`CCT_CLIENT_API_KEY`, `CCT_BOOTSTRAP_API_KEY`)
- IDE configs: `database/config/mcp_client_multi_ide.json`
- STDIO: `database/config/mcp_client_stdio.json` (VSCode, Cursor)
- SSE: `database/config/mcp_client_sse.json` (JetBrains, Copilot, Windsurf)

## Testing & Benchmarking
- No formal test suite; benchmark tools in `tests/benchmarks/`
- Concurrency benchmark: `npm run cct-bench -- --clients=5 --requests=50`
- Output: `tests/benchmarks/concurrency_report_*.json`
- Tool latency baseline: `tests/benchmarks/tool_latency_baseline.json`

## Critical Paths
1. Entry: `./scripts/server/js/index.js` (Node wrapper)
2. Backend: `src/main.py` (FastAPI + FastMCP)
3. Auth: `src/core/services/auth/handshake.py`
4. Memory: `src/engines/memory/manager.py` (LLM-scoped)
5. Config: `src/core/config.py`

## Safety Checks
- Validate `CCT_PORT` matches config before startup
- Check API keys exist in `.env`
- Verify `database/config/mcp_server_registry.json` is writable

## Common Pitfalls
- Race condition in auth handshake (handshake.py lines 308-310) - fixed with atomic transaction + RETURNING
- Unbounded memory in `get_session_history` - now paginated with `limit` param
- LLM collision: each IDE must use unique `--ide` name for proper session isolation
- STDIO mode: only one IDE per port; use SSE for shared access
- **Tool descriptions are LLM-friendly**: First word in docstring = action hint (START, NEXT, RETRIEVE, BREAK DOWN, etc.)
- **Resources available at**: `resources/list` and `resources/read` with `cct://` URI scheme
- **Prompts available at**: `prompts/list` and `prompts/get` with 5 built-in thinking templates

## First Debug Steps
1. Check registry: `database/config/mcp_server_registry.json`
2. Verify server: `curl http://localhost:$CCT_PORT/status`
3. List connected LLMs: `curl http://localhost:$CCT_PORT/status/llms`
4. Per-LLM detail: `curl http://localhost:$CCT_PORT/status/llm/<instance_id>`
5. List MCP resources: `curl -X POST http://localhost:$CCT_PORT/cognitive-api/v1/sync -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"resources/list"}'`
6. List MCP prompts: `curl -X POST http://localhost:$CCT_PORT/cognitive-api/v1/sync -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"prompts/list"}'`

## Style
- i18n messages: `src/core/localization/i18n/*.json`
- Config structure: `database/config/*.json`
- Follow existing tool registration pattern in `src/tools/simplified.py`
- New tools must accept `_llm_instance_id` and `_ide_origin` params (injected by MCP router)
