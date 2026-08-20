"""Lecture / écriture des rapports analytiques."""

from __future__ import annotations

import sqlite3
from typing import Any


def save_report(
    conn: sqlite3.Connection,
    *,
    title: str,
    content_md: str,
    route_summary: str | None = None,
) -> int:
    """Enregistre un rapport Markdown et retourne son id."""
    cursor = conn.execute(
        """
        INSERT INTO reports (title, route_summary, content_md, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (title, route_summary, content_md),
    )
    conn.commit()
    return int(cursor.lastrowid)


def load_report(
    conn: sqlite3.Connection,
    report_id: int,
) -> dict[str, Any] | None:
    """Charge un rapport par id."""
    row = conn.execute(
        """
        SELECT id, title, route_summary, content_md, created_at
        FROM reports
        WHERE id = ?
        """,
        (report_id,),
    ).fetchone()
    return dict(row) if row else None


def load_latest_report(
    conn: sqlite3.Connection,
) -> dict[str, Any] | None:
    """Dernier rapport généré."""
    row = conn.execute(
        """
        SELECT id, title, route_summary, content_md, created_at
        FROM reports
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None
