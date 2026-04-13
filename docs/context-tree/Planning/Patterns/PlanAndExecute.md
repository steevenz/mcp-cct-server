---
title: "Plan-and-Execute: Structured Workflow"
tags: ["planning", "workflow", "structured"]
keywords: ["decomposition", "sub-goals", "state-management"]
related: ["./context.md"]
importance: 80
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Decomposition of enterprise-scale tasks into verifiable sub-goals.
**Files:** `src/engines/orchestrator.py`, `src/utils/pipelines.py`
**Flow:** Decompose → Execute Sub-goal → Validate → Next Sub-goal

## Narrative
Plan-and-Execute is the preferred pattern for long-horizon tasks with clear technical boundaries. It works by first creating a high-level plan (decomposition) and then executing each item in that plan as a separate execution unit.

### Rules
1. **Verifiable Steps**: Each sub-goal must have a clear "Definition of Done."
2. **State Context**: Ensure the context from previous steps is correctly injected into the next execution block.
3. **Adaptive Replanning**: If a sub-goal fails or changes the state significantly, the high-level plan should be modified.

## Facts
- **reliability**: High performance on long-running tasks.
- **auditability**: Clear progress tracking against a predefined checklist.
