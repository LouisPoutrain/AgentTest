"""Tests for core/config.py — path resolution and env validation."""

import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture()
def fresh_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Reset config module so env vars are re-read."""
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("SESSIONS_DB", str(tmp_path / "sessions.db"))
    import app.core.config
    importlib.reload(app.core.config)
    return app.core.config


class TestPathResolution:
    """Tests that config resolves paths correctly from env vars."""

    def test_project_root_from_env(self, fresh_config, tmp_path: Path):
        assert fresh_config.PROJECT_ROOT == tmp_path.resolve()

    def test_crews_dir_exists_and_is_dir(self, fresh_config):
        # CREWS_DIR is fixed to backend/config/crews (not dynamically under PROJECT_ROOT)
        assert fresh_config.CREWS_DIR.is_dir()

    def test_config_dir_exists_and_is_dir(self, fresh_config):
        # CONFIG_DIR is fixed to backend/config (not dynamically under PROJECT_ROOT)
        assert fresh_config.CONFIG_DIR.is_dir()

    def test_db_path_from_env(self, fresh_config, tmp_path: Path):
        assert fresh_config.DB_PATH == tmp_path.resolve() / "sessions.db"

    def test_db_path_default(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        monkeypatch.delenv("SESSIONS_DB", raising=False)
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
        import app.core.config
        importlib.reload(app.core.config)
        # Defaults to PROJECT_ROOT / "sessions.db" (one level above backend/)
        assert app.core.config.DB_PATH == tmp_path.resolve() / "sessions.db"

    def test_crews_dir_created(self, fresh_config):
        assert fresh_config.CREWS_DIR.is_dir()

    def test_config_dir_created(self, fresh_config):
        assert fresh_config.CONFIG_DIR.is_dir()


class TestValidateEnv:
    """Tests that validate_env() catches missing required variables."""

    def test_returns_errors_when_all_missing(self, env_clean):
        import app.core.config
        importlib.reload(app.core.config)
        errors = app.core.config.validate_env()
        assert len(errors) == 2
        assert any("LLM_API_KEY" in e for e in errors)
        assert any("LLM_BASE_URL" in e for e in errors)

    def test_returns_empty_when_all_present(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LLM_API_KEY", "fake-llm-key")
        monkeypatch.setenv("LLM_BASE_URL", "http://localhost:8000/v1")
        import app.core.config
        importlib.reload(app.core.config)
        errors = app.core.config.validate_env()
        assert errors == []

    def test_returns_partial_errors_when_some_missing(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        import app.core.config
        importlib.reload(app.core.config)
        errors = app.core.config.validate_env()
        assert len(errors) == 2

    def test_error_messages_are_descriptive(self, env_clean):
        import app.core.config
        importlib.reload(app.core.config)
        errors = app.core.config.validate_env()
        for error in errors:
            assert "manquante" in error or "missing" in error.lower() or "required" in error.lower()

    def test_each_error_mentions_variable_and_description(self, env_clean):
        import app.core.config
        importlib.reload(app.core.config)
        errors = app.core.config.validate_env()
        # Each error should contain the variable name and a description
        for error in errors:
            assert " : " in error  # separator between var name and description
            parts = error.split(" : ", 1)
            assert len(parts) == 2
            assert len(parts[0]) > 0  # variable name is present
            assert len(parts[1]) > 0  # description is present


class TestDefaultPaths:
    """Tests for default path computation when env vars are not set."""

    def test_default_project_root_is_extended_root(self, monkeypatch: pytest.MonkeyPatch):
        """Default PROJECT_ROOT should be the extended root (Code/ parent of backend/)."""
        import importlib
        monkeypatch.delenv("PROJECT_ROOT", raising=False)
        import app.core.config
        importlib.reload(app.core.config)
        # The default is Path(__file__).resolve().parent.parent.parent.parent
        # which for core/config.py is: core/ -> app/ -> backend/ -> AgentTest/ -> Code/
        # From test_config.py: tests/ -> backend/ -> AgentTest/ -> Code/
        expected = Path(__file__).resolve().parent.parent.parent
        assert app.core.config.PROJECT_ROOT == expected

    def test_default_crewn_dir_is_project_config_crews(self, monkeypatch: pytest.MonkeyPatch):
        import importlib
        monkeypatch.delenv("PROJECT_ROOT", raising=False)
        monkeypatch.delenv("CREWS_DIR", raising=False)
        import app.core.config
        importlib.reload(app.core.config)
        # CREWS_DIR is fixed to backend/config/crews (not dynamically under PROJECT_ROOT)
        expected = Path(__file__).resolve().parent.parent / "config" / "crews"
        assert app.core.config.CREWS_DIR == expected

    def test_default_config_dir_is_project_config(self, monkeypatch: pytest.MonkeyPatch):
        import importlib
        monkeypatch.delenv("PROJECT_ROOT", raising=False)
        monkeypatch.delenv("CONFIG_DIR", raising=False)
        import app.core.config
        importlib.reload(app.core.config)
        # CONFIG_DIR is fixed to backend/config (not dynamically under PROJECT_ROOT)
        expected = Path(__file__).resolve().parent.parent / "config"
        assert app.core.config.CONFIG_DIR == expected
