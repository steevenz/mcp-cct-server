from __future__ import annotations

from pathlib import Path

import pytest

from scripts.server.discover import resolve_tls_verify


def test_resolve_tls_verify_http_returns_true(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CCT_CA_BUNDLE", raising=False)
    assert resolve_tls_verify("http://localhost:8001/health") is True


def test_resolve_tls_verify_https_defaults_to_system_store(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CCT_CA_BUNDLE", raising=False)
    assert resolve_tls_verify("https://example.com/health") is True


def test_resolve_tls_verify_https_rejects_missing_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    missing = tmp_path / "missing-ca.pem"
    monkeypatch.setenv("CCT_CA_BUNDLE", str(missing))
    with pytest.raises(RuntimeError, match="CCT_CA_BUNDLE"):
        resolve_tls_verify("https://example.com/health")


def test_resolve_tls_verify_https_uses_custom_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    bundle = tmp_path / "ca.pem"
    bundle.write_text("-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n", encoding="utf-8")
    monkeypatch.setenv("CCT_CA_BUNDLE", str(bundle))
    assert resolve_tls_verify("https://example.com/health") == str(bundle.resolve())


def test_resolve_tls_verify_https_unreadable_bundle_falls_back_to_system_store(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    bundle = tmp_path / "ca.pem"
    bundle.write_text("-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n", encoding="utf-8")
    monkeypatch.setenv("CCT_CA_BUNDLE", str(bundle))
    monkeypatch.setattr("scripts.server.discover.os.access", lambda *_: False)
    assert resolve_tls_verify("https://example.com/health") is True
