---
title: "Topic: Sequential Flow & Control"
tags: ["sequential", "orchestration", "control-flow"]
keywords: ["metronome", "sequence", "integrity", "branching", "limits"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Topic: Sequential

## Overview
The Sequential topic governs the **"Flow of Time"** and the **"Cognitive Metronome"** of the CCT server. It acts as the system's backbone, ensuring that reasoning proceeds in a logical order, enforcing safety limits, and determining how the cognitive budget expands during complex reasoning cycles or branching events.

## Key Concepts
- **Sequence Integrity**: Active validation and auto-correction of thought numbers (e.g., rejecting Thought 5 if Thought 4 wasn't processed) to prevent LLM sequence hallucinations.
- **Dynamic Budget Expansion**: 
    - **Revision Expansion**: Detecting `is_revision` triggers an automatic increment to the estimated total thoughts.
    - **Boundary Extension**: If a thought is requested near the current estimate, the boundary is automatically pushed forward.
- **Branching Architecture**: Supporting diverged cognitive paths by linking children nodes back to their specific parent IDs across different timelines.
- **Convergence Gates**: Enforcing a minimum reasoning depth (3 steps) and checking orchestrator-defined convergence criteria before enabling task completion.

## Guardrails
- **Max Thoughts [H1]**: Enshrinement of a hard-coded limit (200 thoughts) per session to prevent recursive resource depletion.
- **Depth Minimum**: Preventing premature convergence by requiring a baseline cognitive effort.

## Related Topics
- [Logic Control](logic-control.md)
- [../context.md](../context.md)
