---
title: "Chain-of-Thought: Linear Transparency"
tags: ["cot", "linear", "step-by-step"]
keywords: ["transparency", "explicability", "reasoning"]
related: ["./context.md"]
importance: 75
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Provide a clear, step-by-step logical sequence for easy human audit.
**Files:** `src/engines/sequential/engine.py`
**Flow:** Problem → Step 1 → Step 2 → ... → Final Answer

## Narrative
Chain-of-Thought (CoT) is the most primitive but essential planning pattern. It requires the model to "show its work" by breaking down its reasoning into a sequence of intermediate steps before producing a final answer.

### Value Proposition
- **Mental Scratchpad**: Allows the model to process complex logic sequentially.
- **Traceability**: Enables users to identify exactly where a logical error occurred.

### Rules
- Avoid "blind jumps" in logic.
- Each step should be self-contained and logically follow the previous one.

## Facts
- **explicability**: Primary benefit for audit and debugging.
- **linear**: Simplest structure with no branching or looping.
