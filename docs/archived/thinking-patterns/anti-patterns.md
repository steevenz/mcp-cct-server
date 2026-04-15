---
title: "Thinking Patterns: Anti-Patterns"
tags: ["patterns", "failures", "immunity", "regression"]
keywords: ["forensic-audit", "corrective-action", "cognitive-trap", "failures"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Anti-Patterns

## Overview
Anti-Patterns represent the **Mental Immune System** of the CCT server. They are forensic records of cognitive strategies that resulted in failure, hallucination, or logical inconsistencies. By documenting these failures alongside mandatory **Corrective Actions**, the system ensures it never falls into the same logical trap twice.

## Key Concepts
- **Forensic Capture**: When a thought sequence is aborted due to critical logical failure or negative human feedback, it is candidate for the `anti_patterns` table.
- **Corrective Action**: Every anti-pattern MUST contain a specific instruction on how to avoid the trap in the future.
- **Forced Injection**: During Phase 0 (Routing), if the mission goal matches a known Anti-Pattern's problem domain, the system forcefully injects the Anti-Pattern to warn the AI of the historical pitfall.

## Narrative
The logic of failure:
1.  **Failure Detection**: A cognitive path is rejected by the `ScoringEngine` or a Human Auditor.
2.  **Archiving**: The path is logged into SQLite `anti_patterns`.
3.  **Active Prevention**: In future sessions, the system alerts the AI: "A similar strategy was attempted before and failed because [X]. You MUST apply [Corrective Action]."

## Related Topics
- [./context.md](./context.md)
- [../analysis/Quality/context.md](../analysis/quality/context.md)
