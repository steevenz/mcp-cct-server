---
title: "Domain: Council (Multi-Advisor Consensus)"
tags: ["council", "consensus", "decision-making"]
keywords: ["architect", "skeptic", "pragmatist", "critic"]
importance: 85
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Domain: Council

## Purpose
The Council domain provides a formal decision-making protocol for high-ambiguity or architectural-critical paths. It utilizes four distinct cognitive lenses to surface trade-offs and risks before reaching a consensus.

## Scope
Included in this domain:
- **Architect Lens**: Correctness, maintainability, long-term implications.
- **Skeptic Lens**: Premise challenge, simplification, assumption breaking.
- **Pragmatist Lens**: Shipping speed, user impact, operational reality.
- **Critic Lens**: Edge cases, downside risk, failure modes.

## Usage
Invoke the `COUNCIL_OF_CRITICS` strategy during `ARCH` or `SEC` pipelines when multiple credible paths exist without an obvious winner.
