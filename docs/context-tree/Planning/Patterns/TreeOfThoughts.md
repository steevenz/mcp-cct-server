---
title: "Tree-of-Thoughts: Branching Reasoning"
tags: ["tot", "branching", "exploration"]
keywords: ["reasoning-paths", "evaluation", "pruning"]
related: ["./context.md"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Solve complex problems by exploring and evaluating multiple reasoning candidates.
**Files:** `src/engines/fusion/orchestrator.py`, `src/core/models/enums.py` (Renamed from legacy TREE)
**Flow:** Propose multiple paths → Evaluate candidates → Expand best candidate → Converge

## Narrative
Tree-of-Thoughts (ToT) is designed for problems that require deliberate exploration and backtracking. Instead of a single linear path, the agent generates multiple "thought branches," evaluates them based on logic and evidence, and prioritizes the most promising ones.

### Structure
- **Branching**: Generating 3-5 alternative next steps.
- **Evaluation**: Self-critique or external scoring of each branch's viability.
- **Selection**: Choosing the top candidate via heuristics (greedy, BFS, or DFS).

### Rules
- **Pruning**: Aggressively remove low-confidence branches to save tokens.
- **Breadth Control**: Limit the number of parallel branches to prevent divergence.

## Facts
- **exploration**: High ability to find creative solutions by not settling for the first idea.
- **precision**: Improved logic through systematic evaluation of alternatives.
