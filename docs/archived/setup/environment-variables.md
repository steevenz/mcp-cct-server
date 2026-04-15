---
title: "Setup: Environment Variables"
tags: ["setup", "config", "env-vars"]
keywords: ["CCT_LOG_LEVEL", "CCT_MAX_THOUGHTS", "CCT_MAX_SESSIONS", "overrides"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Environment Variables

## Overview
The CCT MCP Server utilizes environment variables for secure and flexible configuration. All core settings can be tuned via the `CCT_` prefix, allowing for clean separation between code and environment-specific constraints.

## Mandatory Variables
- **`OPENAI_API_KEY`** (or equivalent provider): Required for engine execution.
- **`CCT_DB_PATH`**: Path to the SQLite persistence layer. Defaults to `./data/cct_memory.db`.

## Configuration Overrides
| Variable | Default | Description |
| :--- | :--- | :--- |
| `CCT_LOG_LEVEL` | `INFO` | Standard logging levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `CCT_MAX_THOUGHTS` | `200` | Hard cap on reasoning steps per mission branch. |
| `CCT_MAX_SESSIONS` | `128` | Maximum concurrent cognitive sessions. |
| `CCT_FORCE_HITL` | `false` | If `true`, forces Phase 6.5 human clearance for all missions. |

## Usage
Variables should be set in the host environment or defined in a `.env` file within the project root. The `Core/Configuration` module parses these values at startup, enforcing strict type validation via Pydantic.

## Related Topics
- [./context.md](./context.md)
- [../core/configuration/context.md](../core/configuration/context.md)
