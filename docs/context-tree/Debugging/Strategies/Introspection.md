---
title: "Self-Debugging: Introspection & Reporting"
tags: ["debugging", "introspection", "audit"]
keywords: ["debug-report", "lessons-learned", "prevention"]
related: ["./context.md"]
importance: 85
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Produce a structured debug report for human audit and future avoidance.
**Files:** `src/core/models/domain.py` (AntiPattern)

## Narrative
Introspection is the "after action report" of a failure. It makes the agent's internal debugging process transparent to the user and ensures the failure is used as a learning opportunity.

### Introspection Report Components
- **Failure Summary**: What specifically broke?
- **Root Cause**: What was the technical or logical reason?
- **Recovery Analysis**: What was tried, and did it work?
- **Burn Assessment**: Token and time consumed during the failure/recovery loop.
- **Preventative Action**: How to avoid this pattern in the future.

## Facts
- **auditable_failure**: Ensuring failures are readable by humans for oversight.
- **preventative_encoding**: Noting patterns that should be archived as Anti-Patterns.
