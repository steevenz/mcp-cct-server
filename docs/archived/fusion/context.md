---
title: "Domain: Fusion"
tags: ["core", "fusion", "routing", "synthesis"]
keywords: ["convergence", "automatic-pipeline", "pivot", "consensus"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Domain: Fusion

## Purpose
The Fusion domain is responsible for the **convergent phase** of the cognitive process. It focuses on synthesizing multiple, often divergent, information paths or expert perspectives into high-density, high-quality unified conclusions. It also hosts the "Cognitive GPS" that routes thinking tasks dynamically.

## Scope
Included in this domain:
- **Convergent Synthesis**: Logic in `FusionOrchestrator` to merge multiple `EnhancedThought` nodes (e.g., persona insights) into a single synthesis node.
- **Cognitive Routing**: The **'Automatic Pipeline'** logic (`AutomaticPipelineRouter`) that dynamically selects and pivots thinking strategies based on real-time quality scores.
- **Convergence Analysis**: Determining when a reasoning path has reached a sufficient level of coherence (Avg Coherence > 0.85) to conclude.

## Usage
Developers should reference this domain when:
- Implementing new hybrid modes that require a 'consensus' or 'fusion' step.
- Fine-tuning the 'Automatic Pipeline' routing weights and thresholds.
- Adding new synthesis heuristics or LLM synthesis prompts.
- Troubleshooting session pivots or early termination logic.

## Key Projects
- [Dynamic Routing](routing/context.md)
- [Convergent Orchestration](orchestration/context.md)
- [Automatic Routing Logic](automatic-routing.md)
