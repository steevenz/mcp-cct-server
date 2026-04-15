---
title: "Human Orchestration: Delegate-Review-Own"
tags: ["orchestration", "human-in-the-loop", "ownership"]
keywords: ["delegate", "review", "own", "collaboration"]
related: ["./context.md"]
importance: 85
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Narrative
In an agentic engineering workflow, the division of labor between human and AI is clear. We follow the **Delegate-Review-Own** model to ensure high-velocity development without sacrificing architectural integrity.

### The Model
1. **Delegate**: AI agents perform the bulk of implementation, unit testing, boilerplate scaffolding, and documentation updates.
2. **Review**: Human engineers verify the AI's output for logical correctness, security vulnerabilities, and adherence to system invariants.
3. **Own**: The human engineer remains the ultimate owner of the architecture, trade-off decisions, and project outcomes.

### Quality Gates
Review cycles should focus on:
- Invariants and non-obvious edge cases.
- Error boundaries and failure modes.
- Hidden coupling that the AI might have missed.

## Facts
- **shared_mental_models**: Ensuring AI and human are aligned on the technical vision.
- **velocity_with_control**: Accelerating development while keeping the human "at the wheel."
