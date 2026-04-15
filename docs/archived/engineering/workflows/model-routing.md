---
title: "Tier-Based Model Routing"
tags: ["routing", "efficiency", "intelligence-tiers"]
keywords: ["haiku", "sonnet", "opus", "cost-discipline"]
related: ["./context.md"]
importance: 80
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Match task complexity to the most cost-effective and capable model tier.
**Files:** `src/utils/pricing.py` (Cost Tracking)

## Narrative
Effective engineering requires cost discipline. Not every task requires the maximum intelligence tier. We route tasks based on their specific needs:

### Routing Tiers
- **Haiku (Speed/Efficiency)**: Use for classification, simple boilerplate code, localized documentation edits, and small refactors.
- **Sonnet (Balanced implementation)**: The standard tier for feature implementation, complex refactoring, and logical reasoning within 1-3 files.
- **Opus (Architecture/Complex Analysis)**: Use for overall architecture design, root-cause analysis of subtle bugs, and multi-file invariants that require deep horizontal context.

### Escalation Policy
Only escalate to a higher tier if the lower tier fails to provide a coherent solution and the failure reason points to a reasoning gap rather than a tool error.

## Facts
- **cost_awareness**: Maintaining a high-density, low-overhead engineering budget.
- **tier_optimization**: Ensuring cognitive resources are used where they yield the most value.
