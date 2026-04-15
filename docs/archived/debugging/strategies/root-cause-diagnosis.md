---
title: "Self-Debugging: Root-Cause Diagnosis"
tags: ["debugging", "diagnosis", "root-cause"]
keywords: ["loop-detection", "task-drift", "state-mismatch"]
related: ["./context.md"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Identify the "Why" behind the failure using pattern matching.
**Patterns:** Loop, Drift, Burn, State-Mismatch, Token-Burn.
**Files:** `src/engines/skills_loader.py` (RootCauseDiagnostician)

## Narrative
Diagnosis is the process of matching captured failure state to known **Anti-Patterns**. Instead of guessing, the agent must use a discriminative process to categorize the failure.

### Diagnostic Questions
1. **Is it a Loop?**: Are we calling the same tool with the same input repeatedly?
2. **Is it Drift?**: Have we lost the original objective in a sea of sub-tasks?
3. **Is it Environment?**: Does the file we expect actually exist on disk (vs. in memory)?
4. **Is it Policy?**: Are we hitting a safety or permission bound?

## Facts
- **pattern_matching**: Matching current failure to historical Anti-Patterns in the database.
- **deterministic_check**: Determining if the error will repeat with the same inputs.
