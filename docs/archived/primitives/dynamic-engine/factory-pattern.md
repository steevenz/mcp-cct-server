---
title: "Dynamic Factory: Polymorphic Cognitive Execution"
tags: ["primitives", "architecture", "patterns", "factory"]
keywords: ["DynamicPrimitiveEngine", "ThinkingStrategy", "polymorphism", "orchestration"]
related: ["context.md", "../../core/models/cognitive_models.md"]
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
Eliminate code duplication by consolidating multiple cognitive strategies into a single execution engine capable of handling varied inputs and outputs through a unified interface.

**Files:**
- `src/modes/primitives/orchestrator.py`

**Flow:**
1. Engine is initialized with a specific `ThinkingStrategy`.
2. `execute()` receives a payload, validates it via Pydantic, and handles sequential numbering.
3. A unique IDs is generated based on the strategy prefix (e.g., `ANA`, `SEA`).
4. Real-time scoring and summary generation are applied via the `ScoringEngine`.
5. The engine checks for **Early Convergence** if the quality score is exceptionally high.

## Narrative

### The Unified Execution Pipeline
Traditional AI architectures often create separate handlers for "Search," "Code," and "Analysis." The CCT server refactors this into the `DynamicPrimitiveEngine`. This pattern ensures that every primitive step—regardless of its strategy—undergoes the same rigorous **Critical Verification**:

- **Automated ID Prefixes**: Every thought is uniquely identifiable by its strategy (e.g., `ana-xxx` for analysis).
- **Sequential Guardrails**: The engine automatically interfaces with the `SequentialEngine` to prevent out-of-order thinking steps.
- **Auto-Archiving**: Any thought exceeding the `tp_threshold` (0.9 logical coherence) is immediately passed to the `PatternArchiver` for perpetual storage.

### Early Convergence Detection
A key feature of the Primitive Engine is the ability to signal the end of a session early. If a primitive step produces an "Elite Thought" (Coherence > 0.9), the engine sets `early_convergence_suggested=True`. This allows the **Critical** pillar to override unnecessary **Creative** steps if the problem has already been solved with high precision.

## Facts
- **prefix_logic**: The engine extracts the first 3 characters of the strategy value to use as the thought ID prefix. [convention]
- **payload_validation**: All inputs must conform to `CCTThinkStepInput`, preventing malformed data from entering the cognitive graph. [hardening]
- **dual_linking**: The engine ensures bi-directional links between parents and children in the memory layer during each execution. [memory]
- **integrated_archiver**: The `PatternArchiver` is instantiated within the engine, making every primitive step a potential source of institutional knowledge. [learning]
