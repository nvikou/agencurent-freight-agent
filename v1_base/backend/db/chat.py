"""Historique dialogue user/assistant pour le LLM."""

from __future__ import annotations

import sqlite3
from typing import Any


def save_chat_turn(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    role: str,
    content: str,
) -> None:
    """Enregistre une réplique dans chat_messages."""
    conn.execute(
        """
        INSERT INTO chat_messages (session_id, role, content, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (session_id, role, content),
    )
    conn.commit()


def load_chat_history(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Derniers messages dialogue (ordre chronologique)."""
    rows = conn.execute(
        """
        SELECT role, content, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()
    return [
        {
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]


def clear_chat_history(
    conn: sqlite3.Connection,
    *,
    session_id: str,
) -> None:
    """Efface le dialogue d'une session."""
    conn.execute(
        "DELETE FROM chat_messages WHERE session_id = ?",
        (session_id,),
    )
    conn.commit()
