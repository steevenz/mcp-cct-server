---
title: "API Reference: MCP Tools Mapping"
tags: ["api", "mcp", "tools", "v5.0"]
keywords: ["methods", "parameters", "session", "cognition"]
importance: 100
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# API Reference: The CCT Interface

All public APIs are exposed as MCP tools via `FastMCP` using the `@mcp.tool()` decorator in the `src/tools/` sub-packages.

## Conventions

- **Response Format**: All tool responses are JSON objects.
- **Status Codes**: 
  - `success`: Operation completed.
  - `error`: Error encountered, reason provided in `error` field.
- **Constraints**: 
  - `session_id`: Mandatory for all stateful thinking steps.
  - `SECURITY C1`: Rigid char limits for all free-text inputs.

---

## 1. Session Management (`session_tools.py`)

### `start_cct_session`
Initializes the cognitive mission and selects the adaptive pipeline.
- **Parameters**: `problem_statement`, `profile`.
- **Primary Output**: `session_id`, `dynamic_pipeline`.

### `list_cct_sessions`
Lists active and historical session IDs from memory.

### `get_thinking_path`
Retrieves the full chronological history of a session for forensic analysis.

---

## 2. Cognitive Interaction (`cognitive_tools.py`)

### `cct_think_step`
**[PRIMITIVE]** Executes a single atomic reasoning step.
- **Parameters**: `session_id`, `thought_content`, `strategy`, `thought_type`, etc.

#### `actor_critic_dialog`
Triggers a bipartite debate between a core architect and a singular critic lens.
- **Inputs**: `session_id`, `target_thought_id`, `critic_persona`.

#### `council_of_critics_debate` [v5.1]
Convenes a multi-agent specialized console to stress-test a reasoning node from multiple architectural angles.
- **Inputs**: `session_id`, `target_thought_id`, `specialized_personas` (List).
- **Behavior**: Parallel evaluative branching + Integrative Synthesis.

### `cct_log_failure`
**[ANTI-PATTERN]** Records a logical or strategic failure to the global database.

---

## 3. Analysis & Export (`export_tools.py`)

### `analyze_session`
Computes quality scores (Clarity, Coherence, Novelty) across the session.

## Related Topics
- [./context.md](./context.md)
- [./engine-system.md](./engine-system.md)
