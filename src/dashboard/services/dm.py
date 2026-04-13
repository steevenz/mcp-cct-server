import sqlite3
import json
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class DataManager:
    """
    Sovereign Data Bridge for the CCT Command Center.
    Handles SQLite persistence, pricing logic, and telemetry caches.
    """
    
    def __init__(self, db_path: str = "database/cct_memory.db"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            self.db_path = "cct_memory.db"
            
        self._last_fingerprint = ""
        self.forex_rate = 16000.0  # Default fallback
        self.rate_source = "default"
        
    def get_fingerprint(self) -> str:
        """Generates a stable fingerprint of the database state."""
        try:
            mtime = os.path.getmtime(self.db_path)
            conn = sqlite3.connect(self.db_path)
            counts = conn.execute(
                "SELECT (SELECT COUNT(*) FROM thoughts), "
                "(SELECT COUNT(*) FROM sessions), "
                "(SELECT COUNT(*) FROM thinking_patterns), "
                "(SELECT COUNT(*) FROM anti_patterns)"
            ).fetchone()
            conn.close()
            raw = f"{mtime}:{counts}"
            return hashlib.md5(raw.encode()).hexdigest()[:12]
        except Exception:
            return str(time.time())

    def has_changed(self) -> bool:
        """Checks if the database has changed since the last check."""
        new_fp = self.get_fingerprint()
        if new_fp != self._last_fingerprint:
            self._last_fingerprint = new_fp
            return True
        return False

    def fetch_sessions(self) -> List[Dict[str, Any]]:
        """Fetch all sessions ordered by recency."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, data FROM sessions ORDER BY rowid DESC")
            rows = cursor.fetchall()
            conn.close()
            return [{"session_id": r[0], "data": json.loads(r[1])} for r in rows]
        except Exception:
            return []

    def fetch_db_stats(self) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            thoughts_total = conn.execute("SELECT COUNT(*) FROM thoughts").fetchone()[0]
            sessions_total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            patterns_total = conn.execute("SELECT COUNT(*) FROM thinking_patterns").fetchone()[0]
            anti_total = conn.execute("SELECT COUNT(*) FROM anti_patterns").fetchone()[0]
            conn.close()
            db_size_kb = os.path.getsize(self.db_path) / 1024 if os.path.exists(self.db_path) else 0
            return {
                "thoughts": thoughts_total,
                "sessions": sessions_total,
                "patterns": patterns_total,
                "anti_patterns": anti_total,
                "db_size_kb": round(db_size_kb, 1),
            }
        except Exception:
            return {}

    def fetch_thoughts(self, session_id: str) -> Dict[str, Any]:
        """Fetch all thoughts for a specific session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM thoughts WHERE session_id = ?", (session_id,))
            rows = cursor.fetchall()
            conn.close()
            # Return as dict keyed by thought_id for easy lookup
            return {json.loads(r[0])["id"]: json.loads(r[0]) for r in rows}
        except Exception:
            return {}

    def fetch_session_rollups(self) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            sessions_rows = conn.execute("SELECT session_id, data FROM sessions ORDER BY rowid DESC").fetchall()
            thoughts_rows = conn.execute("SELECT session_id, data FROM thoughts").fetchall()
            conn.close()

            thoughts_by_session: Dict[str, Dict[str, Any]] = {}
            for session_id, data in thoughts_rows:
                try:
                    thought = json.loads(data)
                except Exception:
                    continue
                sid = session_id or thought.get("session_id")
                if not sid:
                    continue
                bucket = thoughts_by_session.setdefault(sid, {})
                tid = thought.get("id")
                if tid:
                    bucket[tid] = thought

            out: List[Dict[str, Any]] = []
            for session_id, sdata in sessions_rows:
                try:
                    s = json.loads(sdata)
                except Exception:
                    s = {}

                history_ids = s.get("history_ids") or []
                thoughts = thoughts_by_session.get(session_id, {})
                selected = [thoughts.get(tid) for tid in history_ids if tid in thoughts]
                if not selected and thoughts:
                    selected = list(thoughts.values())

                in_tokens = 0
                out_tokens = 0
                cost_usd = 0.0
                cost_idr = 0.0

                for t in selected:
                    m = (t or {}).get("metrics", {})
                    in_tokens += int(m.get("input_tokens", 0) or 0)
                    out_tokens += int(m.get("output_tokens", 0) or 0)
                    cost_usd += float(m.get("input_cost_usd", 0) or 0) + float(m.get("output_cost_usd", 0) or 0)
                    cost_idr += float(m.get("input_cost_idr", 0) or 0) + float(m.get("output_cost_idr", 0) or 0)

                out.append(
                    {
                        "session_id": session_id,
                        "data": s,
                        "steps": len(history_ids) if history_ids else len(thoughts),
                        "input_tokens": in_tokens,
                        "output_tokens": out_tokens,
                        "total_tokens": in_tokens + out_tokens,
                        "cost_usd": cost_usd,
                        "cost_idr": cost_idr,
                    }
                )
            return out
        except Exception:
            return []

    def fetch_global_economy(self) -> Dict[str, Any]:
        """Calculate aggregate financial and token metrics across all cognitive sessions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM thoughts")
            rows = cursor.fetchall()
            conn.close()
            
            stats = {
                "input_tokens": 0, "output_tokens": 0,
                "cost_usd": 0.0, "cost_idr": 0.0,
                "thought_count": len(rows)
            }
            
            for row in rows:
                t = json.loads(row[0])
                m = t.get("metrics", {})
                stats["input_tokens"] += m.get("input_tokens", 0)
                stats["output_tokens"] += m.get("output_tokens", 0)
                stats["cost_usd"] += m.get("input_cost_usd", 0) + m.get("output_cost_usd", 0)
                stats["cost_idr"] += m.get("input_cost_idr", 0) + m.get("output_cost_idr", 0)
                
            stats["total_tokens"] = stats["input_tokens"] + stats["output_tokens"]
            return stats
        except Exception:
            return {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_idr": 0.0, "total_tokens": 0, "thought_count": 0}

    def fetch_patterns(self) -> List[Dict[str, Any]]:
        """Fetch both thinking patterns and anti-patterns for the immunity wall."""
        try:
            conn = sqlite3.connect(self.db_path)
            patterns = [json.loads(r[0]) for r in conn.execute("SELECT data FROM thinking_patterns").fetchall()]
            antis = [json.loads(r[0]) for r in conn.execute("SELECT data FROM anti_patterns").fetchall()]
            conn.close()
            return patterns, antis
        except Exception:
            return [], []

    def delete_session(self, session_id: str) -> bool:
        """Atomic purge of a session and its associated cognitive history."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            with conn:
                conn.execute("DELETE FROM thoughts WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.close()
            return True
        except Exception:
            return False

    def get_health(self) -> Dict[str, Any]:
        """Comprehensive system diagnostics."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "db_size_kb": round(os.path.getsize(self.db_path) / 1024, 1) if os.path.exists(self.db_path) else 0,
            "services": {"database": "healthy"}
        }
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
        except Exception as e:
            health["status"] = "degraded"
            health["services"]["database"] = str(e)
        return health
