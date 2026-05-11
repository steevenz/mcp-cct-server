# Thinking Flow Architecture

**Research & Design for MCP Cognitive Computing Toolkit**

---

## 1. Core Research Papers

| Paper | Year | Key Insight | Neural Correlate |
|-------|------|-------------|-----------------|
| **Chain-of-Thought Prompting Elicits Reasoning in Large Language Models** (Wei et al.) | 2022 | Intermediate reasoning steps significantly improve complex reasoning. 540B model + 8 exemplars = SOTA on GSM8K | DLPFC — sequential reasoning, step-by-step decomposition |
| **Tree of Thoughts: Deliberate Problem Solving with LLMs** (Yao et al.) | 2023 | Exploration over coherent units of text (thoughts) with self-evaluation. GPT-4 CoT: 4% → ToT: 74% on Game of 24 | PFC + Basal Ganglia — multiple working memory buffers, explore-exploit |
| **ReAct: Synergizing Reasoning and Acting in Language Models** (Yao et al.) | 2022 | Interleave reasoning traces with action execution. Reasoning improves action planning, actions provide external observations | PFC + Motor Cortex — think-do-observe loop |
| **ReWOO: Reasoning Without Observation** (Xu et al.) | 2023 | Plan all actions upfront, then execute. Reduces token usage by avoiding interleaved reasoning | PFC Planning + Hippocampus — plan-first methodology |

## 2. Key Findings

### These patterns are NOT replacements — they are THINKING PHASES:

```
Phase 1: FRAME    ─→ CoT decomposes problem into sub-components
Phase 2: DIVERGE  ─→ ToT explores multiple solution paths
Phase 3: ANALYZE  ─→ ReAct thinks while doing (agentic)
Phase 4: PLAN     ─→ ReWOO plans first, then executes
Phase 5: STRESS   ─→ Actor-Critic stress-tests the chosen path
Phase 6: SYNTHESIS ─→ Council integrates multiple perspectives
Phase 7: META     ─→ Reflect, consolidate, learn
```

### What Makes Each Pattern Effective:

**CoT (Chain of Thought):**
- Decompose problem into intermediate steps
- Each step produces a coherent thought
- Steps connect logically: step_n → step_{n+1}
- Works because: forces LLM to show work, not jump to conclusion

**ToT (Tree of Thoughts):**
- Four operations:
  1. **Thought decomposition**: break problem into intermediate steps
  2. **Thought generation**: generate candidate next steps (proposal or sampling)
  3. **State evaluation**: evaluate each state's promise (value or voting)
  4. **Search algorithm**: BFS, DFS, lookahead, backtracking
- Works because: avoids local optima, explores multiple paths

**ReAct (Reason + Act):**
- Interleave reasoning traces (thought) with actions (act) and observations
- Three components:
  1. **Thought**: Reason about current state and next action
  2. **Act**: Execute an action (tool call, query, etc.)
  3. **Observe**: Process the result of the action
- Works because: external feedback prevents hallucination loops

**ReWOO (Reasoning Without Observation):**
- Two phases:
  1. **Planning**: Generate complete reasoning and action plan upfront
  2. **Execution**: Execute all planned actions without intermediate reasoning
- Works because: reduces token waste, better for well-understood tasks

## 3. Neural Architecture Mapping

```
Cerebral Cortex Analogy:

Prefrontal Cortex (Executive)
  ├── CoT  → Dorsolateral PFC (working memory, sequential reasoning)
  ├── ToT  → Ventromedial PFC (value comparison, exploration)
  ├── ReAct → Orbitofrontal PFC (action-outcome learning)
  └── ReWOO → Anterior PFC (planning, goal hierarchy)

Basal Ganglia (Action Selection)
  ├── ToT branching → Explore/Exploit switching
  └── ReAct action selection → Go/No-Go pathways

Hippocampus (Memory)
  ├── Pattern consolidation → Episodic → Semantic transfer
  └── Similarity matching → Relevance detection

Amygdala (Salience)
  └── Critical review → Threat detection, error avoidance
```

## 4. Proposed Thinking Flow State Machine

```
                         ┌─────────────────┐
                         │   FRAME PHASE   │
                         │  (CoT scaffold) │
                         │  reframe_problem│
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  DIVERGE PHASE  │
                         │  (ToT scaffold) │
                         │ brainstorm_alt. │
                         └────────┬────────┘
                                  │
                   ┌──────────────┼──────────────┐
                   │              │              │
           ┌───────▼──────┐ ┌────▼────┐ ┌───────▼──────┐
           │ Linear Path  │ │ Agentic │ │ Batch Plan   │
           │  (CoT)       │ │ (ReAct)  │ │ (ReWOO)      │
           └───────┬──────┘ └────┬────┘ └───────┬──────┘
                   │              │              │
                   └──────────────┼──────────────┘
                                  │
                         ┌────────▼────────┐
                         │  STRESS TEST    │
                         │ Actor-Critic    │
                         │ Council         │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  SYNTHESIS      │
                         │ decompose       │
                         │ evaluate        │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  META PHASE     │
                         │ review_thinking │
                         │ consolidate     │
                         └─────────────────┘
```

## 5. Implementation Principle

Each planning engine is a **cognitive scaffold** — it provides:

1. **Structured prompt template**: Kerangka berpikir, bukan konten
2. **Output schema**: LLM tahu format output yang diharapkan  
3. **Decision criteria**: Kapan lanjut, pivot, atau stop
4. **Evaluation rubric**: Cara menilai kualitas output

The MCP server does NOT generate content — it structures HOW the LLM thinks.
