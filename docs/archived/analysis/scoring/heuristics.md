---
title: "Scoring Heuristics: The Metrics of C&C"
tags: ["analysis", "scoring", "heuristics", "metrics"]
keywords: ["clarity", "coherence", "novelty", "evidence", "sampling"]
related: ["context.md"]
importance: 100
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

## Raw Concept

**Task:**
Quantify the quality of reasoning steps across four core dimensions while maintaining token and compute efficiency.

**Files:**
- `src/analysis/scoring_engine.py`
- `src/analysis/metrics.py`

**Flow:**
1. Retrieve thought content and previous history.
2. Check `_metrics_cache` for previous results.
3. Map similarity metrics to quality scores using nonlinear weighting.
4. Output `ThoughtMetrics` and trigger "Elite Pattern" detection if scores are high.

## Narrative

### Structural Heuristics
The CCT framework relies on four primary metrics to enforce **Critical Rigor**:

1. **Logical Coherence**: Measures semantic alignment with the parent thought.
   - **Optimal Range (0.3 - 0.8)**: Boosts score to `0.9`. Indicates meaningful progression.
   - **Loop Penalty (> 0.9)**: Penalizes score to `0.4`. Detects repetitive loops or hallucinations.
   - **Weak Connection (< 0.3)**: Scores `0.5`, flagging potential non-sequiturs.

2. **Novelty Score**: Prevents repetitive "Creative" divergence.
   - Uses **Novelty Sampling**: Compares content against the last few thoughts and samples from older history to maintain O(1) performance in large sessions.
   - Formula: `1.0 - max_similarity`.

3. **Evidence Strength**: Quantitative "Fact-Gating."
   - Weighted by keywords: `count / 3.0` (capped at 1.0).
   - Markers: `data`, `code`, `specifically`, `result`, `evidence`.

4. **Information Density**: Ratio of unique tokens to total token count. High density indicates concise, high-value communication.

### Efficiency Tiering
To maintain low latency and token economy, the `ScoringEngine` implements:
- **Skip Threshold**: Thoughts < 100 characters receive default scores to bypass heavy computation.
- **Lazy Metric Calculation**: Metrics are only computed when requested by the orchestrator.
- **LRU Caching**: All tokenization results are cached to prevent redundant processing.

## Facts
- **tp_threshold**: Coherence >= 0.9 AND Evidence >= 0.8 identifies a "Golden Thinking Pattern." [rule]
- **non_linear_similarity**: Specifically penalizes excessive similarity to break cognitive deadlock. [innovation]
- **incremental_analysis**: The `IncrementalSessionAnalyzer` updates session-wide averages (clarity, bias) in O(1) time per thought. [optimization]
