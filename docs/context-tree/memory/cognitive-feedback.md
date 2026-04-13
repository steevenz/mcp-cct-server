---
title: "Cognitive Feedback: Pattern Archiving & Anti-Patterns"
tags: ["memory", "feedback", "patterns", "archiving", "growth"]
keywords: ["golden_pattern", "antipattern", "archiver", "feedback_loop", "threshold"]
related: ["context.md", "Persistence/sqlite_schema.md"]
importance: 85
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T00:00:00Z"
---

## Raw Concept

**Task:**
Automatically capture high-quality cognitive strategies and documented reasoning failures to build a self-improving persistent knowledge base.

**Files:**
- `src/engines/memory/thinking_patterns.py`

**Flow:**
1. A thought is generated and scored.
2. `PatternArchiver` checks if scores meet the **Elite Threshold** (Logic > 0.9, Evidence > 0.8).
3. If elite, the thought is converted into a `GoldenThinkingPattern`.
4. The pattern is persisted in SQLite AND exported as a Markdown file to the `Thinking-Patterns` domain.

## Narrative

### Structure: The Recursive Feedback Loop
The C&C Framework is built on the idea of **Evolutionary Reasoning**. The `PatternArchiver` acts as the natural selection mechanism:
- **Golden Thinking Patterns**: These are successfully executed strategies that solved a complex part of a problem statement. They serve as references for future sessions.
- **Anti-Patterns**: When a strategy fails or bias is detected, it is logged as an `AntiPattern`. This creates an "Immune System" that warns the AI against repeating similar cognitive mistakes.

### Archiving Rules
- **Automatic Export**: Every Golden Pattern is automatically formatted according to the Context Tree standard and written to `docs/context-tree/thinking-patterns/{StrategyName}/{TP_ID}.md`.
- **Usage Tracking**: Each time a pattern is referenced or contributes to a new solution, its `usage_count` is incremented in the database, allowing the system to identify "battle-tested" logic.

### C&C Framework Alignment
- **Creative Source**: Golden Patterns provide the "seeds" for future creative expansion within similar domains.
- **Critical Shield**: Anti-Patterns provide the critical filters needed to avoid known pitfalls.

## Facts
- **elite_logic_threshold**: Set to `0.9` for logical coherence. Only the top ~5% of thoughts typically reach this. [threshold]
- **cross_session_learning**: Patterns archived in Session A are immediately available as "relevant knowledge" for Session B via simple keyword mapping. [memory]
- **markdown_synchronization**: The system maintains parity between the structured SQLite database and the human-readable Markdown Context Tree. [bridge]
