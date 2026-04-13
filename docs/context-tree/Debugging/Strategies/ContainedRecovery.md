---
title: "Self-Debugging: Contained Recovery"
tags: ["debugging", "recovery", "heuristics"]
keywords: ["minimal-action", "scope-reduction", "context-trimming"]
related: ["./context.md"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Execute the smallest safe action that changes the diagnostics surface.
**Heuristics:** Restate Objective, Verify State, Shrink Scope, Run Probe.
**Files:** `src/engines/skills_loader.py` (ContainedRecoverer)

## Narrative
Once diagnosed, recovery must be **contained**. Large, speculative retries often make the problem worse. The agent should choose an intervention from the standard recovery hierarchy.

### Recovery Heuristics (Order of Preference)
1. **Restate Objective**: Summarize the real goal in one sentence to reset focus.
2. **Verify World State**: Don't trust memory; run a `ls` or `view_file` to confirm facts.
3. **Shrink Scope**: Narrow the task to one failing command or one specific file.
4. **Run One Probe**: Execute one discriminating command to see if the state changed.
5. **Only Then Retry**: Re-attempt the original task with the new adjustments.

## Facts
- **minimal_recovery**: The principle of using the least intrusive fix first.
- **context_trimming**: Removing low-signal data to increase reasoning quality.
