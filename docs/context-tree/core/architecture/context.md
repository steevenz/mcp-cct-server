---
title: "Architecture: The CCT v5.0 System Design"
tags: ["architecture", "core", "design", "v5.0"]
keywords: ["orchestration", "engines", "registry", "persistence"]
importance: 100
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Architecture Overview: Cognitive OS v5.0

## High-Level Purpose

The **Creative Critical Thinking (CCT) Framework** is a multi-layered reasoning engine that transforms standard LLM outputs into hardened architectural artifacts. It moves from "Stateless Completions" to "Persistent Sessions".

## Structural Hierarchy

```mermaid
graph TD
    User([Principal Systems Architect]) -->|Missions| CCT[CCT Framework]
    
    subgraph Orchestration [Orchestration Layer]
        Dispatch[cct-dispatch.md] --> Orch[Master Orchestrator]
        Orch --> Reg[Engine Registry]
    end
    
    subgraph CoreEngines [Core Selective Engines]
        Reg --> Fusion[Fusion Engine: Synthesis]
        Reg --> Seq[Sequential Engine: Logical Integrity]
        Reg --> Memory[Memory Engine: Persistence]
    end
    
    subgraph Storage [The Cognitive Ledger]
        Memory --> SQLite[(SQLite WAL: cct_memory.db)]
        SQLite --> Patterns[Thinking Patterns: Golden/Anti]
    end
    
    subgraph Economy [Resource Management]
        Pruning[Irit Logic: Token Economy]
    end
```

## Key Components

1.  **Master Orchestrator**: The decision brain that parses missions and selects the appropriate strategy via the `Engine Registry`.
2.  **Adaptive Routing**: Dynamically pivots between thinking modes (e.g., from `tree` to `actor-critic`) based on real-time quality scores.
3.  **Sequential Integrity**: Ensures no steps are skipped and maintains a clear, forensic audit trail of all cognitive transitions.
4.  **Cognitive Ledger (SQLite)**: Persists all thoughts, scores, and patterns using thread-safe, WAL-mode persistence.

## Related Topics
- [Technical Standard](./technical-standard.md)
- [Engine System](./engine-system.md)
- [../Models/context.md](../models/context.md)
