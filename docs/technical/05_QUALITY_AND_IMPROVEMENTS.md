# Code Quality Review & Improvement Backlog

Dokumen ini mencatat temuan kualitas kode, risiko runtime, dan rekomendasi perbaikan agar codebase lebih stabil, aman, dan mudah dikembangkan.

## Strengths

- Struktur lapisan cukup jelas: API layer (`tools/`) → orchestrator → registry → engines/modes → persistence.
- Domain model berbasis Pydantic v2 memudahkan validasi payload dan serialisasi JSON.
- `DynamicPrimitiveEngine` mengurangi duplikasi untuk strategi primitive.
- `SequentialEngine` memberi guardrail terhadap “sequence hallucination” dan memastikan state session persisted.

## Key Risks / Issues (Priority)

### P0 — Konsistensi kontrak API & error format

Saat ini ada variasi bentuk error response (mis. `{ "error": ... }` vs `{ "status": "error", "message": ... }`).

Rekomendasi:

- Definisikan satu schema error response lintas semua tools.
- Pastikan semua exceptions di engine layer ter-wrap ke format yang konsisten di API boundary.

### P0 — Configuration Divergence

Ada dua surface konfigurasi:

- `src/main.py` memakai `MCP_SERVER_HOST`/`MCP_SERVER_PORT`.
- `src/core/config.py` memakai `CCT_*` env vars.

Rekomendasi:

- Jadikan `src/core/config.py` sebagai single source of truth dan dipakai oleh `src/main.py`.
- Dokumentasikan defaults dan mode transport (SSE/stdio/http) dengan jelas.

### P1 — Dead/Prototype Code

`src/modes/fusion/orchestrator.py` terlihat sebagai prototype/stub (import path tidak konsisten, ada TODO, dan `sequential_context=None`).

Rekomendasi:

- Jika tidak dipakai: hapus atau pindahkan ke `scratch/` agar tidak membingungkan.
- Jika dipakai: refactor supaya mengikuti kontrak `BaseCognitiveEngine` yang berlaku dan integrasikan ke registry dengan test coverage.

### P1 — Data Integrity: Tree linking incomplete

Di beberapa hybrid engines, parent/children linking dilakukan parsial (mis. append `children_ids` ke object parent tanpa persist kembali).

Rekomendasi:

- Putuskan apakah tree integrity akan dijaga secara strict:
  - Opsi A: simpan relasi hanya lewat `parent_id` dan derive `children_ids` saat query.
  - Opsi B: jika `children_ids` wajib, update parent di DB setiap kali child dibuat.

### P1 — SQLite concurrency & durability

`MemoryManager` membuat koneksi baru per call dengan `check_same_thread=False`. Ini workable untuk beban ringan, tapi ada risiko lock contention.

Rekomendasi:

- Aktifkan WAL mode (PRAGMA `journal_mode=WAL`) dan `busy_timeout`.
- Pertimbangkan satu connection per thread atau pool sederhana jika load meningkat.

### P2 — Security posture untuk input arbitrary

`thought_content` dan `problem_statement` adalah input arbitrary dan bisa sangat panjang.

Rekomendasi:

- Tambahkan guardrails: max length, sanitization untuk output logging, dan rate limiting di layer transport jika digunakan lewat network.
- Jangan log full content di level INFO untuk menghindari kebocoran data sensitif.

### P2 — Dependencies bloat / unused deps

`requirements.txt` mencantumkan `fastapi` dan `uvicorn` walaupun code `src/` tidak menggunakannya saat ini.

Rekomendasi:

- Audit dependency dan pisahkan optional deps (mis. `requirements-dashboard.txt`, `requirements-analysis.txt`).
- Pastikan pinned range compatible untuk reproducibility.

## Suggested Engineering Standards

- Tambahkan type-checking pipeline (mypy/pyright) dan formatter (ruff/black) jika repo ingin lebih ketat.
- Wajibkan unit test untuk:
  - Registry mapping correctness
  - SequentialEngine boundary cases (revision + branching)
  - Memory persistence (session + thought ordering)
- Tambahkan integration tests untuk MCP tool contracts (schema & error formats).

## Observability & Debuggability

- Gunakan structured logging (fields: `session_id`, `strategy`, `thought_id`) untuk traceability.
- Pertimbangkan correlation ID per request untuk multi-step flows.

## Roadmap Improvements (Concrete)

1. Standardize API schemas: `SuccessResponse`, `ErrorResponse`, `ToolResult`.
2. Consolidate config: gunakan `load_settings()` sebagai source of truth.
3. Decide tree integrity model (derive children vs persisted children_ids).
4. Hardening SQLite: WAL mode + timeouts + integration load tests.
5. Optional: tambah semantic similarity berbasis embeddings jika `sentence-transformers` memang dibutuhkan.

