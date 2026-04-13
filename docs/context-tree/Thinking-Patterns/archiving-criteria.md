---
title: "Thinking Patterns: Archiving Criteria"
tags: ["patterns", "archiving", "heuristics"]
keywords: ["logic-score", "evidence-score", "thresholds", "extraction"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Archiving Criteria

## Overview
The Archiving Criteria topic defines the automated filters used by the `PatternArchiver` to identify "high-value" cognitive steps. Not all thoughts are worthy of long-term persistence; only those that exhibit exceptional logical rigor and empirical grounding are promoted to the Context Tree.

## Key Concepts
- **The 0.9 / 0.8 Rule**:
    - **Logic Score >= 0.9**: The thought must represent a flawless architectural or logical derivation.
    - **Evidence Score >= 0.8**: The thought must be backed by strong empirical observation or search data.
- **Novelty Factor**: The `novelty_sampling` algorithm prioritizes thoughts that introduce unique perspectives not already covered by existing patterns in the database.
- **Structural Integrity**: Candidate patterns undergo a schema validation check before being exported as Markdown artifacts with mandatory YAML frontmatter.

## Narrative
The system operates as a filter. During the convergence phase, the `PatternArchiver` scans the successful session branch. If a thought meets the thresholds, it is "Naturalized":
1.  **Extraction**: The thought's narrative and metadata are extracted.
2.  **Archiving**: It is saved to the `thinking_patterns` SQLite table.
3.  **Export**: A Markdown file is generated in `docs/context-tree/thinking-patterns/Generated/` for human review and future AI bootstrapping.

## Related Topics
- [./context.md](./context.md)
- [../analysis/Scoring/context.md](../analysis/scoring/context.md)
