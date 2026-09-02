"""
core/history_manager.py — Gestion de la persistance des conversations.
Utilise SQLite pour stocker les sessions et les messages.
"""

from __future__ import annotations

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Chemin vers la DB à la racine du backend
DB_PATH = Path(__file__).resolve().parent.parent.parent / "sessions.db"

class HistoryManager:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialise la base de données si elle n'existe pas."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            # Table des sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table des messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    crew_used TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()

    def get_or_create_session(self, session_id: Optional[str], user_id: str = "default_user") -> str:
        """Récupère une session existante ou en crée une nouvelle."""
        if not session_id:
            session_id = str(uuid.uuid4())

        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
                    (session_id, user_id)
                )
                conn.commit()
        return session_id

    def add_message(self, session_id: str, role: str, content: str, crew_used: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """Ajoute un message à l'historique d'une session."""
        msg_id = str(uuid.uuid4())
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (message_id, session_id, role, content, crew_used, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, datetime.now(timezone.utc).isoformat(), crew_used, json.dumps(metadata) if metadata else None)
            )
            conn.commit()
        return msg_id

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère les derniers messages d'une session pour le contexte."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, crew_used, metadata FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            # On inverse pour avoir l'ordre chronologique
            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "crew_used": row["crew_used"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
                for row in reversed(rows)
            ]

    def clear_session(self, session_id: str) -> None:
        """Supprime l'historique d'une session."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()

# Instance globale
history_manager = HistoryManager()
