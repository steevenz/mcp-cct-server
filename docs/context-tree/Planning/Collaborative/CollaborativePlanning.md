---
title: "Collaborative Planning Patterns"
tags: ["collaboration", "hitl", "agent-human"]
keywords: ["feedback-loop", "escalation", "transparency"]
related: ["./context.md"]
importance: 80
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Narrative
The most effective AI agents are those that collaborate seamlessly with humans. In the CCT framework, collaborative planning is realized through transparent reasoning and mission-critical checkpoints.

### Strategies for Human Assistance
1. **Confidence-Based Escalation**: If the model's confidence in a plan branch is low (<0.4), it should pause and present options to the user.
2. **Phase 7 Clearance**: For users on the `human_in_the_loop` profile, the system enforces a hard STOP at the strategic impact phase (Phase 7) to allow for manual review.
3. **Interactive Refinement**: Allowing users to modify specific sub-goals in a generated plan before execution begins.

### Implementation Guidelines
- Prioritize **Chain-of-Thought** transparency when a human is reviewing the plan.
- Use **ReAct** observations to present current "ground truth" to the human collaborator.
- Ensure all intervention points are logged for forensics.

## Facts
- **shared_autonomy**: Balancing AI autonomy with human control.
- **mission_critical**: High-stakes scenarios requiring mandatory human review.
