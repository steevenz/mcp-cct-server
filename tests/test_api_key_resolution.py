from pathlib import Path

import pytest

from src.core.security import (
    ApiKeyResolutionError,
    build_x_api_key_header,
    resolve_bootstrap_api_key,
)


def test_resolve_bootstrap_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CCT_BOOTSTRAP_API_KEY", "env-key-123")
    assert resolve_bootstrap_api_key(source="env") == "env-key-123"


def test_resolve_bootstrap_api_key_from_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CCT_BOOTSTRAP_API_KEY", raising=False)
    monkeypatch.delenv("CCT_DASHBOARD_API_KEY", raising=False)
    (tmp_path / ".env").write_text("CCT_BOOTSTRAP_API_KEY=dotenv-key-456\n", encoding="utf-8")
    assert resolve_bootstrap_api_key(project_root=tmp_path) == "dotenv-key-456"


def test_resolve_bootstrap_api_key_missing_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CCT_BOOTSTRAP_API_KEY", raising=False)
    monkeypatch.delenv("CCT_DASHBOARD_API_KEY", raising=False)
    with pytest.raises(ApiKeyResolutionError, match="does not generate API keys algorithmically"):
        resolve_bootstrap_api_key(project_root=tmp_path)


def test_build_x_api_key_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CCT_BOOTSTRAP_API_KEY", "header-key-789")
    assert build_x_api_key_header(source="env") == {"X-API-KEY": "header-key-789"}


def test_resolve_bootstrap_api_key_mismatch_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CCT_BOOTSTRAP_API_KEY", "env-key")
    (tmp_path / ".env").write_text("CCT_BOOTSTRAP_API_KEY=dotenv-key\n", encoding="utf-8")
    with pytest.raises(ApiKeyResolutionError, match="mismatch"):
        resolve_bootstrap_api_key(project_root=tmp_path)


def test_resolve_bootstrap_api_key_dotenv_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CCT_BOOTSTRAP_API_KEY", "env-key")
    (tmp_path / ".env").write_text("CCT_BOOTSTRAP_API_KEY=dotenv-key\n", encoding="utf-8")
    assert resolve_bootstrap_api_key(project_root=tmp_path, source="dotenv") == "dotenv-key"
