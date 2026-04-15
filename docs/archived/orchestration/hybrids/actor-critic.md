---
title: "Actor-Critic Pipeline: Automated Refinement"
tags: ["orchestration", "hybrids", "actor-critic", "refinement"]
keywords: ["ActorCriticEngine", "critic_phase", "synthesis_phase", "automated_loop"]
related: ["context.md", "../../engines/sequential/logic_control.md"]
importance: 95
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T00:00:00Z"
---

## Raw Concept

**Task:**
Automate the iterative refinement of a proposal by generating an internal dialogue between a critical "adversary" and a constructive "synthesizer."

**Files:**
- `src/modes/hybrids/actor_critic/orchestrator.py`

**Flow:**
1. **Target Identification**: Specify a previously generated thought (`target_thought_id`).
2. **Phase 1: The Critic**: Automated generation of an evaluative thought that "attacks" the target's weaknesses.
3. **Phase 2: The Synthesis**: Automated generation of a refined proposal that resolves the criticisms.

## Narrative

### The Refinement Engine
The `ActorCriticEngine` is a heavy-duty hybrid mode designed to eliminate high-level logical errors before they reach final implementation. It automates two cognitive steps in a single execution flow:

- **The Critic (Critical Pillar)**: The system simulates a specialized persona (e.g., "Senior Security Architect") to scan for vulnerabilities, bottlenecks, or flaws. This step is explicitly marked with `contradicts=[target_id]` to maintain logical integrity in the graph.
- **The Synthesis (Creative + Critical Junction)**: The system then generates a resolution that builds on both the original proposal and the newly generated criticisms. By marking this as `is_revision=True`, the engine triggers the **Revision Grace Period** in the `SequentialEngine`, allowing for deeper reasoning beyond normal caps.

### Architectural Benefits
By automating this dialogue, the CCT server ensures that complex ideas are not accepted without objective review. The system forces a **Critical Pivot** by injecting an adversary into the reasoning path, resulting in high-density, battle-tested solutions that are significantly more robust than those produced by a linear creative flow.

## Facts
- **internal_automation_tag**: Both phases use `[INTERNAL AUTOMATION]` markers in their prompts to signal to the LLM (and user) that this is a system-steered reasoning loop. [convention]
- **branch_isolation**: The Critic phase is isolated into a `critic_branch` to prevent it from cluttering the primary solution path unless synthesis is successful. [logic]
- **simulated_stepping**: The engine manually increments `llm_thought_number` for each phase to ensure the `SequentialEngine` remains synchronized during multi-phase execution. [sequential]
- **dialectical_strategy**: The synthesis phase uses `ThinkingStrategy.DIALECTICAL`, signaling a fusion of opposing ideas. [strategy]
