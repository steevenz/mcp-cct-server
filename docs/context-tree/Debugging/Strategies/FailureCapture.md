---
title: "Self-Debugging: Failure Capture"
tags: ["debugging", "telemetry", "snapshots"]
keywords: ["error-logs", "tool-sequence", "state-snapshot"]
related: ["./context.md"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Record the failure precisely before attempting recovery.
**Files:** `src/core/models/domain.py` (EnhancedThought), `src/engines/memory/manager.py` (Persistence)
**Data:** Error type, Message, Tool Sequence, Context Pressure.

## Narrative
The first step of self-debugging is **Capture**. Blind retries compound failure by polluting the context with noise. Agents must take a snapshot of the current environment state, any error messages, and the sequence of actions that led to the crash.

### Data Points to Capture
- **Tool Sequence**: The last 3-5 tool calls and their outputs.
- **Context Pressure**: Is the context window nearly full? Are there redundant plans?
- **Environment State**: Current working directory, active branch, and expected vs. actual file states.
- **Error Signatures**: Exact stack traces and error codes.

## Facts
- **stop_and_capture**: The mandate to record failure state before the next tool call.
- **telemetry_snapshot**: The structured recording of the agent's internal and external state.
