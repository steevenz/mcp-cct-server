# Module & Component Guide

## `src/main.py` (Application Entry Point)

Tanggung jawab:

- Setup logging.
- Inisialisasi `FastMCP`.
- Dependency injection untuk `MemoryManager`, `SequentialEngine`, `CognitiveEngineRegistry`, dan `CognitiveOrchestrator`.
- Registrasi tool APIs via:
  - `register_cognitive_tools()`
  - `register_session_tools()`
  - `register_export_tools()`

## `src/core/` (Domain Models & Configuration)

### `src/core/models/enums.py`

- `ThinkingStrategy`: daftar strategi primitive + hybrid.
- `ThoughtType`: tipe step (analysis, synthesis, dll).
- `CCTProfile`: “profile” untuk session (balanced, creative_first, dst).

### `src/core/models/domain.py`

Pydantic models utama:

- `CCTSessionState`: state session yang dipersist.
- `EnhancedThought`: unit “currency” reasoning per step.
- `ThoughtMetrics`, `SessionMetrics`: metrik kualitas.
- `GoldenThinkingPattern`: cognitive pattern yang bagus yang di-archive.
- `AntiPattern`: pattern gagal untuk pencegahan regresi reasoning.

### `src/core/models/schemas.py`

DTO schemas untuk input tool:

- `CCTThinkStepInput` untuk `cct_think_step`.
- `StartCCTSessionInput` (tidak langsung dipakai oleh tool saat ini).

### `src/core/config.py`

`Settings` loader berbasis env var `CCT_*`. Saat ini tidak menjadi single source of truth untuk `src/main.py`.

## `src/engines/` (Application Services)

### `src/engines/orchestrator.py` — `CognitiveOrchestrator`

Facade untuk:

- Menjalankan strategi (routing `ThinkingStrategy` → engine via registry).
- Start session (create session + pipeline suggestion + knowledge injection).

### `src/engines/memory/manager.py` — `MemoryManager`

SQLite-backed persistence:

- Tabel `sessions`, `thoughts`, `thinking_patterns`, `anti_patterns`.
- Menyimpan model sebagai JSON blob (Pydantic `model_dump_json()`).
- Utility untuk retrieving history dan optimized history via `ContextPruner`.

### `src/engines/sequential/engine.py` — `SequentialEngine`

Anti-hallucination backbone untuk urutan step:

- Validasi `thought_number` agar tidak lompat.
- Expand `estimated_total_thoughts` saat revisi/branch.
- Update session state secara persisten (DB).

### `src/engines/sequential/models.py`

- `SequentialContext`: metadata step (revision + branching).

## `src/modes/` (Strategy Engines)

### `src/modes/base.py`

Kontrak engine:

- `strategy_type: ThinkingStrategy`
- `execute(session_id, input_payload) -> dict`

### `src/modes/registry.py` — `CognitiveEngineRegistry`

Pemetaan strategy → engine:

- Hybrid engines di-map manual:
  - Actor-Critic
  - Lateral Pivot
  - Temporal Horizon
  - Multi-Agent Fusion
- Semua strategy lain diproses oleh `DynamicPrimitiveEngine`.

### `src/modes/primitives/orchestrator.py` — `DynamicPrimitiveEngine`

Satu engine untuk semua primitive strategy:

- Validasi payload (`CCTThinkStepInput`).
- Tracking urutan (`SequentialEngine`).
- Persist `EnhancedThought` ke DB.
- Scoring & summarization via `ScoringEngine`.
- Auto-archiving “Thinking Pattern” via `PatternArchiver`.

### `src/modes/hybrids/*`

Hybrid engines membangun step otomatis (membuat prompt internal) dan menyimpannya sebagai `EnhancedThought`:

- `actor_critic`: create critic thought + synthesis thought.
- `lateral`: create provocation thought.
- `temporal`: create NOW/NEXT/LATER evaluation thought.
- `multi_agent`: create persona insights + fusion synthesis thought.

### `src/modes/fusion/orchestrator.py` (Catatan)

File ini terlihat sebagai prototype/stub, dan import path-nya tidak konsisten dengan struktur saat ini. Tidak direferensikan oleh registry.

## `src/tools/` (Public API Layer)

- `session_tools.py`: start/list/get history session.
- `cognitive_tools.py`: primitive step + hybrid triggers.
- `export_tools.py`: export/analyze metrics.

Semua tool didaftarkan ke MCP via `@mcp.tool()`.

## `src/analysis/` (Heuristics & Scoring)

- `quality.py`: heuristik clarity score berbasis panjang kalimat.
- `metrics.py`: cosine similarity sederhana berbasis token counter (tanpa embedding).
- `bias.py`: deteksi bias flags sederhana (absolutist, overconfidence, generalization).
- `scoring_engine.py`: multi-dimensional scoring untuk sebuah thought (clarity, coherence, novelty, evidence).

## `src/utils/` (Utilities)

- `economy.py`: `ContextPruner` untuk pruning history sebelum dikirim ke LLM.
- `harness.py`: `TokenHarness` untuk kalkulasi biaya dan metrik efisiensi.
- `pipelines.py`: `PipelineSelector` untuk rekomendasi urutan strategi berdasarkan keyword heuristics.

## Extension Guide (Add Strategy Baru)

1. Tambah value di `ThinkingStrategy` (`src/core/models/enums.py`).
2. Jika engine-nya hybrid khusus: buat folder di `src/modes/hybrids/<name>/` + implement `BaseCognitiveEngine`.
3. Register ke `CognitiveEngineRegistry._initialize_registry()` untuk hybrid mapping.
4. Jika cukup primitive: tidak perlu engine baru; `DynamicPrimitiveEngine` akan menangani otomatis.
5. Jika butuh tool API baru: tambahkan function `@mcp.tool()` di `src/tools/` dan delegasikan ke orchestrator.

