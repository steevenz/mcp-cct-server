from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("cct-auth")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class AuthResult:
    ok: bool
    code: int
    message: str
    principal: Optional[Dict[str, Any]] = None


class AuthService:
    """Dual-mode authentication service for MCP clients.

    - Supports legacy shared dashboard key validation.
    - Supports per-instance API key issuance via handshake.
    - Persists keys and handshake sessions in SQLite.
    """

    def __init__(
        self,
        db_path: str,
        bootstrap_api_key: str,
        *,
        auth_mode: str = "dual",
        default_ttl_days: int = 30,
        legacy_enabled: bool = True,
    ) -> None:
        self.db_path = db_path
        self.bootstrap_api_key = bootstrap_api_key
        self.auth_mode = auth_mode
        self.default_ttl_days = max(1, default_ttl_days)
        self.legacy_enabled = legacy_enabled
        self._write_lock = threading.Lock()
        self._rate_lock = threading.Lock()
        self._rate_windows: Dict[str, list[float]] = {}
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_api_keys (
                        key_id TEXT PRIMARY KEY,
                        key_hash TEXT NOT NULL,
                        llm_instance_id TEXT NOT NULL,
                        scopes_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        legacy INTEGER NOT NULL DEFAULT 0,
                        rotation_counter INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        last_used_at TEXT,
                        rate_limit_per_minute INTEGER NOT NULL DEFAULT 120
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_handshakes (
                        handshake_id TEXT PRIMARY KEY,
                        llm_instance_id TEXT NOT NULL,
                        client_nonce TEXT NOT NULL,
                        server_nonce TEXT NOT NULL,
                        challenge TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        used INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_audit_logs (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        request_id TEXT,
                        llm_instance_id TEXT,
                        key_id TEXT,
                        ip TEXT,
                        result TEXT NOT NULL,
                        reason_code TEXT,
                        created_at TEXT NOT NULL,
                        data_json TEXT
                    )
                    """
                )

    def _audit(
        self,
        event_type: str,
        *,
        result: str,
        request_id: str = "",
        llm_instance_id: str = "",
        key_id: str = "",
        ip: str = "",
        reason_code: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload = {
            "event": event_type,
            "result": result,
            "request_id": request_id,
            "llm_instance_id": llm_instance_id,
            "key_id": key_id,
            "ip": ip,
            "reason_code": reason_code,
            "ts": _iso(_utc_now()),
        }
        logger.info(json.dumps(payload, ensure_ascii=True))

        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO auth_audit_logs (
                        event_id, event_type, request_id, llm_instance_id, key_id,
                        ip, result, reason_code, created_at, data_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"evt_{secrets.token_hex(8)}",
                        event_type,
                        request_id or None,
                        llm_instance_id or None,
                        key_id or None,
                        ip or None,
                        result,
                        reason_code or None,
                        _iso(_utc_now()),
                        json.dumps(data or {}, ensure_ascii=True),
                    ),
                )

    def _hash_secret(self, secret: str) -> str:
        return hmac.new(
            self.bootstrap_api_key.encode("utf-8"),
            secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _mint_key(self, llm_instance_id: str, scopes: list[str], ttl_days: int, *, legacy: bool = False) -> Dict[str, Any]:
        key_id = secrets.token_hex(8)
        secret = secrets.token_urlsafe(32)
        token = f"cct_live_{key_id}.{secret}"
        key_hash = self._hash_secret(secret)
        now = _utc_now()
        expires = now + timedelta(days=max(1, ttl_days))
        rate_limit = 120 if not legacy else 90

        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO llm_api_keys (
                        key_id, key_hash, llm_instance_id, scopes_json, status, legacy,
                        rotation_counter, created_at, expires_at, last_used_at, rate_limit_per_minute
                    ) VALUES (?, ?, ?, ?, 'active', ?, 0, ?, ?, NULL, ?)
                    """,
                    (
                        key_id,
                        key_hash,
                        llm_instance_id,
                        json.dumps(sorted(set(scopes))),
                        1 if legacy else 0,
                        _iso(now),
                        _iso(expires),
                        rate_limit,
                    ),
                )

        return {
            "api_key": token,
            "key_id": key_id,
            "llm_instance_id": llm_instance_id,
            "scopes": sorted(set(scopes)),
            "expires_at": _iso(expires),
            "rate_limit_per_minute": rate_limit,
        }

    def issue_legacy_key(self, llm_instance_id: str = "legacy-client") -> Dict[str, Any]:
        key = self._mint_key(
            llm_instance_id=llm_instance_id,
            scopes=["mcp:sync", "mcp:sse", "auth:rotate"],
            ttl_days=self.default_ttl_days,
            legacy=True,
        )
        self._audit("KEY_ISSUED", result="success", llm_instance_id=llm_instance_id, key_id=key["key_id"], reason_code="legacy")
        return key

    def handshake_init(self, llm_instance_id: str, client_nonce: str, request_id: str = "", ip: str = "") -> Dict[str, Any]:
        handshake_id = f"hs_{secrets.token_hex(8)}"
        server_nonce = secrets.token_urlsafe(16)
        challenge = secrets.token_urlsafe(24)
        now = _utc_now()
        expires = now + timedelta(minutes=5)

        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO auth_handshakes (
                        handshake_id, llm_instance_id, client_nonce, server_nonce,
                        challenge, created_at, expires_at, used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        handshake_id,
                        llm_instance_id,
                        client_nonce,
                        server_nonce,
                        challenge,
                        _iso(now),
                        _iso(expires),
                    ),
                )

        self._audit(
            "HANDSHAKE_INIT",
            result="success",
            request_id=request_id,
            llm_instance_id=llm_instance_id,
            ip=ip,
            data={"handshake_id": handshake_id},
        )

        return {
            "handshake_id": handshake_id,
            "server_nonce": server_nonce,
            "challenge": challenge,
            "expires_at": _iso(expires),
            "signature_algorithm": "HMAC-SHA256",
            "certificate_mode": "pinning-required-in-production",
        }

    def handshake_complete(
        self,
        handshake_id: str,
        client_proof: str,
        bootstrap_key: str,
        *,
        request_id: str = "",
        ip: str = "",
        ttl_days: Optional[int] = None,
    ) -> AuthResult:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM auth_handshakes WHERE handshake_id = ?",
                (handshake_id,),
            ).fetchone()

        if not row:
            self._audit("HANDSHAKE_COMPLETE", result="denied", request_id=request_id, ip=ip, reason_code="missing_handshake")
            return AuthResult(False, 404, "handshake_not_found")

        if row["used"]:
            self._audit("HANDSHAKE_COMPLETE", result="denied", request_id=request_id, ip=ip, reason_code="already_used")
            return AuthResult(False, 409, "handshake_already_used")

        exp = datetime.fromisoformat(row["expires_at"])
        if _utc_now() > exp:
            self._audit("HANDSHAKE_COMPLETE", result="denied", request_id=request_id, ip=ip, reason_code="expired")
            return AuthResult(False, 410, "handshake_expired")

        if not secrets.compare_digest(bootstrap_key, self.bootstrap_api_key):
            self._audit("HANDSHAKE_COMPLETE", result="denied", request_id=request_id, ip=ip, reason_code="invalid_bootstrap")
            return AuthResult(False, 403, "invalid_bootstrap_key")

        expected = hmac.new(
            bootstrap_key.encode("utf-8"),
            f"{row['handshake_id']}:{row['llm_instance_id']}:{row['challenge']}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not secrets.compare_digest(client_proof, expected):
            self._audit("HANDSHAKE_COMPLETE", result="denied", request_id=request_id, ip=ip, reason_code="bad_proof")
            return AuthResult(False, 403, "invalid_handshake_proof")

        with self._write_lock:
            with self._get_connection() as conn:
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Try to mark handshake as used while checking it's unused
                    cur = conn.execute(
                        "UPDATE auth_handshakes SET used = 1 WHERE handshake_id = ? AND used = 0 RETURNING *",
                        (handshake_id,)
                    )
                    updated_row = cur.fetchone()
                    if not updated_row:
                        conn.rollback()
                        self._audit("HANDSHAKE_COMPLETE", result="denied", request_id=request_id, ip=ip, reason_code="concurrent_use")
                        return AuthResult(False, 409, "handshake_already_used")
                    
                    issued = self._mint_key(
                        llm_instance_id=row["llm_instance_id"],
                        scopes=["mcp:sync", "mcp:sse", "auth:rotate"],
                        ttl_days=ttl_days or self.default_ttl_days,
                        legacy=False,
                    )
                    
                    self._audit(
                        "KEY_ISSUED",
                        result="success",
                        request_id=request_id,
                        llm_instance_id=row["llm_instance_id"],
                        key_id=issued["key_id"],
                        ip=ip,
                        reason_code="handshake",
                    )
                    
                    conn.commit()
                    return AuthResult(True, 200, "ok", issued)
                except Exception as e:
                    conn.rollback()
                    logger.exception("Failed to complete handshake")
                    self._audit("HANDSHAKE_COMPLETE", result="error", request_id=request_id, ip=ip, reason_code="system_error")
                    return AuthResult(False, 500, "internal_server_error")

    def _check_rate_limit(self, key_id: str, per_minute: int) -> tuple[bool, int]:
        now = time.time()
        with self._rate_lock:
            bucket = self._rate_windows.setdefault(key_id, [])
            cutoff = now - 60
            while bucket and bucket[0] < cutoff:
                bucket.pop(0)
            if len(bucket) >= per_minute:
                retry_after = max(1, int(bucket[0] + 60 - now))
                return False, retry_after
            bucket.append(now)
            return True, 0

    def validate_api_key(self, presented_key: str, required_scope: Optional[str] = None, *, request_id: str = "", ip: str = "") -> AuthResult:
        if not presented_key:
            return AuthResult(False, 403, "missing_api_key")

        legacy_allowed = self.auth_mode in {"dual", "legacy_only"} and self.legacy_enabled
        issued_allowed = self.auth_mode in {"dual", "handshake_only"}

        if legacy_allowed and secrets.compare_digest(presented_key, self.bootstrap_api_key):
            principal = {
                "auth_type": "legacy_shared_key",
                "llm_instance_id": "legacy-shared",
                "scopes": ["mcp:sync", "mcp:sse", "auth:rotate", "admin:revoke"],
            }
            if required_scope and required_scope not in principal["scopes"]:
                return AuthResult(False, 403, "insufficient_scope")
            return AuthResult(True, 200, "ok", principal)

        if not issued_allowed:
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="issued_keys_disabled")
            return AuthResult(False, 403, "issued_keys_disabled")

        if not presented_key.startswith("cct_live_") or "." not in presented_key:
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="bad_format")
            return AuthResult(False, 403, "invalid_api_key_format")

        token_body = presented_key[len("cct_live_"):]
        key_id, secret = token_body.split(".", 1)

        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM llm_api_keys WHERE key_id = ?",
                (key_id,),
            ).fetchone()

        if not row:
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="missing_key", key_id=key_id)
            return AuthResult(False, 403, "invalid_api_key")

        if row["status"] != "active":
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="inactive_key", key_id=key_id)
            return AuthResult(False, 403, "revoked_or_inactive_key")

        if _utc_now() > datetime.fromisoformat(row["expires_at"]):
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="expired_key", key_id=key_id)
            return AuthResult(False, 403, "expired_api_key")

        expected_hash = row["key_hash"]
        if not secrets.compare_digest(self._hash_secret(secret), expected_hash):
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="hash_mismatch", key_id=key_id)
            return AuthResult(False, 403, "invalid_api_key")

        per_minute = int(row["rate_limit_per_minute"] or 120)
        allowed, retry_after = self._check_rate_limit(key_id, per_minute)
        if not allowed:
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="rate_limited", key_id=key_id)
            return AuthResult(False, 429, f"rate_limited:{retry_after}")

        scopes = json.loads(row["scopes_json"] or "[]")
        if required_scope and required_scope not in scopes:
            self._audit("AUTH_VALIDATE", result="denied", request_id=request_id, ip=ip, reason_code="insufficient_scope", key_id=key_id)
            return AuthResult(False, 403, "insufficient_scope")

        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE llm_api_keys SET last_used_at = ? WHERE key_id = ?",
                    (_iso(_utc_now()), key_id),
                )

        principal = {
            "auth_type": "issued_api_key",
            "key_id": key_id,
            "llm_instance_id": row["llm_instance_id"],
            "scopes": scopes,
            "rate_limit_per_minute": per_minute,
            "expires_at": row["expires_at"],
        }
        return AuthResult(True, 200, "ok", principal)

    def rotate_key(self, presented_key: str, *, request_id: str = "", ip: str = "") -> AuthResult:
        validated = self.validate_api_key(presented_key, required_scope="auth:rotate", request_id=request_id, ip=ip)
        if not validated.ok or not validated.principal:
            return validated

        principal = validated.principal
        key_id = principal.get("key_id")
        if not key_id:
            return AuthResult(False, 403, "legacy_key_cannot_rotate")

        llm_instance_id = str(principal.get("llm_instance_id", "unknown"))
        scopes = list(principal.get("scopes", ["mcp:sync", "mcp:sse", "auth:rotate"]))

        replacement = self._mint_key(
            llm_instance_id=llm_instance_id,
            scopes=scopes,
            ttl_days=self.default_ttl_days,
            legacy=False,
        )

        with self._write_lock:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE llm_api_keys SET status = 'revoked', rotation_counter = rotation_counter + 1 WHERE key_id = ?",
                    (key_id,),
                )

        self._audit("KEY_ROTATED", result="success", request_id=request_id, ip=ip, llm_instance_id=llm_instance_id, key_id=replacement["key_id"])
        return AuthResult(True, 200, "ok", replacement)

    def revoke_key(self, key_id: str, *, request_id: str = "", ip: str = "", reason_code: str = "manual") -> AuthResult:
        with self._write_lock:
            with self._get_connection() as conn:
                cur = conn.execute("UPDATE llm_api_keys SET status = 'revoked' WHERE key_id = ?", (key_id,))
                changed = cur.rowcount

        if not changed:
            self._audit("KEY_REVOKED", result="denied", request_id=request_id, ip=ip, key_id=key_id, reason_code="missing_key")
            return AuthResult(False, 404, "key_not_found")

        self._audit("KEY_REVOKED", result="success", request_id=request_id, ip=ip, key_id=key_id, reason_code=reason_code)
        return AuthResult(True, 200, "ok", {"key_id": key_id, "status": "revoked"})
