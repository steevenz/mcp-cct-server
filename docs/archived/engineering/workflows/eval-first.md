---
title: "Eval-First Execution Loop"
tags: ["eval-first", "testing", "validation"]
keywords: ["requirements", "success-criteria", "regression-check"]
related: ["./context.md"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Define success and regression criteria before generating code.
**Files:** `src/core/models/enums.py` (ThoughtType.CRITERIA, REQUIREMENT)
**Flow:** Define Evals → Run Baseline → Implement → Re-run Evals → Deltas

## Narrative
The Eval-First protocol is a technical guardrail that prevents "implementation drift." By requiring the agent to define **Capability Evals** (what must work) and **Regression Evals** (what must not break) upfront, we ensure that the engineering output is verifiable and aligns with user requirements.

### Rules
1. **No Code Without Criteria**: Never start implementation until the `CRITERIA` and `REQUIREMENT` thoughts are established.
2. **Failure Signatures**: Always capture why a baseline failed before attempting the fix.
3. **Delta Comparison**: Measure success based on the delta between baseline and post-implementation results.

## Facts
- **pre_validation**: Ensuring the problem is understood through formal requirements.
- **regression_safety**: Protecting existing functionality from being broken by new changes.
