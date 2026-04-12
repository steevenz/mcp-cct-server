# Architecture Overview

## High-Level Purpose

CCT MCP Server menyediakan “reasoning structure” untuk LLM melalui:

- **Session state yang persisten** (SQLite) untuk menyimpan sejarah reasoning.
- **Strategy registry** untuk memilih mesin (primitive/hybrid) berdasarkan `ThinkingStrategy`.
- **Sequential integrity** untuk mencegah “skip step” atau hallucination pada urutan berpikir.
- **Tool boundary** (MCP tools) sebagai API publik untuk memulai session, menjalankan step, dan export/analyze.

## System Context (C4: Context)

```mermaid
flowchart LR
  user[Developer / IDE Client] -->|MCP calls| server[CCT MCP Server]
  server -->|stores| sqlite[(SQLite cct_memory.db)]
  server -->|optional read| pricing[(datasets/pricing.json)]
  user -->|launch| dashboard[Streamlit Dashboard]
  dashboard -->|reads same DB| sqlite
```

## Container/Component View (C4: Component)

```mermaid
flowchart TB
  subgraph API[API Boundary: MCP Tools]
    t_session[src/tools/session_tools.py]
    t_cognitive[src/tools/cognitive_tools.py]
    t_export[src/tools/export_tools.py]
  end

  subgraph App[Application Layer]
    orch[src/engines/orchestrator.py\nCognitiveOrchestrator]
    registry[src/modes/registry.py\nCognitiveEngineRegistry]
  end

  subgraph Engines[Domain Services / Engines]
    mem[src/engines/memory/manager.py\nMemoryManager]
    seq[src/engines/sequential/engine.py\nSequentialEngine]
  end

  subgraph Modes[Strategy Engines]
    prim[src/modes/primitives/orchestrator.py\nDynamicPrimitiveEngine]
    ac[src/modes/hybrids/actor_critic/orchestrator.py\nActorCriticEngine]
    lat[src/modes/hybrids/lateral/orchestrator.py\nLateralEngine]
    tmp[src/modes/hybrids/temporal/orchestrator.py\nLongTermHorizonEngine]
    maf[src/modes/hybrids/multi_agent/orchestrator.py\nMultiAgentFusionEngine]
  end

  API --> orch
  orch --> registry
  registry --> prim
  registry --> ac
  registry --> lat
  registry --> tmp
  registry --> maf

  prim --> mem
  prim --> seq
  ac --> mem
  ac --> seq
  lat --> mem
  lat --> seq
  tmp --> mem
  tmp --> seq
  maf --> mem
  maf --> seq
```

## Runtime Flow (Sequence)

### 1) Start Session

```mermaid
sequenceDiagram
  participant Client as IDE Client
  participant Tool as start_cct_session()
  participant Orch as CognitiveOrchestrator
  participant Pip as PipelineSelector
  participant Mem as MemoryManager
  participant DB as SQLite

  Client->>Tool: problem_statement, profile
  Tool->>Orch: start_session(problem_statement, profile)
  Orch->>Pip: select_pipeline(problem_statement)
  Orch->>Mem: get_relevant_knowledge(problem_statement)
  Mem->>DB: SELECT skills + anti_patterns
  Orch->>Mem: create_session(problem_statement, profile, estimated_thoughts)
  Mem->>DB: INSERT sessions
  Orch->>Mem: update_session(enriched session)
  Mem->>DB: UPDATE sessions
  Orch-->>Tool: session_id + dynamic_pipeline + injected counts
  Tool-->>Client: JSON response
```

### 2) Think Step (Primitive)

```mermaid
sequenceDiagram
  participant Client as IDE Client
  participant Tool as cct_think_step()
  participant Orch as CognitiveOrchestrator
  participant Reg as CognitiveEngineRegistry
  participant Eng as DynamicPrimitiveEngine
  participant Seq as SequentialEngine
  participant Mem as MemoryManager
  participant DB as SQLite

  Client->>Tool: session_id + payload
  Tool->>Orch: execute_strategy(session_id, strategy, payload)
  Orch->>Reg: get_engine(strategy)
  Reg-->>Orch: engine instance
  Orch->>Eng: execute(session_id, payload)
  Eng->>Seq: process_sequence_step(...)
  Seq->>Mem: get_session(session_id)
  Mem->>DB: SELECT session JSON
  Seq->>Mem: update_session(mutated counters)
  Mem->>DB: UPDATE session JSON
  Eng->>Mem: save_thought(session_id, thought)
  Mem->>DB: INSERT thought + UPDATE session history_ids
  Eng-->>Orch: status + generated_thought_id
  Orch-->>Tool: result
  Tool-->>Client: JSON response
```

## Data Model & Storage (SQLite)

### Logical Tables

- `sessions(session_id, data JSON)` — `CCTSessionState` sebagai JSON blob.
- `thoughts(thought_id, session_id, data JSON)` — `EnhancedThought` sebagai JSON blob.
- `skills(skill_id, thought_id, usage_count, data JSON)` — `GoldenSkill`.
- `anti_patterns(failure_id, thought_id, failed_strategy, category, data JSON)` — `AntiPattern`.

```mermaid
erDiagram
  SESSIONS ||--o{ THOUGHTS : has
  THOUGHTS ||--o{ SKILLS : may_archive_as
  THOUGHTS ||--o{ ANTI_PATTERNS : may_log_as

  SESSIONS {
    TEXT session_id PK
    JSON data
  }
  THOUGHTS {
    TEXT thought_id PK
    TEXT session_id FK
    JSON data
  }
  SKILLS {
    TEXT skill_id PK
    TEXT thought_id
    INT usage_count
    JSON data
  }
  ANTI_PATTERNS {
    TEXT failure_id PK
    TEXT thought_id
    TEXT failed_strategy
    TEXT category
    JSON data
  }
```

## Key Design Patterns

- **Facade / Application Service**: `CognitiveOrchestrator` sebagai single entry point untuk eksekusi strategi.
- **Registry + Factory**: `CognitiveEngineRegistry` memetakan `ThinkingStrategy` → engine; primitives memakai `DynamicPrimitiveEngine` untuk menghindari duplikasi.
- **Document Store Pattern**: SQLite menyimpan Pydantic models sebagai JSON blob untuk fleksibilitas schema.
- **Telemetry & Token Economy** (partial): `ContextPruner` dan `TokenHarness` menyediakan pola untuk kontrol konteks dan biaya.

