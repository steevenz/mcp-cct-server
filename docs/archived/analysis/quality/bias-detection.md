---
title: "Technical: Cognitive Bias Detection"
tags: ["analysis", "quality", "bias", "guardrails"]
keywords: ["flags", "regex", "oversimplification", "anchoring"]
related: ["context.md"]
importance: 70
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

## Raw Concept

**Task:**
Identify and flag linguistic markers of cognitive bias in real-time during the reasoning process.

**Files:**
- `src/analysis/bias.py`
- `src/analysis/quality.py`

**Flow:**
Input Text -> Multicast Regex Match -> Categorize Flags -> Append to Thought Metadata.

## Narrative

### Structural Detection
Bias detection in the CCT server is implemented as a lightweight, rule-based filter. It identifies linguistic "red flags" that indicate a breakdown in the **Critical** pillar.

**Core Bias Categories:**
1. **Oversimplification**: Identifying phrases like "obviously," "just," or "simple fix" that may bypass deep complexity analysis.
2. **False Certitude**: Detecting absolute statements in ambiguous domains (e.g., "always," "never").
3. **Emotional Anchoring**: Flagging hyperbole or emotionally charged language that might skew objective reasoning.
4. **Logical Leaps**: Identifying missing causal links (e.g., "therefore" without preceding evidence).

### Rules
- **Non-Blocking**: Bias detection never stops the execution flow; it only adds metadata to the thought node.
- **Reporting**: Aggregated bias flags are displayed in the session summary and used by the `FusionOrchestrator` to decide if a "Counter-Bias" strategy is needed.

## Facts
- **regex_engine**: Uses Python's standard `re` module with pre-compiled patterns for O(1) matching per categories. [tech]
- **session_threshold**: If a session accumulates >3 unique bias flags, the `AutomaticPipelineRouter` may trigger a pivot to `SYSTEMATIC` or `ANALYTICAL` engines. [heuristic]
