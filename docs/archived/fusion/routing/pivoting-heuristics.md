---
title: "Heuristics: Dynamic Strategy Pivoting"
tags: ["routing", "automatic-pipeline", "metacognition", "router"]
keywords: ["pivot", "strategy-selection", "pivoting-threshold"]
related: ["../context.md", "../../cct/context.md"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T16:58:12Z"
updatedAt: "2026-04-12T18:00:00Z"
---

## Raw Concept

**Task:**
Monitors session quality and dynamically switches thinking engines if performance targets are not met.

**Files:**
- `src/engines/fusion/router.py`
- `src/engines/orchestrator.py`

**Flow:**
Execute Step -> Score Step -> Compare to Threshold -> (If Low) Request Pivot -> Select New Strategy.

## Narrative

### Structure: The Cognitive GPS
The `AutomaticPipelineRouter` acts as the "Pre-frontal Cortex" of the CCT server. It is injected into the Master Orchestrator and evaluates every thought tick. It maintains no local state, ensuring it remains scalable and predictable across hundreds of concurrent sessions.

### Rules
1. **Initial Categorization**: The router uses keyword analysis and logic-profile mapping to select an optimal initial pipeline (e.g., ANALYICAL for code, CREATIVE for ideation).
2. **Pivot Trigger**: If `logical_coherence` or `clarity_score` falls below the **PIVOT_THRESHOLD** (`0.4`), a pivot is triggered.
3. **Pivoting Path**:
   - Sequential failure triggers `UNCONVENTIONAL_PIVOT` (Lateral thinking break).
   - Low coherence triggers `MULTI_AGENT_FUSION` to simulate a "Council of Critics" and resolve cognitive deadlock.
4. **Adaptive Scaling**: If a pivot is successful (score improves), the router may choose to remain in the new strategy for the remainder of the pipeline.

### Examples
If a user asks for a high-risk security refactor and the initial steps produce low coherence scores because the model is over-simplifying, the router will trigger an `UNCONVENTIONAL_PIVOT` or route to `THOUGHTS_V2` (Precise) to force deeper validation before continuing.

## Facts
- **PIVOT_THRESHOLD**: 0.4 (Derived from `src.core.constants`). [heuristic]
- **max_pivots**: 3 per session limit to prevent infinite oscillation. [limit]
- **early_exit**: The router can bypass convergence logic if a high-confidence conclusion node (score > 0.8) is hit before reaching the estimated total. [optimization]
