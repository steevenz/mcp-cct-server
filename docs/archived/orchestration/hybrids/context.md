---
title: "Orchestration: Hybrid Engines"
tags: ["orchestration", "hybrids", "multi-agent"]
keywords: ["actor-critic", "fusion", "complex-pipelines"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Topic: Hybrid Engines

## Overview
Hybrid Engines are **Composite Strategies** that coordinate multiple primitive engines into a single, cohesive reasoning cycle. They are designed for high-complexity tasks where a single perspective is insufficient.

## Key Concepts
- **Cognitive Redundancy**: Executing multiple divergent engines (e.g., ANALYTICAL and CREATIVE) in parallel to ensure solution coverage.
- **Iterative Feedback (Actor-Critic)**: One engine generates a hypothesis (Actor) while another evaluates and refines it (Critic) in a recursive loop.
- **Fusion Pipelines**: Strategies that culminate in a `convergent_synthesis` step to merge insights from divergent threads.

## Implementation Examples
- **Multi-Agent Fusion**: Distributing a problem across several specialized thinking models and fusing their outputs.
- **Chain of Verification (CoVe)**: A self-correcting pipeline that generates a response, identifies embedded claims, and verifies them individually before final synthesis.

## Related Topics
- [../../fusion/context.md](../../fusion/context.md)
- [../../fusion/orchestration/context.md](../../fusion/orchestration/context.md)
