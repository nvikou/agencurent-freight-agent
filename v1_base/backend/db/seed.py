"""Données de référence : transporteurs, villes, routes pilotes."""

from __future__ import annotations

import sqlite3

CARRIERS = [
    ("dellin", "Dellin"),
    ("pek", "ПЭК"),
    ("baikal", "Baikal Service"),
]

CITIES = [
    "Санкт-Петербург",
    "Москва",
    "Омск",
]

# alias pour les API des transporteurs
CITY_ALIASES: dict[str, dict[str, str]] = {
    "Санкт-Петербург": {
        "dellin": "Санкт-Петербург",
        "pek": "Санкт-Петербург",
        "baikal": "Санкт-Петербург",
    },
    "Москва": {
        "dellin": "Москва",
        "pek": "Москва",
        "baikal": "Москва",
    },
    "Омск": {
        "dellin": "Омск",
        "pek": "Омск",
        "baikal": "Омск",
    },
}

# 6 routes pilotes (3 villes)
COLLECTION_ROUTES = [
    ("Санкт-Петербург", "Москва"),
    ("Москва", "Санкт-Петербург"),
    ("Санкт-Петербург", "Омск"),
    ("Омск", "Санкт-Петербург"),
    ("Москва", "Омск"),
    ("Омск", "Москва"),
]


def seed_reference_data(conn: sqlite3.Connection) -> None:
    """Insère transporteurs, villes, alias et tâches de collecte."""
    for code, name_ru in CARRIERS:
        conn.execute(
            "INSERT OR IGNORE INTO carriers (code, name_ru) VALUES (?, ?)",
            (code, name_ru),
        )

    for city_name in CITIES:
        conn.execute(
            "INSERT OR IGNORE INTO cities (name_ru) VALUES (?)",
            (city_name,),
        )

    city_ids = {
        row["name_ru"]: row["id"]
        for row in conn.execute("SELECT id, name_ru FROM cities")
    }
    carrier_ids = {
        row["code"]: row["id"]
        for row in conn.execute("SELECT id, code FROM carriers")
    }

    for city_name, aliases in CITY_ALIASES.items():
        city_id = city_ids[city_name]
        for carrier_code, alias in aliases.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO city_aliases
                    (city_id, carrier_id, alias)
                VALUES (?, ?, ?)
                """,
                (city_id, carrier_ids[carrier_code], alias),
            )

    for departure, destination in COLLECTION_ROUTES:
        conn.execute(
            """
            INSERT OR IGNORE INTO collection_tasks
                (departure_id, destination_id, volume_m3, weight_kg, places)
            SELECT ?, ?, 1, 1, 1
            WHERE NOT EXISTS (
                SELECT 1 FROM collection_tasks
                WHERE departure_id = ? AND destination_id = ?
            )
            """,
            (
                city_ids[departure],
                city_ids[destination],
                city_ids[departure],
                city_ids[destination],
            ),
        )

    conn.commit()
