"""Tools BDD : quotes et comparaison transport de base."""

from __future__ import annotations

import json
from typing import Any

from db.connection import get_connection
from db.quotes import load_all_quotes, load_quotes


LOAD_QUOTES_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "load_quotes_from_db",
        "description": (
            "Читает ИСТОРИЮ цен из SQLite (снимки collected_at). "
            "Поля: transport_price, delivery_days, source "
            "(collect|live), collected_at. "
            "Вызывать для сравнения LIVE (сейчас) vs история. "
            "По умолчанию — все снимки; latest_only=true — "
            "только последний по каждому маршруту."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": (
                        "ID задачи сбора (опционально). "
                        "Если не указан — все quotes."
                    ),
                },
                "latest_only": {
                    "type": "boolean",
                    "description": (
                        "true = только последний snapshot "
                        "на пару маршрут+перевозчик"
                    ),
                },
            },
            "required": [],
        },
    },
}

OPENAI_TOOLS = [LOAD_QUOTES_TOOL]


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Exécute un tool BDD."""
    if isinstance(arguments, str):
        payload = json.loads(arguments) if arguments.strip() else {}
    else:
        payload = arguments or {}

    if name == "load_quotes_from_db":
        conn = get_connection()
        try:
            task_id = payload.get("task_id")
            latest_only = bool(payload.get("latest_only", False))
            if task_id is not None:
                rows = load_quotes(
                    conn,
                    int(task_id),
                    latest_only=latest_only,
                )
            else:
                rows = load_all_quotes(
                    conn,
                    latest_only=latest_only,
                )
        finally:
            conn.close()

        comparable = [
            {
                "task_id": row.get("task_id"),
                "departure": row["departure"],
                "destination": row["destination"],
                "carrier": row["carrier_code"],
                "transport_price": row["transport_price"],
                "delivery_days": row["delivery_days"],
                "status": row["status"],
                "source": row.get("source"),
                "collected_at": row["collected_at"],
                "error_message": row.get("error_message"),
            }
            for row in rows
        ]
        return json.dumps(
            {
                "rule": (
                    "Только транспорт база, Стандарт, "
                    "без упаковки и опций"
                ),
                "count": len(comparable),
                "quotes": comparable,
            },
            ensure_ascii=False,
        )

    raise ValueError(f"Unknown tool: {name}")
