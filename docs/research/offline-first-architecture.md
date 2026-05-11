# Symbiotic Architecture: Offline-First, MCP Sampling-Escalate

## Design Philosophy

**Offline-First**: Setiap interaksi user dianalisa offline dulu menggunakan embedded Gemma. Online cloud LLM **TIDAK PERLU API KEY** — menggunakan MCP Sampling untuk minta tolong LLM client yang sudah terhubung.

**Key Insight**: LLM yang request (claude, GPT, dll via IDE) bisa dipakai sebagai "online tier" melalui MCP Sampling protocol. Server tidak perlu API key sendiri.

**Neural Analogy**:
- Gemma 2B = Reflex (automatic, fast, always on)
- Gemma 9B = Cortex (reasoning capable, in-package)
- Client LLM via Sampling = Prefrontal Cortex (deep thinking, provided by IDE)

---

## Three-Tier LLM Stack (Gemma Series)

```
TIER 1: GEMMA 2B EMBEDDED (llama-cpp-python)
┌─────────────────────────────────────────────┐
│  Model: Gemma-2-2B-it-Q4_K_M.gguf           │
│  RAM: ~1.2GB  ← PALING RENDAH               │
│  Speed: ~40 tok/s (CPU, 4 threads)          │
│  Cost: FREE, always available               │
│  Tasks:                                      │
│  ├─ Pattern extraction dari sesi             │
│  ├─ User behavior classification             │
│  ├─ Thinking quality scoring                 │
│  ├─ Cognitive bias detection                 │
│  ├─ Strategy tagging                         │
│  ├─ Lightweight reasoning (QA sederhana)     │
│  └─ Confidence scoring                       │
└─────────────────────────────────────────────┘
         │ failover (low confidence / perlu reasoning lebih)
         ▼
TIER 2: GEMMA 9B EMBEDDED (llama-cpp-python)
┌─────────────────────────────────────────────┐
│  Model: Gemma-2-9B-it-Q4_K_M.gguf           │
│  RAM: ~5.5GB                                │
│  Speed: ~12 tok/s (CPU, 8 threads)          │
│  Cost: FREE, included in package            │
│  Tasks:                                      │
│  ├─ Deep pattern clustering                  │
│  ├─ User behavior trend detection            │
│  ├─ Strategy success analysis                │
│  ├─ Dynamic mindset generation               │
│  ├─ Reasoning untuk review_thinking          │
│  ├─ Decomposition tugas sederhana            │
│  └─ Fallback reasoning ketika client LLM     │
│     tidak tersedia (offline total)            │
└─────────────────────────────────────────────┘
         │ failover (perlu complex reasoning, creative)
         ▼
TIER 3: CLIENT LLM via MCP SAMPLING (No API Key!)
┌─────────────────────────────────────────────┐
│  Sumber: LLM yang sudah terhubung via MCP   │
│  (Claude, GPT, Gemini di IDE user)           │
│  Protocol: sampling/createMessage            │
│  Cost: Ditanggung user (via IDE mereka)      │
│  Tasks:                                      │
│  ├─ Deep reasoning (Actor-Critic loop)       │
│  ├─ Creative thinking (Lateral Pivot)        │
│  ├─ Complex problem decomposition            │
│  ├─ Council of Critics (multi-perspective)   │
│  ├─ Temporal Horizon projection              │
│  └─ ANY task where offline confidence < 0.4  │
└─────────────────────────────────────────────┘
```

---

## Why Gemma (bukan Qwen/Llama)

| Model | RAM (Q4) | Kelebihan |
|-------|----------|-----------|
| **Gemma 2 2B** | **~1.2 GB** | Paling ringan, cukup untuk klasifikasi + pattern extraction |
| Gemma 2 9B | ~5.5 GB | Reasoning capable, fallback offline |
| Gemma 3 27B | ~15 GB | Opsional, kalau RAM tersedia |
| Qwen 1.5B | ~1.5 GB | Lebih berat dari Gemma 2B |
| Llama 3B | ~2 GB | Lebih berat dari Gemma 2B |

**Gemma 2 2B Q4_K_M = rekomendasi untuk Tier 1** karena:
- Hanya ~1.2GB RAM — jalan di laptop mana pun
- Instruct-tuned — cocok untuk classification & extraction
- Tokenizer efisien untuk coding/technical text

---

## How MCP Sampling Replaces Online API

```python
# Server TIDAK butuh API key. Pake client LLM via Sampling:
async def tier3_reasoning(prompt: str, session) -> str:
    """
    Minta client LLM untuk deep reasoning.
    Client = Claude/GPT/Gemini yang ada di IDE user.
    """
    result = await session.sampling.create_message(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        model_preferences={
            "hints": [{"name": "claude-3-sonnet"}, {"name": "gpt-4o"}],
            "intelligencePriority": 0.9,
            "costPriority": 0.3,
        },
    )
    return result.content.text
```

**Keuntungan:**
- ✅ Server tidak perlu API key OpenAI/Anthropic
- ✅ User pake LLM favorit mereka sendiri
- ✅ Biaya ditanggung user (via IDE subscription)
- ✅ Privacy lebih terjaga (data tetap di client LLM)
- ✅ Support multi-provider otomatis

---

## Complete Data Flow

```
USER MELALUI IDE (Claude/GPT/etc)
    │
    ├─ MCP Request → tools/call
    │
    ▼
┌─────────────────────────────────────────────┐
│  MCP SERVER                                 │
│  ┌───────────────────────────────────────┐  │
│  │ Thinking Strategy Execution           │  │
│  │ - CoT, ToT, ReAct, Actor-Critic      │  │
│  │ - EKSEKUSI: client LLM via Sampling  │  │
│  │   (karena butuh reasoning dalam)      │  │
│  └──────────────────┬────────────────────┘  │
│                     │                        │
│              Session Complete                 │
│                     │                        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │ AUTO: Hippocampus.analyze_session()   │  │
│  └──────────────────┬────────────────────┘  │
│                     │                        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │ TIER 1: Gemma 2B (embedded)           │◄─┤ GRATIS
│  │ Extract preferences from thoughts     │  │
│  │ Classify strategies used              │  │
│  │ Score thought quality                 │  │
│  │ Detect cognitive biases               │  │
│  │ Confidence scoring                    │  │
│  └──────────────────┬────────────────────┘  │
│                     │                        │
│          if confidence < 0.5                 │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │ TIER 2: Gemma 9B (embedded)           │  │
│  │ Deep pattern clustering               │  │
│  │ Behavior trend detection              │  │
│  │ Generate dynamic mindset              │  │
│  └──────────────────┬────────────────────┘  │
│                     │                        │
│          if masih perlu deep reasoning       │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │ TIER 3: Client LLM via MCP Sampling   │  │
│  │ Complex pattern synthesis             │  │
│  │ Creative insight generation           │  │
│  └───────────────────────────────────────┘  │
│                     │                        │
│                     ▼                        │
│  Update learned_identity.json                │
│  Save ke database (pattern, feedback)        │
└─────────────────────────────────────────────┘
```

---

## How LLMs Are Used

| Task | Gemma 2B | Gemma 9B | Client LLM (Sampling) |
|------|:--------:|:--------:|:--------------------:|
| **Pattern extraction** | ✅ | - | - |
| **Quality scoring** | ✅ | - | - |
| **Bias detection** | ✅ | - | - |
| **Strategy tagging** | ✅ | - | - |
| **Light reasoning** | ✅ | ✅ | - |
| **Behavior clustering** | - | ✅ | - |
| **Trend detection** | - | ✅ | - |
| **Mindset generation** | - | ✅ | - |
| **Deep reasoning** | - | - | ✅ |
| **Creative thinking** | - | - | ✅ |
| **Complex analysis** | - | - | ✅ |
| **Actor-Critic loop** | - | - | ✅ |
| **Fallback reasoning** | - | ✅ | - |

---

## Database Schema Update

```sql
-- User feedback on thinking quality
CREATE TABLE user_feedback (
    feedback_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    thought_id TEXT,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    feedback_type TEXT NOT NULL,
    comment TEXT,
    llm_tier TEXT,           -- 'gemma_2b', 'gemma_9b', 'client_sampling'
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

-- Learned behavior patterns
CREATE TABLE behavior_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    user_id TEXT NOT NULL,
    data JSON NOT NULL,
    confidence REAL DEFAULT 0.5,
    observation_count INTEGER DEFAULT 1,
    first_observed TEXT,
    last_observed TEXT NOT NULL
);

-- Offline analysis cache (hindari reprocessing)
CREATE TABLE offline_analysis_cache (
    cache_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    result JSON NOT NULL,
    llm_tier TEXT NOT NULL,
    confidence REAL,
    created_at TEXT NOT NULL,
    UNIQUE(source_id, analysis_type)
);
```

---

## Implementation Plan

### Phase 1: Wire Learning (No LLM yet)
1. `review_thinking` auto-trigger `analyze_session()`
2. Session completion → auto analyze
3. Database migration (3 new tables)
4. Update `learned_identity.json` from session analysis

### Phase 2: Gemma 2B Embedded
1. Install `llama-cpp-python`
2. Create `src/core/llm_offline/engine.py`
3. Auto-download Gemma 2B GGUF on first run
4. Wire into `analyze_session()` for pattern extraction

### Phase 3: Gemma 9B + MCP Sampling
1. Download Gemma 9B GGUF (optional, in-package)
2. Wire MCP Sampling for Tier 3
3. Smart routing: confidence-based LLM selection

### Phase 4: Symbiotic Loop Complete
1. Auto-learning runs after every session
2. `learned_identity.json` adapts dynamically
3. Next session: personalized prompts + scaffolds

---

## Mandatory vs Optional: Online LLM Analysis

Setelah tracing seluruh codebase, **tidak ada yang mandatory online.**

### Where LLM is Actually Called:

| Engine | File | Online Needed? | Local Gemma 9B Can Handle? |
|--------|------|:--------------:|:--------------------------:|
| ActorCriticEngine (critique) | `modes/hybrids/critics/actor/...` | NO - Optional | YES - Structured critique |
| ActorCriticEngine (refinement) | same file | NO - Optional | YES - Dialectical refinement |
| CouncilOfCritics (persona) | `modes/hybrids/critics/council/...` | NO - Optional | YES - Persona review |
| CouncilOfCritics (synthesis) | same file | NO - Optional | YES - Multi-perspective |
| MultiAgentFusion (persona) | `modes/hybrids/multiagents/...` | NO - Optional | YES - Perspective gen |
| FusionOrchestrator (synthesis) | `engines/fusion/orchestrator.py` | NO - Optional | YES - Pattern synthesis |

### SmartLLMService Decision Flow:

```
generate_thought():
  1. Gemma 9B available?       -> Use it (free, private, always on)
  2. quality_boost=True AND     -> Use online API
     online available?            (better quality, costs money)
  3. No online API?             -> Always use Gemma
  4. No local model?            -> Fallback to online (last resort)
```

**Kesimpulan: SEMUA engine bisa jalan 100% offline dengan Gemma 9B. Online API hanya untuk quality boost ketika user request.**

