---
title: "ReWOO: Reasoning Without Observation"
tags: ["rewoo", "efficiency", "off-chain"]
keywords: ["token-efficiency", "upfront-planning"]
related: ["./context.md"]
importance: 70
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Execute a predictable sequence of tool calls with minimum latency.
**Files:** `src/utils/pipelines.py`, `src/engines/skills_loader.py`
**Flow:** Plan all steps → Execute all steps → Synthesize Answer

## Narrative
ReWOO (Reasoning Without Observation) optimizes for token efficiency and latency by decoupling the planning phase from the execution phase. It assumes that the tool sequence can be predicted without needing to see individual outputs first.

### Structure
1. **Planner**: Decides the sequence of actions and their dependencies.
2. **Executor**: Runs the actions (often in parallel).
3. **Solver**: Synthesizes the final answer using the collected data.

### Rules
- Use only when the reasoning path is stable.
- If an observation changes the plan, fall back to **ReAct**.

## Facts
- **token_economy**: Reduces model calls by batching tool execution.
- **parallelism**: Enables running non-dependent tool calls at the same time.
