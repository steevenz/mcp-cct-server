---
title: "Memory Persistence: SQLite Schema & Hardening"
tags: ["memory", "sqlite", "persistence", "db", "security"]
keywords: ["schema", "wal", "locking", "documentstore", "sessions"]
related: ["context.md"]
importance: 90
recency: 1.0
maturity: validated
accessCount: 0
updateCount: 1
createdAt: "2026-04-12T00:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

## Raw Concept

**Task:**
Implement a high-performance, concurrent, and secure persistence layer for cognitive graph data using a Document Store pattern on top of SQLite.

**Files:**
- `src/engines/memory/manager.py`

**Flow:**
1. `MemoryManager` verifies `db_path` safety [C2].
2. `_init_db()` bootstraps 4 tables and performance indexes.
3. Thread-safe transactions handle concurrent async updates from tool handlers.

## Narrative

### Structure: The Document Store Pattern
The system uses SQLite not as a relational database, but as an optimized **Document Store**. Complex Python objects (EnhancedThoughts, Sessions) are serialized to JSON and stored in `JSON NOT NULL` columns. This allows for schema flexibility without frequent migrations.

**Core Tables:**
- `sessions`: Stores the session state, problem statement, and tokens.
- `thoughts`: Stores the individual reasoning nodes, linked by `session_id`.
- `thinking_patterns`: Global archive for high-quality "Golden" reasoning styles.
- `anti_patterns`: Defensive archive for documented reasoning failures.

### Rules & Hardening
- **WAL Mode**: Enabled via `PRAGMA journal_mode=WAL` to allow multiple concurrent readers without blocking writes.
- **Write Serialization**: A `threading.Lock` serializes all write operations (INSERT/UPDATE) to prevent "database is locked" errors in highly concurrent async tool executions.
- **Forensic Audit Logs**: Every write operation emits a structured JSON log entry to the `cct.audit` channel.
- **Path Traversal Protection [C2]**: The `db_path` is strictly resolved and verified to reside within the project root.

### Performance Indexing
Speed is critical for real-time thinking. Secondary indexes are provided for:
- `session_id` in the `thoughts` table (fast history retrieval).
- `usage_count` in `thinking_patterns` (retrieving battle-tested strategies).
- `failed_strategy` in `anti_patterns` (fast avoidance checks).

## Facts
- **atomic_history_append**: Saving a thought and updating the session's history sequence are performed within a single `IMMEDIATE` transaction. [convention]
- **bearer_session_tokens [H2]**: Cryptographically random 32-byte tokens are issued per session to prevent horizontal privilege escalation. [security]
- **timing_attack_protection**: Session token validation uses `secrets.compare_digest` to prevent side-channel timing attacks. [security]
