---
title: "Orchestration: Engine Registry"
tags: ["orchestration", "registry", "modular"]
keywords: ["strategy-mapping", "engine-discovery", "decoupling"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Topic: Engine Registry

## Overview
The Engine Registry is the **Map Room** of the CCT server. It decouple the intent (ThinkingStrategy) from the implementation (CognitiveEngine), allowing for a highly modular architecture where new engines can be added or swapped without modifying the Master Orchestrator.

## Key Concepts
- **Strategy Mapping**: Associating `ThinkingStrategy` enums with their corresponding Python class instances.
- **Provider Pattern**: The registry acts as a provider for the `CognitiveOrchestrator`, ensuring it always has access to the correct execution logic.
- **Lazy Initialization**: Engines are registered at startup but their internal resources (LLM configurations, specific prompt templates) are handled per-session.

## Related Topics
- [../context.md](../context.md)
- [../../Primitives/context.md](../../primitives/context.md)
