---
title: "Early Convergence: Dynamic Thresholding"
tags: ["patterns", "performance", "convergence", "economy"]
keywords: ["early_convergence_suggested", "DEFAULT_TP_THRESHOLD", "Elite_Thought", "token_optimization"]
related: ["context.md", "archiving_criteria.md", "../economy/Budgets/pruning_strategies.md"]
importance: 80
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T00:00:00Z"
---

## Raw Concept

**Task:**
Identify moments where the problem has been solved "ahead of schedule" and suggest an early end to the reasoning chain.

**Files:**
- `src/modes/primitives/orchestrator.py`
- `src/core/constants.py`

**Flow:**
1. During execution, a thought is generated and scored.
2. If the `logical_coherence` exceeds the strict `DEFAULT_TP_THRESHOLD` (0.95), it is flagged as an "Elite" thought.
3. The server sets `early_convergence_suggested: true` in its response.
4. The client can choose to terminate the planned pipeline immediately, saving 50-80% of the remaining token budget.

## Narrative

### Beyond the Planned Pipeline
Cognitive missions often start with a multi-step suggested pipeline (e.g., 5 steps of analysis). However, high-intelligence models often achieve a "Breakthrough" in the very first or second step. The CCT Framework detects these breakthroughs using **Dynamic Thresholding**.

### The "Elite" Breakthrough
An elite thought is one that doesn't just meet the archiving criteria but significantly exceeds it. When `coherence > 0.95`, the system recognizes that the current reasoning path has reached a state of **Total Convergence**. Continuing the pipeline would likely result in redundant "Self-Correction" or loops.

### Strategic Termination
This mechanism is a key pillar of the server's **Cheap/Fast** philosophy. By providing the `early_convergence_suggested` flag, the server empowers the client to stop the "Creative" exploration once the "Critical" objective has been achieved, preventing the waste of compute resources.

## Facts
- **high_rigor_gate**: The 0.95 threshold is significantly higher than the standard 0.9 archiving threshold to ensure that only near-perfect reasoning triggers the termination signal. [gate]
- **non_blocking**: The suggestion is advisory. Clients can choose to ignore it if they want to pursue divergent "Creativity" even after a breakthrough. [flexibility]
- **economy_link**: Early convergence is the most effective form of **Context Pruning**, as it removes the need for subsequent thoughts entirely. [efficiency]
