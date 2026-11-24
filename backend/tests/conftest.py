"""Shared fixtures for all backend tests."""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary directory that looks like a project root (backend/ inside)."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "backend").mkdir()
    (project / "config").mkdir()
    (project / "config" / "crews").mkdir()
    return project


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with sibling projects."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "backend").mkdir()
    (workspace / "frontend").mkdir()
    return workspace


@pytest.fixture()
def sample_crew_yaml(tmp_path: Path) -> Path:
    """Write a minimal crew YAML file."""
    crew_dir = tmp_path / "config" / "crews"
    crew_dir.mkdir(parents=True, exist_ok=True)
    crew_file = crew_dir / "test_crew.yaml"
    crew_file.write_text(
        "name: test_crew\n"
        "description: A test crew\n"
        "tasks:\n"
        "  - name: test_task\n"
        "    description: Do something\n"
    )
    return crew_file


@pytest.fixture()
def sample_capabilities(tmp_path: Path) -> Path:
    """Write a minimal capabilities.json."""
    caps_file = tmp_path / "config" / "capabilities.json"
    caps_file.write_text(
        json.dumps({
            "crews": {
                "test_crew": {"description": "A test crew"},
            },
            "model_tiers": {
                "fast": "openai/qwen-3.6-35b-instruct",
                "balanced": "openai/qwen-3.6-35b-instruct",
                "expert": "openai/qwen-3.6-35b-instruct",
            },
        })
    )
    return caps_file


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    """Return a path to a temporary SQLite database file. The DB is initialised by HistoryManager."""
    db_path = tmp_path / "test_sessions.db"
    return db_path


@pytest.fixture(autouse=True)
def _override_db_path(temp_db: Path, monkeypatch: pytest.MonkeyPatch):
    """Make HistoryManager use the temp database for every test."""
    monkeypatch.setenv("SESSIONS_DB", str(temp_db))
    # Force re-import so the module-level DB_PATH picks up the env var
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    import app.core.history_manager
    importlib.reload(app.core.history_manager)
    yield
    # Cleanup
    if temp_db.exists():
        temp_db.unlink()


@pytest.fixture()
def env_clean(monkeypatch: pytest.MonkeyPatch):
    """Remove all LLM-related env vars so validate_env() returns errors."""
    for key in ("LLM_API_KEY", "LLM_BASE_URL", "PROJECT_ROOT"):
        monkeypatch.delenv(key, raising=False)
    return env_clean
