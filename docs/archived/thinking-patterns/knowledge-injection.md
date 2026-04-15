---
title: "Thinking Patterns: Knowledge Injection"
tags: ["patterns", "injection", "bootstrap", "memory"]
keywords: ["pre-computation", "semantic-search", "warm-start", "context-injection"]
importance: 85
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Knowledge Injection

## Overview
Knowledge Injection is the mechanism by which the CCT server performs "Cognitive Warm-starting." Instead of every session starting from a blank slate, the `CognitiveOrchestrator` semanticly searches the patterns database for relevant historical successes and injects them as **Pre-Computation Context**.

## Key Concepts
- **Domain Matching**: Patterns are tagged with domains (e.g., `Security`, `API`, `Database`). When a new mission description is received, the system retrieves patterns from matching or related domains.
- **Pre-Computation Context**: Injected patterns are placed at the beginning of the prompt, instructing the LLM to "Adopt the reasoning strategies observed in these elite examples."
- **Evolutionary Advantage**: This process ensures that the system doesn't just memorize *facts*, but inherits *methodologies* from previous successes.

## Narrative
The lifecycle of injection:
1.  **Semantic Retrieval**: During Phase 0 (Routing), the system queries the `thinking_patterns` table using key terms from the user request.
2.  **Selection**: The top $N$ patterns with the highest logic scores are selected.
3.  **Injection**: These patterns are formatted and prepended to the system message, effectively "leveling up" the AI's persona for that specific mission.

## Related Topics
- [./context.md](./context.md)
- [../orchestration/context.md](../orchestration/context.md)
