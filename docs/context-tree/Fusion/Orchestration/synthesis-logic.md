---
title: "Algorithm: Convergent Cognitive Synthesis"
tags: ["fusion", "synthesis", "convergence", "llm"]
keywords: ["merging", "integrative", "cognitive-density"]
related: ["../context.md", "../routing/pivoting_heuristics.md"]
importance: 90
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T16:58:00Z"
updatedAt: "2026-04-12T16:58:00Z"
---

## Raw Concept

**Task:**
Synthesize multiple divergent perspectives into a unified, high-coherence conclusion node.

**Files:**
- `src/engines/fusion/orchestrator.py`
- `src/analysis/scoring_engine.py`

**Flow:**
Input Thoughts -> Context Extraction -> LLM Synthesis (Convergent Prompt) -> Scoring Validation -> Memory Persistence.

## Narrative

### Structure
The synthesis logic resides within the `FusionOrchestrator`. It operates as a post-processing layer that can be invoked by any hybrid mode (e.g., `MULTI_AGENT_FUSION`). It uses a structured context window where constituent thoughts are delineated by IDs and strategy types to provide the LLM with the necessary provenance for each insight.

### Rules
1. **Cognitive Gain Requirement**: Every synthesis node must be analyzed by the `ScoringEngine`. The result is only considered successful if the `logical_coherence` or `evidence_strength` of the synthesis exceeds the average of its constituents.
2. **Provenance Preservation**: The `builds_on` field in the `EnhancedThought` model must be populated with all input IDs to maintain the traceability of the conclusion.
3. **Efficiency Tiering**: For standard fusion tasks, the system uses "efficiency" tier models (fast/cheap) to reduce latency, switching to precision tiers only for final session summaries.

### Examples
When merging different engine outputs (e.g., ANALYICAL and CREATIVE), the orchestrator directs the LLM to:
- Resolve contradictions between the analytical data and creative hypotheses.
- Maintain the creative spark while grounding it in analytical evidence.
- Produce a single `INTEGRATIVE` thought node.

## Facts
- **convergence_threshold**: Set to 0.85 by default. Logic concludes when recent thoughts hit this coherence level. [rule]
- **model_tier**: Default is 'efficiency'. [config]
