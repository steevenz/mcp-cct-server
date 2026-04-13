---
title: "Core: Models (Structural Integrity)"
tags: ["core", "models", "pydantic", "schemas"]
keywords: ["enhanced-thought", "session-state", "validation", "telemetry"]
importance: 90
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Models

## Overview
The Models topic defines the **Structural Integrity** layer of the CCT server. By utilizing Pydantic for data validation and parsing, the system ensures that every cognitive step, state transition, and metadata extraction follows a strict, predictable schema.

## Key Concepts
- **EnhancedThought**: The primary data unit for a single reasoning step, including telemetry (token counts, duration) and multidimensional scoring.
- **CCTSessionState**: The overarching model for an active mission, tracking the history of thoughts, pruning decisions, and the currently active logical branch.
- **Strict Parsing**: Enforcing type safety ensures that legacy memory retrievals (SQLite) match the runtime expectations of the Python codebase.

## Related Topics
- [../context.md](../context.md)
- [./cognitive_models.md](./cognitive-models.md)
