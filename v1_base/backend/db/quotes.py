"""Lecture / écriture des quotes (historique append-only)."""

from __future__ import annotations

import sqlite3
from typing import Any

_SELECT_BODY = """
    SELECT
        q.id,
        q.task_id,
        c_from.name_ru AS departure,
        c_to.name_ru AS destination,
        t.volume_m3,
        t.weight_kg,
        t.places,
        t.tariff_type,
        car.code AS carrier_code,
        car.name_ru AS carrier_name,
        q.transport_price,
        q.delivery_days,
        q.status,
        q.error_message,
        q.source,
        q.collected_at
    FROM quotes q
    JOIN collection_tasks t ON t.id = q.task_id
    JOIN cities c_from ON c_from.id = t.departure_id
    JOIN cities c_to ON c_to.id = t.destination_id
    JOIN carriers car ON car.id = q.carrier_id
"""

_LATEST_CLAUSE = """
    AND q.id = (
        SELECT q2.id FROM quotes q2
        WHERE q2.task_id = q.task_id
          AND q2.carrier_id = q.carrier_id
        ORDER BY q2.id DESC
        LIMIT 1
    )
"""


def save_quote(
    conn: sqlite3.Connection,
    *,
    task_id: int,
    carrier_id: int,
    transport_price: float | None,
    delivery_days: int | None,
    status: str,
    error_message: str | None = None,
    source: str = "collect",
) -> int:
    """Insère un snapshot de prix (ne remplace pas l'historique)."""
    cur = conn.execute(
        """
        INSERT INTO quotes (
            task_id, carrier_id, transport_price,
            delivery_days, status, error_message, source,
            collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            task_id,
            carrier_id,
            transport_price,
            delivery_days,
            status,
            error_message,
            source,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def load_quotes(
    conn: sqlite3.Connection,
    task_id: int,
    *,
    latest_only: bool = False,
) -> list[dict[str, Any]]:
    """Quotes d'une tâche (historique ou dernier snapshot)."""
    sql = _SELECT_BODY + " WHERE q.task_id = ?"
    if latest_only:
        sql += _LATEST_CLAUSE
    sql += " ORDER BY car.code, q.id"
    rows = conn.execute(sql, (task_id,)).fetchall()
    return [dict(row) for row in rows]


def load_all_quotes(
    conn: sqlite3.Connection,
    *,
    latest_only: bool = False,
) -> list[dict[str, Any]]:
    """Toutes les quotes (historique complet ou derniers)."""
    sql = _SELECT_BODY + " WHERE 1=1"
    if latest_only:
        sql += _LATEST_CLAUSE
    sql += (
        " ORDER BY c_from.name_ru, c_to.name_ru, "
        "car.code, q.id"
    )
    rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def load_latest_quotes(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Dernier snapshot par (route, transporteur)."""
    return load_all_quotes(conn, latest_only=True)
