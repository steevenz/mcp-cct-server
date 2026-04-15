---
title: "Analysis: Scoring Heuristics"
tags: ["analysis", "scoring", "heuristics"]
keywords: ["metrics", "evaluation", "pattern-gating"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Topic: Scoring

## Overview
The Scoring topic defines the heuristics used to evaluate the quality of a cognitive step. It provides the mathematical grounding for the **Critical** pillar, allowing the system to quantify success and identify when a line of reasoning has stalled or converged.

## Key Concepts
- **Multi-Dimensional Metrics**: Evaluation across four primary axes (Clarity, Coherence, Novelty, Evidence).
- **Token Efficiency**: Using caching and sampling to ensure that scoring does not exhaust the token budget.
- **Pattern Gating**: Using strict thresholds (0.9 coherence) to identify elite thoughts worthy of long-term storage in the `thinking_patterns` archive.

## Related Topics
- [Scoring Heuristics](heuristics.md)
- [../Quality/context.md](../quality/context.md)
