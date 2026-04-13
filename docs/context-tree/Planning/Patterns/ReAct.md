---
title: "ReAct: Reason + Act Pattern"
tags: ["react", "dynamic", "observation"]
keywords: ["loop", "adaptive", "interation"]
related: ["./context.md"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

## Raw Concept
**Task:** Dynamically adapt reasoning based on environmental feedback.
**Files:** `src/engines/sequential/engine.py` (Implementation), `src/core/models/enums.py` (Strategy)
**Flow:** Thought → Action → Observation → Result

## Narrative
The ReAct pattern is the cornerstone of dynamic agent behavior. Instead of planning everything upfront, the agent iterates through a loop where it expresses a **Thought** (reasoning about the state), performs an **Action** (calling a tool), and receives an **Observation** (tool output).

### Rules
1. **Never skip observations**: Actions must be informed by previous results.
2. **Explain the "Why"**: Thoughts must clearly state why a specific action is being taken.
3. **Limit loops**: To prevent token waste, a retry limit should be enforced.

### Examples
```markdown
1. Thought: "I need to find the latest stock price for NVIDIA."
2. Action: search_web(query="NVIDIA stock price today")
3. Observation: "NVIDIA (NVDA) is trading at 900.00 USD."
4. Thought: "The price is higher than the set alert. I will notify the user."
```

## Facts
- **dynamic_adaptation**: Ability to change reasoning direction based on real-time data.
- **transparency**: Clear audit trail of why actions were performed.
