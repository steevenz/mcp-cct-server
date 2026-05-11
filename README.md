# CCT MCP Server — Cognitive Computing Toolkit

**Version**: 1.1.0 | **Multi-IDE / Multi-LLM Architecture** | **Offline-First with Google Gemma**

A production-grade MCP (Model Context Protocol) server providing advanced cognitive computing capabilities — thinking patterns, session orchestration, adversarial review, and memory persistence — for multiple IDEs and LLM providers concurrently. **Runs 100% offline** with embedded Google Gemma models. Online LLM optional for quality boost only.
---

## Quick Start (One-Click Setup)

```powershell
# Windows (PowerShell) - Recommended
# This installs dependencies, downloads models, and registers the server in your IDEs automatically.
./scripts/setup/setup.ps1 -Download -Register -Run
```

```bash
# Linux / macOS (bash)
./scripts/setup/setup.sh --download --register --run
```

---

## Commands

### Setup & Management
| Command | Description |
|---------|-------------|
| `./scripts/setup/setup.ps1 -Download` | Download Gemma models (1.5GB + 5GB) |
| `./scripts/setup/setup.ps1 -Register` | Auto-register in Claude, Cursor, Windsurf |
| `./scripts/setup/setup.ps1 -InstallService` | Install as Windows Background Service |
| `npm run cct-server` | Start the shared server (SSE mode, port 8010) |

### Per-IDE Launch (Legacy/Direct)
| Command | Transport | Port | IDE |
|---------|-----------|------|-----|
| `npm run cct-server:vscode` | STDIO | 8010 | VSCode |
| `npm run cct-server:cursor` | STDIO | 8011 | Cursor |
| `npm run cct-server:jetbrains` | SSE | 8001 | JetBrains |
| `npm run cct-server:windsurf` | SSE | 8002 | Windsurf |
| `npm run cct-server:copilot` | SSE | 8003 | Copilot |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  VSCode (STDIO)  │  Cursor (STDIO)  │  JetBrains (SSE)
└────────┬─────────┘──────┬───────────┘──────┬────────┘
         │                │                  │
         ▼                ▼                  ▼
┌─────────────────────────────────────────────────────┐
│              NPX Wrapper (scripts/server/js/)         │
│  ┌─────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │CLI Parser│  │Conn Registry  │  │Auth Handshake  │  │
│  └─────────┘  └───────────────┘  └────────────────┘  │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│            Python FastAPI + FastMCP (port 8001)       │
│  ┌─────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ Auth    │  │ MemoryManager  │  │ MCP Router     │  │
│  │ Service │  │ (LLM-scoped)  │  │ (header-aware)  │  │
│  └─────────┘  └───────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────┘
```

See [docs/architecture/multi-ide-architecture.md](docs/architecture/multi-ide-architecture.md) for complete design details.

---

## Features

### OpenCode Framework
OpenCode is our advanced framework for **Multi-Agent Collaborative Reasoning**. It transforms the CCT MCP server into a **Cognitive Shared Bus** where multiple agents can:
- **Share a Global Thought Space**: Agents (Architect, Coder, Auditor) share a unified session history.
- **Cross-Model Validation**: Use different LLMs (e.g., Claude for logic, DeepSeek for review) in the same session.
- **Role-Based Orchestration**: Metadata-driven task attribution for complex multi-step missions.

### Core Cognitive Engine
- **Sequential Thinking**: Step-by-step reasoning with revision and branching.
- **Tree of Thoughts**: Multi-branch exploration with comparison and pruning.
- **Adversarial Review**: Cross-model critique and security clearance.
- **Memory Persistence**: SQLite-backed session and thought storage.
- **Pattern Detection**: Golden thinking patterns and anti-pattern identification.

---

## 🧱 Reasoning Engine & Symbiotic Readiness (v5.0)

CCT MCP is not just an interface; it is a **Mission-Critical Cognitive OS**. Below is the verified readiness status of our core reasoning and symbiosis modules.

### Part 1: Reasoning Engine Readiness (Checklist v5.0)

| ID | Feature | Status | Codebase Evidence |
|----|---------|--------|-------------------|
| 1 | Core Architecture | ✅ VERIFIED | IntelligenceRouter (Dynamic Routing), ScoringService (Validation), ReasoningTraceID (Observability). |
| 0x1 | Task Decomposition | ✅ VERIFIED | `src/tools/engineering.py` -> decompose_thinking. Supports execution graphs. |
| 0x2 | Critical Analysis | ✅ VERIFIED | `src/tools/simplified.py` -> critical_analyze. Activates actor-critic loop. |
| 0x3 | Planning | ✅ VERIFIED | `src/tools/simplified.py` -> generate_plan. Uses REWOO strategy. |
| 0x4 | Verification | ✅ VERIFIED | `src/tools/simplified.py` -> verify_output. Consistency check via ScoringService. |
| 0x5 | Reflection | ✅ VERIFIED | `src/tools/simplified.py` -> reflect_reasoning. Meta-cognitive audit session. |
| 0x6 | Decision Matrix | ✅ VERIFIED | `src/tools/simplified.py` -> evaluate_options. Scoring & Tradeoff analysis. |
| 8 | Coding Intelligence | ✅ VERIFIED | Specialized pipelines: review_architecture, review_security, review_scalability. |
| 10 | Failure Handling | ✅ VERIFIED | IntelligenceRouter utilizes UNCONVENTIONAL_PIVOT for reasoning recovery. |

### Part 2: Symbiotic CCT Readiness — Cognitive Symbiosis

| Component | Level | Symbiosis Mechanism |
|-----------|-------|---------------------|
| Thinking Profile | ✅ ACTIVE | `configs/identity/mindset.md` defines your "Architect DNA". AI follows system-enforced guardrails rather than just roleplaying. |
| Golden Thinking | ✅ ACTIVE | `is_pattern_candidate` in ScoringService detects high-coherence reasoning (Coherence > 0.9) and archives it to `docs/context-tree/Thinking-Patterns`. |
| Pattern Extraction | ✅ ACTIVE | POST_MISSION_LEARNING strategy in PolicyService automatically runs after complex pipelines to "absorb" your problem-solving methods. |
| Cognitive Identity | ✅ LOCKED | IdentityRail in `src/modes/base.py` prevents style hallucination and maintains consistency with your engineering philosophy. |
| Reflection Engine | ✅ ACTIVE | IncrementalSessionAnalyzer periodically distills noisy chat logs into "High-Density Cognition" artifacts. |

---

## 🛡️ Final Flow Check (The Symbiotic Loop)

1. **Input**: Complex problem ingestion.
2. **Routing**: IntelligenceRouter selects Gemma (Local) as default for privacy and cost-efficiency.
3. **Reasoning**: EnhancedThought execution with ReasoningTraceID.
4. **Verification**: Every step is validated via ConfidenceScore & ContradictionFlags.
5. **Learning**: High-quality reasoning triggers the `is_thinking_pattern` flag.
6. **Evolution**: Background ConsolidationCycle updates `learned_identity.json` with new cognitive insights.

**Status: MISSION CRITICAL READY 🧱🔥🧠**

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture/multi-ide-architecture.md) | System design and multi-tenant isolation |
| [Setup Guide](docs/guides/multi-ide-setup.md) | Per-IDE configuration and launch |
| [Feature Spec](docs/features/multi-ide-support.md) | Capabilities and API changes |
| [Upgrade Guide](docs/versions/v1.1.0/multi-ide-upgrade.md) | Migration from v1.0.0 |
| [AGENTS.md](AGENTS.md) | OpenCode session guidance |

---

## Configuration

All configuration lives under `database/config/`:

| File | Purpose |
|------|---------|
| `mcp_client_multi_ide.json` | Central multi-IDE configuration |
| `mcp_client_stdio.json` | STDIO transport settings |
| `mcp_client_sse.json` | SSE transport settings |
| `mcp_server_registry.json` | Live connection registry |

Environment variables (`.env` or process):

| Variable | Required | Description |
|----------|----------|-------------|
| `CCT_BOOTSTRAP_API_KEY` | Yes | Bootstrap/shared API key |
| `CCT_CLIENT_API_KEY` | No | Per-instance client key |
| `CCT_PORT` | No | Server port (default: 8001) |
| `CCT_TRANSPORT` | No | Transport mode (stdio/sse) |
| `CCT_HOST` | No | Bind address (default: 127.0.0.1) |
| `CCT_IDE` | No | IDE identifier |

---

## Monitoring

```bash
# Server health
curl http://localhost:8001/health

# Full status with LLM registry
curl http://localhost:8001/status

# Connected LLMs
curl http://localhost:8001/status/llms

# Per-LLM detail
curl http://localhost:8001/status/llm/vscode

# List MCP resources (thinking patterns, sessions)
curl -X POST http://localhost:8001/cognitive-api/v1/sync \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"resources/list"}'

# List MCP prompts (thinking templates)
curl -X POST http://localhost:8001/cognitive-api/v1/sync \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"prompts/list"}'

# Initialize MCP session (returns Mcp-Session-Id)
curl -X POST http://localhost:8001/cognitive-api/v1/sync \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25"}}'
```

---

## MCP Features

The server implements MCP spec (v2025-11-25):

| Feature | Methods | Description |
|---------|---------|-------------|
| **Tools** (11) | `tools/list`, `tools/call` | start_thinking, continue_thinking, recall_thinking, etc. |
| **Resources** | `resources/list`, `resources/read` | `cct://patterns/golden/`, `cct://sessions/`, `cct://patterns/list` |
| **Prompts** (5) | `prompts/list`, `prompts/get` | critical_review, architectural_decomposition, security_audit, debug_root_cause, decision_framework |
| **Session Mgmt** | `Mcp-Session-Id` header | Streamable HTTP compliant sessions |
| **Lifecycle** | `initialize` → `notifications/initialized` | Capability negotiation |

### Capabilities
```json
{
  "tools": {"listChanged": true},
  "resources": {"listChanged": true},
  "prompts": {"listChanged": true}
}
```

---

## Development

### Project Structure
```
src/
├── main.py              # FastAPI + FastMCP entry point
├── core/                # Configuration, security, auth
│   ├── config.py        # Environment-based settings
│   ├── security.py      # Token handling, sanitization
│   ├── rate_limiter.py  # Sliding window rate limiter
│   └── services/auth/   # Authentication service
├── resources/           # MCP Resources (patterns, sessions)
├── prompts/             # MCP Prompts (thinking templates)
├── engines/
│   └── memory/          # MemoryManager + ConsolidationEngine
├── tools/               # MCP tool registration
├── modes/               # Engine registry
└── utils/               # Utilities
scripts/server/js/       # NPX wrapper
database/                # SQLite, config, metadata
tests/benchmarks/        # Concurrency benchmarks
docs/                    # Architecture, guides, features
```

---

## Token Economy

CCT MCP saves **~90% tokens** vs in-context thinking by storing thought history in SQLite instead of conversation context.

### Per-Session Comparison (10 thinking steps):

```
Without MCP:
  Step 1: context(3K) + thought(500) = 3,500 tokens
  Step 5: context(5K) + thought(500) = 5,500 tokens
  Step 10: context(8K) + thought(500) = 8,500 tokens
  Total: ~55,000 tokens (accumulated context growth)

With CCT MCP:
  tools/list (once):    ~2,600 tokens
  Per tool call:        ~300 tokens × 10 = 3,000 tokens
  Total:                ~5,600 tokens (constant context)

Savings: ~49,400 tokens (90% reduction per session)
```

### Why So Efficient?

| Factor | Without MCP | With CCT MCP |
|--------|------------|--------------|
| Thought storage | Conversation context | SQLite database |
| Context growth | O(n) per step | O(1) constant |
| Pattern reuse | Must regenerate | Injected automatically |
| Past session recall | Lost after conversation | `recall_thinking` retrieves |
| Tool descriptions | N/A | ~2,600 tokens (one-time) |

### Tool Description Optimization

All 14 tools have been optimized for token economy:
- Action-first descriptions: `START HERE`, `NEXT STEP`, `FRAME`, `DIVERGE`, `RETRIEVE`
- Average **745 chars** per tool (down from 1,037)
- Concise parameter docs — enough for LLM to decide, not verbose tutorials

---

## Offline LLM: Google Gemma Embedded

The server includes **embedded Google Gemma models** via `llama-cpp-python` for full offline operation. **Zero cloud API keys required on the server.** Online LLMs are used only for optional quality boost when the user explicitly requests it.

### Why Google Gemma?

| Model | RAM | Speed (CPU) | Why Selected |
|-------|-----|-------------|--------------|
| **Gemma 2 2B** Q4_K_M | **~1.2 GB** | ~40 tok/s | **Lowest RAM** — runs on any laptop, even with 8GB RAM |
| Gemma 2 9B Q4_K_M | ~5.5 GB | ~12 tok/s | Reasoning-capable fallback, fits in 8-16GB RAM |
| Qwen 2.5 1.5B | ~1.5 GB | ~30 tok/s | Higher RAM than Gemma 2B, lower quality |
| Llama 3.2 3B | ~2.0 GB | ~25 tok/s | 2x RAM of Gemma 2B, same quality tier |
| Phi-3 Mini 3.8B | ~2.5 GB | ~20 tok/s | 2x RAM of Gemma 2B, needs more CPU |

**Gemma 2 2B was selected as default because:**

1. **Lowest RAM footprint** (~1.2 GB) — runs on ANY machine, even low-end laptops
2. **Google's instruct tuning** — excellent for classification, extraction, and structured output tasks
3. **Efficient tokenizer** — optimized for technical/code content
4. **Apache 2.0 license** — free for commercial use
5. **Proven quality** — Gemma 2 series benchmarks show competitive performance vs 2-3x larger models
6. **Automatic download** — first-run download from HuggingFace, zero manual setup

### 3-Tier Architecture (Local-First, Sampling-Escalate)

```
TIER 1: Gemma 2B  (~1.2 GB) — ALWAYS FREE, always available
  Tasks: pattern extraction, classification, quality scoring, bias detection

TIER 2: Gemma 9B  (~5.5 GB) — INCLUDED, reasoning capable
  Tasks: deep reasoning, clustering, behavior analysis, FALLBACK reasoning

TIER 3: Client LLM via MCP Sampling — NO API KEY NEEDED
  Uses the requesting LLM (Claude/GPT/Gemini from IDE) for deep/creative thinking
  Biaya ditanggung user (via IDE subscription)
```

### No Cloud API Keys Required

The server uses `SmartLLMService` which routes ALL thinking engine calls:
1. **Gemma 9B available?** → Use it (free, private, always on)
2. **User requested quality boost?** → Use online API (if configured)
3. **No online API?** → Always use Gemma
4. **No local model?** → Fallback to online (last resort)

This applies to ALL cognitive engines: Actor-Critic, Council of Critics, Multi-Agent Fusion, Fusion Orchestrator. **Zero mandatory online dependency.**

### Install Models

The easiest way is using the setup script:
```bash
./scripts/setup/setup.ps1 -Download
```

Or manual download if you prefer:
```bash
pip install llama-cpp-python
huggingface-cli download bartowski/gemma-2-2b-it-GGUF --include '*-Q4_K_M.gguf' --local-dir models/
```

**MIT License** — Copyright (c) 2026 Steeven Andrian
