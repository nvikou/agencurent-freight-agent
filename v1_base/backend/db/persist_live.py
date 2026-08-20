"""Persistance des calculs LIVE dans quotes (source=live)."""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any

from db.extract import extract_base_transport_price
from db.quotes import save_quote

logger = logging.getLogger(__name__)

CARRIER_BY_TOOL = {
    "calculate_dellin_shipping": "dellin",
    "calculate_pek_shipping": "pek",
    "calculate_baikal_shipping": "baikal",
}


def _find_task_id(
    conn: sqlite3.Connection,
    departure: str,
    destination: str,
) -> int | None:
    row = conn.execute(
        """
        SELECT t.id
        FROM collection_tasks t
        JOIN cities c_from ON c_from.id = t.departure_id
        JOIN cities c_to ON c_to.id = t.destination_id
        WHERE c_from.name_ru = ? AND c_to.name_ru = ?
          AND t.is_active = 1
        """,
        (departure, destination),
    ).fetchone()
    return int(row["id"]) if row else None


def _find_carrier_id(
    conn: sqlite3.Connection,
    code: str,
) -> int | None:
    row = conn.execute(
        "SELECT id FROM carriers WHERE code = ?",
        (code,),
    ).fetchone()
    return int(row["id"]) if row else None


def persist_live_from_tool(
    conn: sqlite3.Connection,
    tool_name: str,
    arguments: dict[str, Any],
    tool_result_json: str,
) -> dict[str, Any] | None:
    """
    Après un calcul LIVE réussi, enregistre un snapshot quotes.

    Retourne un résumé ou None si non applicable.
    """
    carrier_code = CARRIER_BY_TOOL.get(tool_name)
    if carrier_code is None:
        return None

    try:
        payload = json.loads(tool_result_json)
    except json.JSONDecodeError:
        return None

    if payload.get("error"):
        return None

    result = payload.get("result") or {}
    departure = str(arguments.get("departure_city", "")).strip()
    destination = str(arguments.get("destination_city", "")).strip()
    if not departure or not destination:
        return None

    task_id = _find_task_id(conn, departure, destination)
    carrier_id = _find_carrier_id(conn, carrier_code)
    if task_id is None or carrier_id is None:
        logger.warning(
            "LIVE non sauvé: task/carrier introuvable "
            "(%s → %s / %s)",
            departure,
            destination,
            carrier_code,
        )
        return None

    try:
        price = extract_base_transport_price(carrier_code, result)
    except ValueError as exc:
        logger.warning("LIVE extract fail: %s", exc)
        return None

    days = result.get("delivery_days")
    if days is not None:
        days = int(days)

    quote_id = save_quote(
        conn,
        task_id=task_id,
        carrier_id=carrier_id,
        transport_price=price,
        delivery_days=days,
        status="ok",
        source="live",
    )
    return {
        "quote_id": quote_id,
        "carrier": carrier_code,
        "route": f"{departure} → {destination}",
        "transport_price": price,
        "delivery_days": days,
        "source": "live",
    }
