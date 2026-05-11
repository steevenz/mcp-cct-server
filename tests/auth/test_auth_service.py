from __future__ import annotations

import hashlib
import hmac
import sqlite3

from src.core.services.auth.handshake import AuthService


def _make_service(tmp_path):
    db_path = tmp_path / "auth_test.db"
    return AuthService(str(db_path), "bootstrap-secret", auth_mode="dual", default_ttl_days=7, legacy_enabled=True)


def test_legacy_key_validation(tmp_path):
    service = _make_service(tmp_path)
    result = service.validate_api_key("bootstrap-secret", required_scope="mcp:sync")
    assert result.ok is True
    assert result.principal
    assert result.principal["auth_type"] == "legacy_shared_key"


def test_handshake_issue_and_validate_scoped_key(tmp_path):
    service = _make_service(tmp_path)
    init = service.handshake_init("llm-alpha", "nonce-1")
    material = f"{init['handshake_id']}:llm-alpha:{init['challenge']}".encode("utf-8")
    proof = hmac.new(b"bootstrap-secret", material, hashlib.sha256).hexdigest()

    completed = service.handshake_complete(init["handshake_id"], proof, "bootstrap-secret")
    assert completed.ok is True
    assert completed.principal

    issued_key = completed.principal["api_key"]
    valid_sync = service.validate_api_key(issued_key, required_scope="mcp:sync")
    assert valid_sync.ok is True

    invalid_admin = service.validate_api_key(issued_key, required_scope="admin:revoke")
    assert invalid_admin.ok is False
    assert invalid_admin.message == "insufficient_scope"


def test_rotate_key_revokes_old_token(tmp_path):
    service = _make_service(tmp_path)
    init = service.handshake_init("llm-rotate", "nonce-2")
    material = f"{init['handshake_id']}:llm-rotate:{init['challenge']}".encode("utf-8")
    proof = hmac.new(b"bootstrap-secret", material, hashlib.sha256).hexdigest()
    completed = service.handshake_complete(init["handshake_id"], proof, "bootstrap-secret")
    old_key = completed.principal["api_key"]

    rotated = service.rotate_key(old_key)
    assert rotated.ok is True
    new_key = rotated.principal["api_key"]

    old_check = service.validate_api_key(old_key)
    assert old_check.ok is False
    assert old_check.message == "revoked_or_inactive_key"

    new_check = service.validate_api_key(new_key, required_scope="mcp:sync")
    assert new_check.ok is True


def test_rate_limit_is_enforced(tmp_path):
    service = _make_service(tmp_path)
    init = service.handshake_init("llm-rate", "nonce-3")
    material = f"{init['handshake_id']}:llm-rate:{init['challenge']}".encode("utf-8")
    proof = hmac.new(b"bootstrap-secret", material, hashlib.sha256).hexdigest()
    completed = service.handshake_complete(init["handshake_id"], proof, "bootstrap-secret")
    key = completed.principal["api_key"]
    key_id = completed.principal["key_id"]

    with sqlite3.connect(service.db_path) as conn:
        conn.execute("UPDATE llm_api_keys SET rate_limit_per_minute = 1 WHERE key_id = ?", (key_id,))

    first = service.validate_api_key(key, required_scope="mcp:sync")
    second = service.validate_api_key(key, required_scope="mcp:sync")

    assert first.ok is True
    assert second.ok is False
    assert second.code == 429
    assert second.message.startswith("rate_limited:")


def test_handshake_only_mode_rejects_legacy_key(tmp_path):
    db_path = tmp_path / "auth_test_mode.db"
    service = AuthService(str(db_path), "bootstrap-secret", auth_mode="handshake_only", default_ttl_days=7, legacy_enabled=True)
    result = service.validate_api_key("bootstrap-secret")
    assert result.ok is False
    assert result.message == "invalid_api_key_format"
