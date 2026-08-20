"""Crée la BDD et insère les données de référence."""

from __future__ import annotations

from db.connection import default_db_path, get_connection, init_schema
from db.seed import seed_reference_data


def main() -> None:
    conn = get_connection()
    init_schema(conn)
    seed_reference_data(conn)
    conn.close()
    print(f"БД готова: {default_db_path()}")


if __name__ == "__main__":
    main()
