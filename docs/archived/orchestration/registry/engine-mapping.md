---
title: "Engine Mapping: Routing Cognitive Strategies"
tags: ["orchestration", "registry", "mapping", "routing"]
keywords: ["CognitiveEngineRegistry", "hybrid_mapping", "ThinkingStrategy", "dispatch"]
related: ["context.md", "../../Primitives/dynamic-engine/factory_pattern.md"]
importance: 100
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T00:00:00Z"
---

## Raw Concept

**Task:**
Efficiently dispatch incoming thinking requests to the correct implementation engine based on the `ThinkingStrategy` requested in the payload.

**Files:**
- `src/modes/registry.py`

**Flow:**
1. Orchestrator calls `registry.get_engine(strategy)`.
2. Registry identifies if the strategy is a "Hybrid" or a "Primitive."
3. If Hybrid, it returns a specialized singleton/instance of the hybrid engine.
4. If Primitive, it returns an instance of `DynamicPrimitiveEngine` configured for that specific strategy.

## Narrative

### The Dispatch Hierarchy
The `CognitiveEngineRegistry` manages the lifecycle of all reasoning engines. It uses a tiered mapping system to maintain architectural cleaness:

1. **The Catch-All (Default)**: By iterating through the `ThinkingStrategy` enum, the registry automatically assigns all unrecognized strategies to the `DynamicPrimitiveEngine`. This allows the server to scale to 22+ strategies without manual boilerplate.
   
2. **Hybrid Overrides**: Strategies that require complex orchestration (more than one thought step per request) or access to the `Fusion` layer are manually overridden:
   - **Multi-Agent Fusion**: Injected with the `FusionOrchestrator` for high-density convergent synthesis.
   - **Actor-Critic Loop**: Automated two-phase refinement (Criticism -> Synthesis).
   - **Lateral/Horizon**: Specialized engines for non-linear and long-term reasoning paths.

### Dependency Injection
During initialization, the registry ensures all engines have standardized access to the infrastructure (`Memory`, `Sequential`). This decoupling means that adding a new engine (a new "Specialized Hybrid") only requires adding a line to the `hybrid_mapping` dictionary in the registry.

## Facts
- **lazy_vs_eager**: The registry initializes all engines *eagerly* during the startup of the `CognitiveEngineRegistry` instance to prevent latency spikes during the first request. [performance]
- **enum_driven**: The system is strictly enum-driven; any strategy not in the `ThinkingStrategy` enum will fail validation before reaching the registry. [type-safety]
- **polymorphic_return**: Regardless of the implementation (Hybrid or Primitive), every engine returns a standardized dictionary response, ensuring the top-level transport layer remains decoupled from cognitive details. [design]
