---
title: "Fusion Logic: Dynamic Routing & Convergence"
tags: ["fusion", "orchestration", "routing", "synthesis"]
keywords: ["fusion", "router", "convergence", "heuristic", "multi-agent"]
related: ["context.md"]
importance: 100
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

## Raw Concept

**Task:**
Synthesize divergent thoughts into high-density convergent conclusions and dynamically route the cognitive pipeline based on real-time quality benchmarks.

**Files:**
- `src/engines/fusion/orchestrator.py`
- `src/engines/fusion/router.py`

**Flow:**
1. **Divergent Phase**: Specialized thinking strategies generate cognitive nodes.
2. **Dynamic Routing**: `AutomaticPipelineRouter` evaluates if the current path is quality-stable.
3. **Adaptive Pivot**: If scores drop below thresholds, an `UNCONVENTIONAL_PIVOT` is triggered.
4. **Convergence Phase**: `FusionOrchestrator` synthesizes multiple perspectives into a unified Synthesis node upon reaching threshold-heavy clusters.

## Narrative

### Structure: Convergent Synthesis
The `FusionOrchestrator` implements the **Convergent** half of the C&C Framework. Its role is to take a set of "Raw Thoughts" (Divergent/Creative) and extract the "Unified Conclusion" (Critical). It uses efficiency-tiered LLM tokens to consolidate redundant data, resolve internal objective contradictions, and finalize a high-confidence reasoning path.

### Dynamic Routing & The PIVOT_THRESHOLD
The system features an `AutomaticPipelineRouter` that monitors session health in real-time. 
- **Pivot Logic**: If `clarity_score` or `logical_coherence` of recent thoughts falls below the **PIVOT_THRESHOLD** (`0.4`), the router automatically switches strategy (e.g., `UNCONVENTIONAL_PIVOT`) to break intellectual stagnation.
- **Convergence Logic**: If coherence remains consistently above `0.85` or high-density persona insights are detected (minimum depth 3), the system triggers `MULTI_AGENT_FUSION` to wrap up findings.

### Synthesis Heuristics
1. **Redundancy Removal**: Merging duplicate observations into single nodes.
2. **Conflict Resolution**: Identifying and flagging contradictions in divergent thoughts.
3. **Pattern Extraction**: Finding shared themes across multi-agent perspectives.

## Facts
- **convergence_threshold**: Set to `0.85` by default; below this, thinking is considered incomplete unless a conclusion node is reached. [metrics]
- **efficiency_tiering**: Synthesis steps default to "efficiency" model tiers to reduce latency during iterative fusion. [economy]
- **synthesis_as_revision**: Every fusion step is treated as a `revision` in the sequential engine, granting extra cognitive "slots" for the conclusion. [logic]
- **automated_pivoting**: The system "self-corrects" its routing if it detects falling scores (Clarity/Coherence < 0.4). [autonomy]
