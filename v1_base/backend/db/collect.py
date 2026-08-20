"""Collecte des prix transport de base depuis les calculateurs v1."""

from __future__ import annotations

import sqlite3
from typing import Any

from baikal.calculator import calculate_shipping as calculate_baikal
from dellin.calculator import calculate_shipping as calculate_dellin
from pek.calculator import calculate_shipping as calculate_pek

from db.extract import extract_base_transport_price
from db.quotes import save_quote


def _fetch_tasks(
    conn: sqlite3.Connection,
    task_id: int | None = None,
) -> list[sqlite3.Row]:
    query = """
        SELECT
            t.id,
            t.volume_m3,
            t.weight_kg,
            t.places,
            t.tariff_type,
            c_from.name_ru AS departure,
            c_to.name_ru AS destination
        FROM collection_tasks t
        JOIN cities c_from ON c_from.id = t.departure_id
        JOIN cities c_to ON c_to.id = t.destination_id
        WHERE t.is_active = 1
    """
    params: tuple[Any, ...] = ()
    if task_id is not None:
        query += " AND t.id = ?"
        params = (task_id,)
    query += " ORDER BY t.id"
    return conn.execute(query, params).fetchall()


def _fetch_carriers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, code FROM carriers ORDER BY id"
    ).fetchall()


def _city_alias(
    conn: sqlite3.Connection,
    city_name: str,
    carrier_id: int,
) -> str:
    row = conn.execute(
        """
        SELECT a.alias
        FROM city_aliases a
        JOIN cities c ON c.id = a.city_id
        WHERE c.name_ru = ? AND a.carrier_id = ?
        """,
        (city_name, carrier_id),
    ).fetchone()
    if row is None:
        return city_name
    return row["alias"]


def _call_calculator(
    carrier_code: str,
    departure: str,
    destination: str,
    volume_m3: float,
    weight_kg: float,
    places: int,
) -> dict[str, Any]:
    """Appel sans options : transport de base uniquement."""
    if carrier_code == "dellin":
        return calculate_dellin(
            departure_city=departure,
            destination_city=destination,
            volume_m3=volume_m3,
            weight_kg=weight_kg,
            places=places,
        )
    if carrier_code == "pek":
        return calculate_pek(
            departure_city=departure,
            destination_city=destination,
            volume_m3=volume_m3,
            weight_kg=weight_kg,
            places=places,
        )
    if carrier_code == "baikal":
        return calculate_baikal(
            departure_city=departure,
            destination_city=destination,
            volume_m3=volume_m3,
            weight_kg=weight_kg,
            places=places,
        )
    raise ValueError(f"Неизвестный перевозчик: {carrier_code}")


def collect_task(
    conn: sqlite3.Connection,
    task_id: int,
) -> list[dict[str, Any]]:
    """Collecte les quotes pour une tâche."""
    tasks = _fetch_tasks(conn, task_id=task_id)
    if not tasks:
        raise ValueError(f"Задача {task_id} не найдена")

    results: list[dict[str, Any]] = []
    for task in tasks:
        results.extend(_collect_one_task(conn, task))
    return results


def collect_all(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Collecte toutes les tâches actives."""
    results: list[dict[str, Any]] = []
    for task in _fetch_tasks(conn):
        results.extend(_collect_one_task(conn, task))
    return results


def _collect_one_task(
    conn: sqlite3.Connection,
    task: sqlite3.Row,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for carrier in _fetch_carriers(conn):
        departure = _city_alias(
            conn, task["departure"], carrier["id"]
        )
        destination = _city_alias(
            conn, task["destination"], carrier["id"]
        )
        try:
            raw = _call_calculator(
                carrier["code"],
                departure,
                destination,
                task["volume_m3"],
                task["weight_kg"],
                task["places"],
            )
            price = extract_base_transport_price(carrier["code"], raw)
            days = raw.get("delivery_days")
            if days is not None:
                days = int(days)
            save_quote(
                conn,
                task_id=task["id"],
                carrier_id=carrier["id"],
                transport_price=price,
                delivery_days=days,
                status="ok",
                source="collect",
            )
            collected.append(
                {
                    "task_id": task["id"],
                    "route": f"{task['departure']} → {task['destination']}",
                    "carrier": carrier["code"],
                    "transport_price": price,
                    "delivery_days": days,
                    "status": "ok",
                }
            )
        except Exception as exc:
            save_quote(
                conn,
                task_id=task["id"],
                carrier_id=carrier["id"],
                transport_price=None,
                delivery_days=None,
                status="error",
                error_message=str(exc),
                source="collect",
            )
            collected.append(
                {
                    "task_id": task["id"],
                    "route": f"{task['departure']} → {task['destination']}",
                    "carrier": carrier["code"],
                    "status": "error",
                    "error_message": str(exc),
                }
            )
    return collected
