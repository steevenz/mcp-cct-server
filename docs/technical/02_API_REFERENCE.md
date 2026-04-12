# API Reference (MCP Tools)

Semua API publik diekspos sebagai MCP tools via `FastMCP` dan decorator `@mcp.tool()` pada modul `src/tools/`.

## Conventions

- Semua response berbentuk JSON (Python `dict`).
- Error format tidak sepenuhnya uniform; beberapa tools return `{ "error": "..." }`, yang lain `{ "status": "error", "message": "..." }`.
- `session_id` adalah key utama untuk mengakses state persisten di SQLite.

## Session Tools (`src/tools/session_tools.py`)

### start_cct_session

**Tujuan:** Inisialisasi session baru dan menyimpan state awal ke SQLite.

**Parameters**

- `problem_statement: str`
- `profile: str = "general"` (jika tidak valid, server fallback ke `balanced`)

**Returns**

- `{ status: "success", session_id: "...", problem_statement: "...", profile: "...", dynamic_pipeline: [...], injected_skills_count: int, injected_failures_count: int, timestamp: "..." }`
- atau `{ status: "error", message: "..." }`

**Example**

```json
{
  "problem_statement": "Refactor orchestrator to be testable and secure",
  "profile": "balanced"
}
```

### list_cct_sessions

**Tujuan:** List semua session yang ada di DB.

**Returns**

- `{ "sessions": ["session_..."] }`

### get_thinking_path

**Tujuan:** Ambil full history thoughts untuk sebuah session dalam urutan kronologis.

**Parameters**

- `session_id: str`

**Returns**

- `{ session_id, problem_statement, profile, steps_count, steps: EnhancedThought[] }`
- atau `{ "error": "session_not_found" }`

### suggest_cognitive_pipeline

**Tujuan:** Preview rekomendasi pipeline strategi berbasis heuristik tanpa membuat session.

**Parameters**

- `problem_statement: str`

**Returns**

- `{ category: "DEBUG|ARCH|FEAT|SEC|BIZ|GENERIC", pipeline: string[], estimated_total_thoughts: int }`

**Example**

```json
{
  "problem_statement": "Implement new feature for export tool"
}
```

## Cognitive Tools (`src/tools/cognitive_tools.py`)

### cct_think_step

**Tujuan:** Menjalankan satu step primitive untuk strategi tertentu (mis. `systematic`, `first_principles`).

**Parameters**

- `session_id: str`
- `thought_content: str`
- `strategy: str` (harus cocok dengan `ThinkingStrategy` enum value)
- `thought_type: str = "analysis"` (harus cocok dengan `ThoughtType` enum value)
- `thought_number: int = 1`
- `estimated_total_thoughts: int = 5`
- `next_thought_needed: bool = True`
- `is_revision: bool = False`
- `revises_thought_id: str | null`
- `branch_from_id: str | null`
- `branch_id: str | null`

**Returns**

- `{ status: "success", orchestration_mode: "<strategy>", generated_thought_id: "...", is_golden_skill: bool, early_convergence_suggested: bool, current_step: int, estimated_total: int }`
- atau `{ "error": "..." }` jika `strategy` tidak dikenali.

**Notes**

- Validasi payload dilakukan oleh `CCTThinkStepInput` di `src/core/models/schemas.py`.
- Integrity urutan step dijaga oleh `SequentialEngine.process_sequence_step()`.

### actor_critic_dialog

**Tujuan:** Memicu loop Actor-Critic otomatis terhadap thought tertentu.

**Parameters**

- `session_id: str`
- `target_thought_id: str`
- `critic_persona: str = "Security Expert"`

**Returns**

- `{ status: "success", orchestration_mode: "actor_critic_loop", target_thought_id, critic_phase: {...}, synthesis_phase: {...}, current_step }`

### lateral_pivot_brainstorm

**Tujuan:** Memicu lateral pivot untuk memaksa perubahan paradigma.

**Parameters**

- `session_id: str`
- `current_paradigm: str`
- `provocation_method: str = "REVERSE_ASSUMPTION"`

**Returns**

- `{ status: "success", orchestration_mode: "unconventional_pivot", provocation_applied, generated_thought_id, current_step, instruction }`

### temporal_horizon_projection

**Tujuan:** Memicu evaluasi temporal (NOW/NEXT/LATER) untuk thought tertentu.

**Parameters**

- `session_id: str`
- `target_thought_id: str`
- `projection_scale: str = "LONG_TERM"`

**Returns**

- `{ status: "success", orchestration_mode: "long_term_horizon", projection_scale, generated_thought_id, current_step, instruction }`

## Export & Analysis Tools (`src/tools/export_tools.py`)

### export_thinking_session

**Tujuan:** Export semua steps dari session untuk konsumsi eksternal.

**Parameters**

- `session_id: str`

**Returns**

- `{ "steps": EnhancedThought[] }`
- atau `{ "error": "session_not_found_or_empty" }`

### analyze_session

**Tujuan:** Hitung metrik global session (clarity, bias flags, semantic consistency).

**Parameters**

- `session_id: str`

**Returns**

- `{ session_id, problem_statement, metrics: { clarity_score: float, bias_flags: string[], consistency_score: float } }`
- atau `{ "error": "session_not_found" }`
