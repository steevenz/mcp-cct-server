---
title: "CCT Server Settings & Environment Schema"
tags: ["core", "config", "environment", "setup"]
keywords: ["settings", "env", "configuration", "transport", "sessions"]
related: ["context.md"]
importance: 70
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T00:00:00Z"
---

## Raw Concept

**Task:**
Standardize system-wide configuration via environment variables and dataclasses to ensure predictable cross-platform deployments.

**Files:**
- `src/core/config.py` (Parser & Dataclass)
- `src/core/constants.py` (Hardcoded Defaults)

**Flow:**
1. `load_settings()` reads `os.getenv`.
2. Sanitizers/Parsers validate types and ranges.
3. Frozen `Settings` dataclass is injected into the server lifecycle.

## Narrative

### Structure
The configuration layer is split between **Constants** (internal guardrails) and **Settings** (externally tunable parameters). This separation ensures that sensitive system limits (like the 200-thought hard cap) cannot be accidentally overridden by environmental configuration, while deployment details remain flexible.

### Rules
1. **Naming Convention**: All environment variables are prefixed with `CCT_`.
2. **Immutability**: Once loaded, the `Settings` object is a frozen dataclass.
3. **Range Validation**: Ports must be 1-65535; Session counts must be 1-100,000.

### Configuration Table
| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `CCT_SERVER_NAME` | `cct-mcp-server` | User-facing identifier for the MCP server. |
| `CCT_TRANSPORT` | `stdio` | Communication layer (`stdio` or `http`). |
| `CCT_HOST` | `0.0.0.0` | Binding host for HTTP mode. |
| `CCT_PORT` | `8000` | Port for HTTP mode. |
| `CCT_MAX_SESSIONS` | `128` | Max concurrent cognitive pipelines allowed. |

## Facts
- **transport_agnostic**: The system logic is decoupled from the transport layer. [architecture]
- **fail_fast_validation**: Invalid port or session numbers raise `ValueError` immediately on startup. [convention]
- **token_budget_tuning**: Default context strategy is `summarized` to optimize for Claude's attention window. [economy]
