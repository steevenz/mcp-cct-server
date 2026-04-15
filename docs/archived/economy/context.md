---
title: "Domain: Economy (Economic Logic / Irit Logic)"
tags: ["economy", "tokens", "pruning", "optimization"]
keywords: ["context-pruning", "summarization", "budgeting", "irit-logic"]
importance: 100
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Domain: Economy

## Purpose
The Economy domain regulates the consumption of limited cognitive resources (Tokens and Compute). It implements the system's **"Irit Logic"** (Economic Logic)—an aggressive resource optimization strategy designed to maintain long-term session coherence without exhausting the context window or token budget.

## Scope
Included in this domain:
- **Context Pruning**: Strategies for filtering history, including `branch_only` (ancestral filtering) and `summarized` (recursive compression).
- **Token Estimation**: Internal heuristics for calculating consumption per reasoning step.
- **Resource Budgeting**: Enforcing session-wide limits on thought depth and context size.

Excluded from this domain:
- **Quality Evaluation**: Determining *which* thoughts are valuable (handled by `Analysis`).
- **Memory Persistence**: The physical storage of history (handled by `Memory`).

## Usage
Developers should reference this domain when optimizing the system for high-concurrency or deep-reasoning sessions. It provides the core algorithms for maintaining "Contextual Intuition" while shedding the payload of irrelevant historical data.

## C&C Framework Alignment
The Economy domain is the environmental constraint that forces **Critical Pruning**. In the CCT Framework, divergent creative expansion is naturally bounded by economic realities. By enforcing a "Token Budget," the system forces the orchestrator to prioritize the most coherent and novel thoughts, effectively performing **Convergent Selection** throughout the session lifecycle.
