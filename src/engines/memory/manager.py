from __future__ import annotations

import json
import os
import secrets
import sqlite3
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from src.core.models.enums import CCTProfile
from src.core.models.domain import CCTSessionState, EnhancedThought, GoldenThinkingPattern, AntiPattern
from src.core.constants import DEFAULT_DB_PATH
from src.utils.economy import ContextPruner

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("cct.audit")  # [M2] Dedicated structured audit log channel


def _audit_log(operation: str, entity_id: str, detail: str = "") -> None:
    """
    [SECURITY M2] Emits a structured audit log entry for every write operation.
    Provides a forensic trail for security reviews and compliance.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "op": operation,
        "entity": entity_id,
        "detail": detail,
    }
    audit_logger.info(json.dumps(entry))

class MemoryManager:
    """
    SQLite-backed memory manager utilizing the Document Store Pattern.
    Persists all active sessions and thoughts as JSON blobs, surviving server restarts.

    Thread Safety:
    - WAL (Write-Ahead Logging) mode allows concurrent reads without blocking.
    - A threading.Lock serializes all write operations to prevent 'database is locked' errors
      under FastMCP's concurrent async tool handler execution.
    """
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        # [SECURITY C2] Harden db_path to prevent path traversal attacks.
        # Resolve the absolute path and ensure it stays within the project working directory.
        resolved = os.path.abspath(db_path)
        project_root = os.path.abspath(os.getcwd())
        if not resolved.startswith(project_root):
            raise ValueError(
                f"[SECURITY] db_path '{resolved}' is outside the project root '{project_root}'. "
                "Path traversal attack detected and blocked."
            )
        self.db_path = resolved
        # Serializes concurrent writes from async MCP tool handlers
        self._write_lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Creates a localized connection to ensure thread safety across async requests."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Enable WAL mode for concurrent reads without full table locking
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Bootstraps the database tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            # Create tables
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data JSON NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS thoughts (
                    thought_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    data JSON NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS thinking_patterns (
                    tp_id TEXT PRIMARY KEY,
                    thought_id TEXT,
                    usage_count INTEGER DEFAULT 1,
                    data JSON NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS anti_patterns (
                    failure_id TEXT PRIMARY KEY,
                    thought_id TEXT,
                    failed_strategy TEXT,
                    category TEXT,
                    data JSON NOT NULL
                )
            ''')

            # Create indexes for performance optimization
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_thoughts_session ON thoughts(session_id)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_thoughts_thought_id ON thoughts(thought_id)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_patterns_usage ON thinking_patterns(usage_count DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_anti_patterns_strategy ON anti_patterns(failed_strategy)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_anti_patterns_category ON anti_patterns(category)
            ''')

            conn.commit()
            logger.info(f"SQLite Memory mapped to: {self.db_path}")

    def create_session(
        self, 
        problem_statement: str, 
        profile: CCTProfile, 
        estimated_thoughts: int = 5,
        model_id: Optional[str] = None,
        suggested_pipeline: Optional[List[ThinkingStrategy]] = None,
        complexity: str = "unknown"
    ) -> CCTSessionState:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # [SECURITY H2] Generate a cryptographically random bearer token for this session.
        # The caller must store this token — it is required to access session history.
        session_token = secrets.token_urlsafe(32)
        
        session = CCTSessionState(
            session_id=session_id,
            problem_statement=problem_statement,
            profile=profile,
            current_thought_number=0,
            estimated_total_thoughts=estimated_thoughts,
            session_token=session_token,
            model_id=model_id if model_id else "claude-3-5-sonnet-20240620",
            suggested_pipeline=suggested_pipeline or [],
            complexity=complexity
        )
        
        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO sessions (session_id, data) VALUES (?, ?)",
                    (session_id, session.model_dump_json())
                )
        
        # [M2] Audit log: session creation
        _audit_log("SESSION_CREATE", session_id, f"profile={profile.value}")
        logger.info(f"Session {session_id} created for profile: {profile.value}")
        return session

    def get_session(self, session_id: str) -> Optional[CCTSessionState]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return CCTSessionState.model_validate_json(row[0])
        return None

    def update_session(self, session: CCTSessionState) -> None:
        """Explicitly saves mutated session state back to the database."""
        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE sessions SET data = ? WHERE session_id = ?",
                    (session.model_dump_json(), session.session_id)
                )
        # [M2] Audit log: session state update
        _audit_log("SESSION_UPDATE", session.session_id, f"status={session.status} thought_num={session.current_thought_number}")

    def validate_session_token(self, session_id: str, token: str) -> bool:
        """
        [SECURITY H2] Validates that the provided bearer token matches the session's stored token.
        Uses secrets.compare_digest to prevent timing-based side-channel attacks.
        Returns True only if the session exists AND the token matches.
        """
        session = self.get_session(session_id)
        if not session:
            return False
        # compare_digest prevents timing attacks on string comparison
        return secrets.compare_digest(session.session_token, token)

    def save_thought(self, session_id: str, thought: EnhancedThought) -> None:
        """
        Saves a new thought and updates session history atomically.
        Uses explicit transaction to ensure consistency.
        """
        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    # 1. Save the thought node
                    conn.execute(
                        "INSERT INTO thoughts (thought_id, session_id, data) VALUES (?, ?, ?)",
                        (thought.id, session_id, thought.model_dump_json())
                    )

                    # 2. Append thought ID to session history atomically within the same transaction
                    cursor = conn.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,))
                    row = cursor.fetchone()
                    if row:
                        session = CCTSessionState.model_validate_json(row[0])
                        session.history_ids.append(thought.id)
                        conn.execute(
                            "UPDATE sessions SET data = ? WHERE session_id = ?",
                            (session.model_dump_json(), session_id)
                        )
                    else:
                        logger.warning(f"Attempted to save thought to non-existent session: {session_id}")

                    conn.commit()
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.error(f"Failed to save thought {thought.id}: {e}")
                    raise

    def update_thought(self, session_id: str, thought: EnhancedThought) -> None:
        """
        Updates an existing thought node in the database.
        """
        with self._write_lock:
            with self._get_connection() as conn:
                try:
                    conn.execute(
                        "UPDATE thoughts SET data = ? WHERE thought_id = ? AND session_id = ?",
                        (thought.model_dump_json(), thought.id, session_id)
                    )
                    conn.commit()
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.error(f"Failed to update thought {thought.id}: {e}")
                    raise

        # [M2] Audit log: thought updated
        _audit_log("THOUGHT_UPDATE", thought.id, f"session={session_id} strategy={thought.strategy.value}")
        logger.debug(f"Updated thought {thought.id} in SQLite session {session_id}")

    def get_thought(self, thought_id: str) -> Optional[EnhancedThought]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM thoughts WHERE thought_id = ?", (thought_id,))
            row = cursor.fetchone()
            if row:
                return EnhancedThought.model_validate_json(row[0])
        return None
        
    def list_sessions(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT session_id FROM sessions")
            return [row[0] for row in cursor.fetchall()]

    def get_session_history(self, session_id: str) -> List[EnhancedThought]:
        session = self.get_session(session_id)
        if not session:
            return []
            
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM thoughts WHERE session_id = ?", (session_id,))
            thoughts_dict = {}
            for row in cursor.fetchall():
                thought = EnhancedThought.model_validate_json(row[0])
                thoughts_dict[thought.id] = thought
                
        history_set = set(session.history_ids)
        ordered: List[EnhancedThought] = []

        for tid in session.history_ids:
            thought = thoughts_dict.get(tid)
            if thought:
                ordered.append(thought)

        remaining = [t for tid, t in thoughts_dict.items() if tid not in history_set]
        remaining.sort(key=lambda t: (t.sequential_context.thought_number, t.timestamp))

        if ordered:
            return ordered + remaining
        return remaining


    def save_thinking_pattern(self, pattern: GoldenThinkingPattern):
        """Persists a high-quality cognitive pattern to the global thinking_patterns table."""
        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO thinking_patterns (tp_id, thought_id, usage_count, data) VALUES (?, ?, ?, ?)",
                    (pattern.id, pattern.thought_id, pattern.usage_count, pattern.model_dump_json())
                )
        # [M2] Audit log: thinking pattern archived
        _audit_log("PATTERN_ARCHIVE", pattern.id, f"thought={pattern.thought_id} session={pattern.session_id}")
        logger.info(f"Thinking Pattern Archived: {pattern.id} (Ref: {pattern.thought_id})")

    def record_pattern_usage(self, tp_id: str):
        """Increments the usage count for a given pattern to identify battle-tested strategies."""
        with self._write_lock:
            with self._get_connection() as conn:
                # 1. Update count in the indexed column
                conn.execute("UPDATE thinking_patterns SET usage_count = usage_count + 1 WHERE tp_id = ?", (tp_id,))
                # 2. Sync with JSON blob to keep data consistent
                cursor = conn.execute("SELECT data FROM thinking_patterns WHERE tp_id = ?", (tp_id,))
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    data["usage_count"] = data.get("usage_count", 1) + 1
                    conn.execute("UPDATE thinking_patterns SET data = ? WHERE tp_id = ?", (json.dumps(data), tp_id))
        # [M2] Audit log: pattern usage increment
        _audit_log("PATTERN_USAGE", tp_id)
        logger.info(f"Pattern Usage Recorded: {tp_id}")

    def get_global_patterns(self) -> List[GoldenThinkingPattern]:
        """Retrieves all archived thinking patterns across all past sessions."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM thinking_patterns ORDER BY rowid DESC")
            return [GoldenThinkingPattern.model_validate_json(row[0]) for row in cursor.fetchall()]

    def get_optimized_history(
        self, 
        session_id: str, 
        current_thought_id: Optional[str] = None
    ) -> List[EnhancedThought]:
        """
        Retrieves a token-optimized history that follows pruning and summarization rules.
        """
        session = self.get_session(session_id)
        if not session:
            return []
            
        full_history = self.get_session_history(session_id)
        return ContextPruner.prune_history(session, full_history, current_thought_id)

    def save_anti_pattern(self, failure: AntiPattern):
        """Persists a cognitive failure to the global anti-patterns table."""
        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO anti_patterns (failure_id, thought_id, failed_strategy, category, data) VALUES (?, ?, ?, ?, ?)",
                    (failure.id, failure.thought_id, failure.failed_strategy.value, failure.category, failure.model_dump_json())
                )
        # [M2] Audit log: anti-pattern committed to immune wall
        _audit_log("ANTIPATTERN_LOG", failure.id, f"category={failure.category} session={failure.session_id}")
        logger.warning(f"Anti-Pattern Logged: {failure.id} (Category: {failure.category})")

    def get_global_anti_patterns(self) -> List[AntiPattern]:
        """Retrieves all logged cognitive failures."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM anti_patterns ORDER BY rowid DESC")
            return [AntiPattern.model_validate_json(row[0]) for row in cursor.fetchall()]

    def get_relevant_knowledge(self, problem_statement: str) -> Dict[str, List[Any]]:
        """
        Retrieves patterns and anti-patterns relevant to the current problem.
        """
        all_patterns = self.get_global_patterns()
        all_failures = self.get_global_anti_patterns()
        
        # Simple heuristic mapping
        problem_keywords = problem_statement.lower().split()
        
        relevant_patterns = [
            p for p in all_patterns 
            if any(kw in p.original_problem.lower() or kw in p.summary.lower() for kw in problem_keywords)
        ]
        
        relevant_failures = [
            f for f in all_failures
            if any(kw in f.problem_context.lower() or kw in f.failure_reason.lower() for kw in problem_keywords)
        ]
        
        return {
            "thinking_patterns": relevant_patterns,
            "anti_patterns": relevant_failures
        }

    def get_all_thinking_patterns(self) -> List[Dict[str, Any]]:
        """
        Retrieve all thinking patterns as raw dictionaries.
        Used by PatternInjector for automatic Phase 0 injection.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM thinking_patterns ORDER BY rowid DESC")
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def get_all_anti_patterns(self) -> List[Dict[str, Any]]:
        """
        Retrieve all anti-patterns as raw dictionaries.
        Used by PatternInjector for automatic Phase 0 injection.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM anti_patterns ORDER BY rowid DESC")
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def delete_session(self, session_id: str) -> bool:
        """
        Purges a session and all its associated thoughts from the database.
        [SECURITY M2] Logged in the forensic audit trail.
        """
        with self._write_lock:
            with self._get_connection() as conn:
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    # 1. Delete associated thoughts first (manual cascade)
                    conn.execute("DELETE FROM thoughts WHERE session_id = ?", (session_id,))
                    # 2. Delete the session itself
                    cursor = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                    success = cursor.rowcount > 0
                    conn.commit()
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.error(f"Failed to delete session {session_id}: {e}")
                    return False
        
        if success:
            _audit_log("SESSION_DELETE", session_id)
            logger.info(f"Session {session_id} and its history purged.")
        return success

    def get_aggregate_usage(self) -> Dict[str, Any]:
        """
        Calculates global token and cost usage across all sessions in the database.
        Returns a dictionary with sum of prompt_tokens, completion_tokens, and costs.
        """
        totals = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "cost_idr": 0.0,
            "session_count": 0
        }
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM sessions")
            rows = cursor.fetchall()
            
            totals["session_count"] = len(rows)
            for row in rows:
                try:
                    data = json.loads(row[0])
                    totals["prompt_tokens"] += data.get("total_prompt_tokens", 0)
                    totals["completion_tokens"] += data.get("total_completion_tokens", 0)
                    totals["cost_usd"] += data.get("total_cost_usd", 0.0)
                    totals["cost_idr"] += data.get("total_cost_idr", 0.0)
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
            
            totals["total_tokens"] = totals["prompt_tokens"] + totals["completion_tokens"]
            # Round financial totals
            totals["cost_usd"] = round(totals["cost_usd"], 8)
            totals["cost_idr"] = round(totals["cost_idr"], 2)
            
        return totals
