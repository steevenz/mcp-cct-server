---
title: "Heuristics: Dynamic Strategy Pivoting"
tags: ["routing", "automatic-pipeline", "metacognition", "router"]
keywords: ["pivot", "strategy-selection", "pivoting-threshold"]
related: ["../context.md", "../../CCT/context.md"]
importance: 85
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T16:58:12Z"
updatedAt: "2026-04-12T16:58:12Z"
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

### Structure
The `AutomaticPipelineRouter` acts as the "Pre-frontal Cortex" of the CCT server. It is initialized during server bootstrap and injected into the Master Orchestrator. It maintains no local state, instead processing the `CCTSessionState` and `ScoringEngine` results on each tick.

### Rules
1. **Initial Categorization**: The router uses keyword analysis and problem-type mapping (e.g., 'code', 'research', 'ideation') to select the first engine.
2. **Pivot Trigger**: If `logical_coherence` falls below `PIVOT_THRESHOLD` (default 0.6) for more than one step, a pivot is triggered.
3. **Pivoting Path**:
   - `ANALYTICAL` failure triggers `CREATIVE` (Lateral thinking).
   - `LINEAR` failure triggers `SYSTEMATIC` (Tree traversal).
   - Any persistent failure triggers `MULTI_AGENT_FUSION` to force a divergent-convergent break.

### Examples
If a user asks for a complex refactor and the initial `ANALYTICAL` steps produce low coherence scores, the router will automatically pivot the session to `UNCONVENTIONAL_PIVOT`. This forces the system to re-examine the problem from a different angle before returning to analytical execution.

## Facts
- **PIVOT_THRESHOLD**: 0.6 [heuristic]
- **max_pivots_per_session**: 3 [limit]
