---
title: "15-Minute Task Decomposition"
tags: ["decomposition", "modularity", "lego-principle"]
keywords: ["agent-sized-units", "atomicity", "dependencies"]
related: ["./context.md"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Break complex engineering tasks into small, atomized execution units.
**Protocol:** The 15-Minute Rule.
**Files:** `src/engines/skills_loader.py` (TaskDecomposer)

## Narrative
Following the **Lego Principle**, all engineering work must be deconstructed into "agent-sized units." Each unit should represent a task that can be executed and verified within a 15-minute window. This limits the risk of large-scale failures and makes debugging significantly easier.

### Principles
- **Independently Verifiable**: Every unit must have a specific test/check that proves it works.
- **Single Dominant Risk**: Each unit should address one specific complexity to avoid cognitive overload.
- **Dependency Ordering**: Units must be ordered so that foundations are built before superstructures.

## Facts
- **atomic_completion**: Ensuring each step is a complete, usable chunk of code.
- **risk_isolation**: Confining technical complexity to small, manageable boundaries.
