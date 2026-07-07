"""
Lightweight SQLite persistence layer. No ORM — the schema is tiny and this keeps the
dependency footprint minimal while remaining trivial to read and extend.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional

from app.models.conversation import Conversation
from app.models.message import Message, Role

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    pinned      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages (conversation_id);
"""


class DatabaseManager:
    """Owns the single SQLite connection used by the whole application."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._cursor() as cur:
            cur.executescript(_SCHEMA)

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        finally:
            cur.close()

    # ------------------------------------------------------------------ #
    # Conversations
    # ------------------------------------------------------------------ #
    def create_conversation(self, title: str = "New chat") -> Conversation:
        now = datetime.now().isoformat(timespec="seconds")
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (title, created_at, updated_at, pinned) "
                "VALUES (?, ?, ?, 0)",
                (title, now, now),
            )
            new_id = cur.lastrowid
        return Conversation(
            id=new_id,
            title=title,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            message_count=0,
            pinned=False,
        )

    def list_conversations(self, search: str = "") -> List[Conversation]:
        query = """
            SELECT c.id, c.title, c.created_at, c.updated_at, c.pinned,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
        """
        params: tuple = ()
        if search:
            query += " WHERE c.title LIKE ? "
            params = (f"%{search}%",)
        query += " GROUP BY c.id ORDER BY c.pinned DESC, c.updated_at DESC"

        with self._cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        return [
            Conversation(
                id=row["id"],
                title=row["title"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                message_count=row["message_count"],
                pinned=bool(row["pinned"]),
            )
            for row in rows
        ]

    def rename_conversation(self, conversation_id: int, new_title: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (new_title, conversation_id),
            )

    def set_pinned(self, conversation_id: int, pinned: bool) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE conversations SET pinned = ? WHERE id = ?",
                (int(pinned), conversation_id),
            )

    def touch_conversation(self, conversation_id: int) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(timespec="seconds"), conversation_id),
            )

    def delete_conversation(self, conversation_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    # ------------------------------------------------------------------ #
    # Messages
    # ------------------------------------------------------------------ #
    def add_message(self, message: Message) -> Message:
        now = message.created_at.isoformat(timespec="seconds")
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (message.conversation_id, message.role.value, message.content, now),
            )
            message.id = cur.lastrowid
        self.touch_conversation(message.conversation_id)
        return message

    def update_message_content(self, message_id: int, content: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE messages SET content = ? WHERE id = ?", (content, message_id)
            )

    def delete_messages_after(self, conversation_id: int, message_id: int) -> None:
        """Used when editing a user message: drop everything after it."""
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM messages WHERE conversation_id = ? AND id >= ?",
                (conversation_id, message_id),
            )

    def get_messages(self, conversation_id: int) -> List[Message]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, conversation_id, role, content, created_at FROM messages "
                "WHERE conversation_id = ? ORDER BY id ASC",
                (conversation_id,),
            )
            rows = cur.fetchall()
        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=Role(row["role"]),
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def delete_last_assistant_message(self, conversation_id: int) -> Optional[int]:
        """Remove the trailing assistant message (used before regenerating)."""
        messages = self.get_messages(conversation_id)
        if messages and messages[-1].role == Role.ASSISTANT:
            with self._cursor() as cur:
                cur.execute("DELETE FROM messages WHERE id = ?", (messages[-1].id,))
            return messages[-1].id
        return None

    def close(self) -> None:
        self._conn.close()
