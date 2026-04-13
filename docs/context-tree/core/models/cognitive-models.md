---
title: "Core Models: Cognitive Schema Details"
tags: ["core", "models", "schema", "telemetry"]
keywords: ["enhanced-thought", "cct-session-state", "pydantic", "data-types"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Cognitive Models

## Overview
This topic details the specific Pydantic schemas used to maintain the state of the CCT Framework. These models are used across the `Engines`, `Memory`, and `Analysis` domains to ensure consistent data handling.

## Essential Models

### 1. `EnhancedThought`
Represents a single atomic step in a Chain-of-Thought (CoT) process.
- **Narrative**: The human-readable thought content.
- **ThoughtType**: Categorization (e.g., `observation`, `hypothesis`, `synthesis`).
- **Phase**: The current phase in the C&C lifecycle (0 to 7).
- **Scores**: A dictionary containing multi-dimensional quality metrics (Clarity, Logic, Novelty, Evidence).
- **Telemetry**: Performance data including token usage and execution duration.

### 2. `CCTSessionState`
Maintains the global state for a persistent cognitive session.
- **SessionId**: Unique UUID for the mission.
- **History**: A list of all `EnhancedThought` objects generated.
- **BranchId**: Identifier for the currently prioritized logical path.
- **PrunedBranches**: List of ancestral IDs that have been evicted for token economy.
- **Metadata**: Key-value store for session-specific context (e.g., target technology stack).

## Database Interaction
These models are serialized to JSON before being persisted in the `sessions` table of the SQLite database. Upon retrieval, the `MemoryManager` re-instantiates them using `model_validate_json()` to restore cognitive state with full type safety.

## Related Topics
- [./context.md](./context.md)
- [../../Memory/persistence/sqlite_schema.md](../../memory/persistence/sqlite-schema.md)
