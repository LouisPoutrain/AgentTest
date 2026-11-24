"""Tests for core/history_manager.py — CRUD operations on session history."""

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any

import pytest


@pytest.fixture()
def temp_db(tmp_path: Path):
    """Return a path to a temporary SQLite database file."""
    db_path = tmp_path / "test_sessions.db"
    return db_path


@pytest.fixture()
def history_manager(temp_db: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a fresh HistoryManager backed by the temp database.

    This fixture sets the SESSIONS_DB env var and forces a re-import
    of the history_manager module so the global DB_PATH picks up the temp path.
    """
    monkeypatch.setenv("SESSIONS_DB", str(temp_db))
    # Force re-import so the module-level DB_PATH picks up the env var
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    import app.core.history_manager
    importlib.reload(app.core.history_manager)
    yield app.core.history_manager.history_manager
    # Cleanup
    if temp_db.exists():
        temp_db.unlink()


class TestInitDB:
    """Tests for database initialization."""

    def test_creates_tables(self, temp_db: Path):
        from app.core.history_manager import HistoryManager
        hm = HistoryManager()
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
        assert "sessions" in tables
        assert "messages" in tables

    def test_sessions_table_schema(self, temp_db: Path):
        from app.core.history_manager import HistoryManager
        hm = HistoryManager()
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sessions)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "session_id" in columns
        assert "user_id" in columns
        assert "created_at" in columns

    def test_messages_table_schema(self, temp_db: Path):
        from app.core.history_manager import HistoryManager
        hm = HistoryManager()
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(messages)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "message_id" in columns
        assert "session_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "timestamp" in columns
        assert "metadata" in columns


class TestGetOrCreateSession:
    """Tests for session creation and retrieval."""

    def test_creates_new_session(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session(None, "user_1")
        assert session_id is not None
        assert len(session_id) > 0

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, user_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
        assert row is not None
        assert row[0] == session_id
        assert row[1] == "user_1"

    def test_returns_existing_session(self, history_manager):
        session_id = history_manager.get_or_create_session("my-session-id", "user_1")
        assert session_id == "my-session-id"

        # Calling again should return the same ID
        session_id2 = history_manager.get_or_create_session("my-session-id", "user_2")
        assert session_id2 == "my-session-id"

    def test_generates_uuid_for_none(self, history_manager):
        session_id = history_manager.get_or_create_session(None, "user_1")
        # Should be a valid UUID string
        assert len(session_id) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    def test_default_user_id(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session(None, "default_user")
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, user_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
        assert row[1] == "default_user"

    def test_idempotent_with_same_id(self, history_manager, temp_db: Path):
        """Calling get_or_create_session with the same ID should not create duplicates."""
        history_manager.get_or_create_session("dup-test", "user_1")
        history_manager.get_or_create_session("dup-test", "user_2")

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE session_id = ?", ("dup-test",))
            count = cursor.fetchone()[0]
        assert count == 1


class TestAddMessage:
    """Tests for adding messages to a session."""

    def test_adds_user_message(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("msg-test", "user_1")
        msg_id = history_manager.add_message(session_id, "user", "Hello, world!")

        assert msg_id is not None
        assert len(msg_id) > 0

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages WHERE message_id = ?", (msg_id,))
            row = cursor.fetchone()
        assert row[0] == "user"
        assert row[1] == "Hello, world!"

    def test_adds_assistant_message(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("msg-test", "user_1")
        msg_id = history_manager.add_message(session_id, "assistant", "Hi there!")

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages WHERE message_id = ?", (msg_id,))
            row = cursor.fetchone()
        assert row[0] == "assistant"
        assert row[1] == "Hi there!"

    def test_stores_crew_used(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("msg-test", "user_1")
        msg_id = history_manager.add_message(
            session_id, "assistant", "Done!", crew_used="code_review"
        )

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT crew_used FROM messages WHERE message_id = ?", (msg_id,))
            row = cursor.fetchone()
        assert row[0] == "code_review"

    def test_stores_metadata_as_json(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("msg-test", "user_1")
        metadata = {"duration_ms": 1234, "tokens": 500}
        msg_id = history_manager.add_message(
            session_id, "assistant", "Done!", metadata=metadata
        )

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata FROM messages WHERE message_id = ?", (msg_id,))
            row = cursor.fetchone()
        assert row[0] is not None
        parsed = json.loads(row[0])
        assert parsed["duration_ms"] == 1234
        assert parsed["tokens"] == 500

    def test_stores_null_metadata(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("msg-test", "user_1")
        msg_id = history_manager.add_message(session_id, "user", "Hello", metadata=None)

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata FROM messages WHERE message_id = ?", (msg_id,))
            row = cursor.fetchone()
        assert row[0] is None

    def test_multiple_messages(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("msg-test", "user_1")
        msg_id_1 = history_manager.add_message(session_id, "user", "First")
        msg_id_2 = history_manager.add_message(session_id, "assistant", "Second")
        msg_id_3 = history_manager.add_message(session_id, "user", "Third")

        assert msg_id_1 != msg_id_2
        assert msg_id_2 != msg_id_3
        assert msg_id_1 != msg_id_3

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
            count = cursor.fetchone()[0]
        assert count == 3


class TestGetHistory:
    """Tests for retrieving session history."""

    def test_returns_empty_for_unknown_session(self, history_manager):
        result = history_manager.get_history("nonexistent")
        assert result == []

    def test_returns_messages_in_chronological_order(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        history_manager.add_message(session_id, "user", "First")
        time.sleep(0.01)
        history_manager.add_message(session_id, "assistant", "Second")
        time.sleep(0.01)
        history_manager.add_message(session_id, "user", "Third")

        result = history_manager.get_history(session_id)
        assert len(result) == 3
        assert result[0]["content"] == "First"
        assert result[1]["content"] == "Second"
        assert result[2]["content"] == "Third"

    def test_respects_limit(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        for i in range(10):
            history_manager.add_message(session_id, "user", f"Message {i}")

        result = history_manager.get_history(session_id, limit=3)
        assert len(result) == 3
        # Should be the last 3 messages
        assert result[0]["content"] == "Message 7"
        assert result[1]["content"] == "Message 8"
        assert result[2]["content"] == "Message 9"

    def test_default_limit_is_20(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        for i in range(25):
            history_manager.add_message(session_id, "user", f"Message {i}")

        result = history_manager.get_history(session_id)
        assert len(result) == 20

    def test_includes_crew_used(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        history_manager.add_message(
            session_id, "assistant", "Done!", crew_used="code_review"
        )

        result = history_manager.get_history(session_id)
        assert result[0]["crew_used"] == "code_review"

    def test_includes_metadata(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        metadata = {"duration_ms": 42}
        history_manager.add_message(
            session_id, "assistant", "Done!", metadata=metadata
        )

        result = history_manager.get_history(session_id)
        assert result[0]["metadata"] == {"duration_ms": 42}

    def test_includes_null_metadata(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        history_manager.add_message(session_id, "assistant", "Done!", metadata=None)

        result = history_manager.get_history(session_id)
        assert result[0]["metadata"] is None

    def test_includes_null_crew_used(self, history_manager):
        session_id = history_manager.get_or_create_session("hist-test", "user_1")
        history_manager.add_message(session_id, "user", "Hello")

        result = history_manager.get_history(session_id)
        assert result[0]["crew_used"] is None


class TestClearSession:
    """Tests for clearing session history."""

    def test_clears_messages(self, history_manager):
        session_id = history_manager.get_or_create_session("clear-test", "user_1")
        history_manager.add_message(session_id, "user", "Message 1")
        history_manager.add_message(session_id, "assistant", "Reply 1")

        history_manager.clear_session(session_id)

        result = history_manager.get_history(session_id)
        assert result == []

    def test_does_not_delete_session(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("clear-test", "user_1")
        history_manager.add_message(session_id, "user", "Message 1")
        history_manager.clear_session(session_id)

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE session_id = ?", (session_id,))
            count = cursor.fetchone()[0]
        assert count == 1

    def test_clears_nonexistent_session(self, history_manager):
        """Should not raise for a session that doesn't exist."""
        history_manager.clear_session("nonexistent-session")

    def test_clears_all_messages(self, history_manager, temp_db: Path):
        session_id = history_manager.get_or_create_session("clear-test", "user_1")
        for i in range(5):
            history_manager.add_message(session_id, "user", f"Message {i}")

        history_manager.clear_session(session_id)

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
            count = cursor.fetchone()[0]
        assert count == 0


class TestGlobalInstance:
    """Tests for the global history_manager singleton."""

    def test_global_instance_exists(self):
        from app.core.history_manager import history_manager
        from app.core.history_manager import HistoryManager
        assert history_manager is not None
        assert isinstance(history_manager, HistoryManager)
