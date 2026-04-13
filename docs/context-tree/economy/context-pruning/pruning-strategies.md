---
title: "Pruning Strategies: Cognitive Focus & Token Optimization"
tags: ["economy", "tokens", "pruning", "optimization"]
keywords: ["sliding_window", "branch_only", "ancestral_path", "summarization", "budget"]
related: ["context.md"]
importance: 90
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T00:00:00Z"
---

## Raw Concept

**Task:**
Reduce the token footprint of the cognitive history sent to the LLM to maintain high performance and avoid context window limits.

**Files:**
- `src/utils/economy.py`

**Flow:**
1. Retrieve the session's `context_strategy`.
2. Based on the strategy, filter or transform the list of `EnhancedThought` objects.
3. Return the optimized history for inclusion in the next LLM prompt.

## Narrative

### Active Pruning Strategies
The `ContextPruner` implements four distinct strategies to manage cognitive sprawl:

1. **Full History (`full`)**: No pruning. Used for short-duration sessions requiring maximum context.
2. **Sliding Window (`sliding`)**: Retains only the most recent **8 thoughts**. This is the default for high-speed, linear reasoning where older context is less relevant to the immediate next step.
3. **Branch-Only (`branch_only`)**: The most precise strategy for complex divergent thinking. It identifies the `target_thought_id` and filters out all thoughts except those that are direct ancestors. This removes "dead branches" from other divergent paths.
4. **Summarized History (`summarized`)**: A depth-aware optimization.
   - Thoughts within **3 levels** of the target are kept in full.
   - Distant thoughts have their `content` replaced by their `summary` (if available), prepended with `[SUMMARY]`.
   - Optimized thoughts are tagged with `context_optimized` for tracking.

### The Mechanism of Filtered Attention
By isolating the "Active Path," the system ensures that the LLM is not distracted by failed experiments or irrelevant branches. This is the implementation of **Operational Convergent Thinking** — even if the engine has generated 100 paths, it only presents the "Winning Trace" to the next analysis step.

## Facts
- **depth_threshold**: Default is set to `3` for the summarization strategy. [threshold]
- **tag_injection**: Pruned thoughts are specifically marked with the `context_optimized` tag to alert downstream processes that the content has been compressed. [convention]
- **O(depth) complexity**: Pruning strategies use pointer-chasing (parent_id) to reconstruct paths efficiently in a single pass. [performance]
