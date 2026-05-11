# Golden Features Audit: Unwired, Dead, and Broken Code

**Audit Date**: 2026-05-09 | **Scope**: Full codebase analysis

---

## 1. CRITICAL BUG: `MultiAgentFusionEngine` is Broken

**File**: `src/modes/hybrids/multiagents/orchestrator.py:145`

```python
# LINE 145 — MISSING AWAIT
fusion_thought = self.fusion.fuse_thoughts(  # ← missing await!
    session_id=session_id,
    thought_ids=[n.id for n in persona_nodes],
    ...
)
fusion_thought.id  # ← AttributeError: 'coroutine' object has no attribute 'id'
```

`fuse_thoughts` is `async def` but called without `await`. This causes a **silent coroutine leak** — the function never executes, and accessing `.id` crashes. The entire Multi-Agent Fusion pipeline (divergent persona generation → convergent synthesis) is **non-functional**.

**Fix**: Add `await` keyword.

---

## 2. 34 Hollow Primitive Strategies

All 34 `ThinkingStrategy` values route to `DynamicPrimitiveEngine` which does the **exact same thing** for every strategy:

| Strategy | What it Actually Does | What it Should Do |
|----------|----------------------|-------------------|
| `CHAIN_OF_THOUGHT` | Logs thought + tags it | Generates step-by-step scaffold with 5 reasoning steps |
| `TREE_OF_THOUGHTS` | Logs thought + tags it | Creates branching structure with 3 candidate paths per node |
| `REACT` | Logs thought + tags it | Produces think→act→observe loop scaffold |
| `REWOO` | Logs thought + tags it | Produces plan→execute structure scaffold |
| `FIRST_PRINCIPLES` | Logs thought + tags it | Decomposes to atomic assumptions |
| All 34 | Same generic logic | Different cognitive algorithm per strategy |

**Fix**: Differentiate `DynamicPrimitiveEngine` per strategy using the standalone planning engines (CoT, ToT, ReAct, ReWOO) as reference implementations.

---

## 3. 30 Dead MCP Tools (4 Registration Functions Never Called)

`main.py` only calls `register_simplified_tools()`. Four other registration files exist but are **never invoked**:

| File | Tools Inside | Lines of Code |
|------|-------------|---------------|
| `src/tools/session.py` | 7 tools (`start_cct_session`, `list_cct_sessions`, etc.) | ~200 |
| `src/tools/export.py` | 2 tools (`export_thinking_session`, `analyze_session`) | ~100 |
| `src/tools/engineering.py` | 10+5 tools (`define_eval_criteria`, `execute_react`, etc.) | ~300 |
| `src/tools/cognitive.py` | 6 tools (`cct_think_step`, `cct_log_failure`, etc.) | ~150 |

**Note**: Some are duplicates of simplified tools (e.g., `define_eval_criteria` → `evaluate_thinking`). But `register_planning_tools()` provides direct standalone CoT/ToT/ReAct/ReWOO interfaces that the simplified `plan_thinking` wrapper doesn't expose.

---

## 4. 8 Dead Services (~1,800 Lines of Orphaned Code)

| Service | Lines | What It Does | Why It Matters for Thinking Flow |
|---------|-------|-------------|----------------------------------|
| `src/engines/planning/react.py` | 161 | ReAct think→act→observe engine | **Strategic**: powers agentic reasoning in Analysis Phase |
| `src/engines/planning/rewoo.py` | 145 | ReWOO plan→execute engine | **Strategic**: powers planning in Synthesis Phase |
| `src/engines/planning/chainofthought.py` | 142 | CoT step-by-step engine | **Strategic**: powers decomposition in Frame Phase |
| `src/engines/planning/threeofthoughts.py` | 222 | ToT branching engine | **Strategic**: powers exploration in Diverge Phase |
| `src/core/services/analysis/bias.py` | 350 | Cognitive bias detection | **Tactical**: could power audit/quality checks |
| `src/core/services/detector/convergence.py` | 345 | 6-factor convergence detection | **Tactical**: could improve early-stop decisions |
| `src/core/services/analysis/metrics.py` | 230 | Engine performance metrics | **Tactical**: could power observability dashboard |
| `src/core/services/llm/monitor.py` | 60 | LLM monitoring service | **Tactical**: could track cost/usage per session |

**Key insight**: The 4 planning engines (CoT, ToT, ReAct, ReWOO) are NOT dead code — they are **reference implementations** that should power the primitive strategies in `DynamicPrimitiveEngine`. They're just not wired.

---

## 5. Dual-Path Confusion: Planning Engines X 2

The 4 planning strategies exist in **two competing paths**:

```
Path A: plan_thinking(pattern="cot") → CoTEngine directly (standalone, no session)
Path B: continue_thinking(strategy="chain_of_thought") → DynamicPrimitiveEngine → generic thought logger (with session)
```

Same strategy name, completely different behavior depending on which tool calls it. Path A does actual CoT scaffold (though hardcoded), Path B just tags the thought.

**Fix**: Unify — `DynamicPrimitiveEngine` should delegate to the specific planning engine for each strategy type.

---

## 6. `ConvergenceService`: Elite Detection Not Used

`src/core/services/detector/convergence.py` implements a sophisticated 6-factor convergence model:
- Coherence streak (2+ consecutive high-coherence thoughts)
- Evidence strength
- Persona insight density
- No quality degradation
- Conclusion type detection
- Revision stability

Currently, `SequentialEngine.evaluate_convergence()` uses a much simpler 2-factor heuristic (coherence + evidence only). Wiring `ConvergenceService` would enable earlier and more accurate convergence detection, saving tokens.

---

## 7. Thinking Flow Mapping

### Current (Broken):
```
FRAME ──→ DIVERGE ──→ ANALYZE ──→ STRESS ──→ SYNTHESIS ──→ META
  ❌        ❌         ⚠️          ✅          ⚠️           ❌
No tool   No tool    CoT/ToT not  Actor-     ReWOO not     No reflection
                     differen-    Critic     differen-
                     tiated       wired      tiated
```

### Proposed (Fixed):
```
FRAME ──→ DIVERGE ──→ ANALYZE ──→ STRESS ──→ SYNTHESIS ──→ META
  │         │          │           │           │            │
reframe   brainstorm  continue    actor_     decompose    review_
_problem  _alternatives_thinking  critic     _thinking    thinking
  │         │          │           │           │            │
  CoT       ToT       CoT/ReAct   Council    ReWOO        consolidate
                     differentiated           differentiated
```

---

## Implementation Priority

| # | Fix | Impact | Effort | Type |
|---|-----|--------|--------|------|
| 1 | ✅ Fix `await` bug in MultiAgentFusion | Critical | 1 line | Bug |
| 2 | 🎯 Differentiate DynamicPrimitiveEngine per strategy | High | Medium | Feature |
| 3 | 🎯 Wire planning engines (CoT/ToT/ReAct/ReWOO) into primitives | High | Medium | Feature |
| 4 | 🆕 Add `reframe_problem` tool (Frame Phase) | High | Low | New |
| 5 | 🆕 Add `brainstorm_alternatives` tool (Diverge Phase) | High | Low | New |
| 6 | 🆕 Add `review_thinking` tool (Meta Phase) | Medium | Low | New |
| 7 | ⚡ Wire ConvergenceService into SequentialEngine | Medium | Low | Enhancement |
| 8 | 🔌 Activate dead register_planning_tools() | Medium | Low | Activation |
