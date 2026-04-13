---
title: "Domain: Orchestration (The Central Executive)"
tags: ["orchestration", "executive", "lifecycle"]
keywords: ["session", "lifecycle", "coordination", "self-improvement"]
importance: 100
recency: 1.0
maturity: "core"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Domain: Orchestration

## Purpose
The Orchestration domain acts as the **Central Executive** of the CCT server. It is responsible for high-level decision making, mapping thinking strategies to their appropriate engines, and coordinating the lifecycle of cognitive tasks through complex, multi-phase pipelines.

## Scope
Included in this domain:
- **Master Orchestrator**: The primary application service (`CognitiveOrchestrator`) coordinating Memory, Sequential, Fusion, and Analysis.
- **Engine Registry**: The central mapping of `ThinkingStrategy` enums to concrete engine implementations.
- **Session Lifecycle**: Managing the sequence of "Start -> Execute -> Pivot -> Conclude."
- **Self-Improvement Loop**: Injecting historical knowledge (patterns/anti-patterns) into active reasoning sessions.

Excluded from this domain:
- **Individual Engine Logic**: Specific "Thinking" rules (handled by `Engines`).
- **Heuristic Math**: Core scoring logic (handled by `Analysis`).

## Usage
Developers should reference this domain when:
- Adding a new thinking strategy or hybrid reasoning mode.
- Modifying the high-level coordination between engines.
- Adjusting how historical context is injected into new sessions.

## C&C Framework Alignment
The Orchestration domain is where the **Creative** and **Critical** pillars are woven into a cohesive strategy. It determines the "Executive Balance" — deciding when raw divergent thinking needs to be throttled by critical review, and when the system should pivot strategies to break a cognitive stalemate.
