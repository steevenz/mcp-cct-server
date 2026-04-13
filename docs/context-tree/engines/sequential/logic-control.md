---
title: "Sequential: Logic Control & The Cognitive Metronome"
tags: ["sequential", "logic", "flow", "metronome"]
keywords: ["integrity", "expansion", "hallucination", "gates"]
related: ["context.md"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

## Raw Concept

**Task:**
Manage the temporal progression of cognitive tasks, ensuring logical path integrity and preventing state explosion.

**Files:**
- `src/engines/sequential/engine.py`

**Flow:**
1. Incoming `process_sequence_step` call.
2. Validate `llm_thought_number` against `expected_thought_number`.
3. Auto-correct hallucinations to maintain persistence state.
4. Calculate dynamic expansion (Revisions vs. Boundaries).
5. Update `CCTSessionState` in Memory.

## Narrative

### The Cognitive Metronome
The `SequentialEngine` acts as a heartbeat for the thinking process. It ensures that every thought is accounted for in a strict linear or branched sequence. By decoupling the "thought number" from the LLM's own estimation, it provides a stable ground truth for the persistence layer.

### Sequence Integrity
LLMs frequently experience "Sequence Hallucination," skipping numbers or jumping ahead. The Sequential Engine intercepts these errors:
- If an LLM claims to be on Thought 5 but the database shows Thought 3 was last, the engine forces the next node to be logged as Thought 4.
- This ensures that the [Timeline View](docs/technical/01-architecture.md) remains coherent for both the user and the system's own recursive learning engines.

### Dynamic Expansion Logic
Unlike rigid sequences, CCT allows the cognitive budget to breathe:
- **Revision Expansion**: When a thought is marked as `is_revision`, the engine adds `REVISION_EXPANSION_INCREMENT` to the budget, acknowledging that deeper thought requires more space.
- **Boundary Extension**: If the user (via LLM) keeps requesting new thoughts while nearing the limit, the engine pushes the boundary further using `BOUNDARY_EXTENSION_INCREMENT`, up to the `MAX_THOUGHTS_PER_SESSION` hard-cap.

## Facts
- **convergence_depth**: A session cannot converge if fewer than 3 thoughts exist. [rule]
- **max_thought_guard [H1]**: A security gate prevents sessions from exceeding 200 thoughts to avoid resource flooding. [security]
- **branching_divergence**: Branching is validated by ensuring the `branch_from_id` actually exists in the SQLite persistence layer before allowing divergence. [integrity]
