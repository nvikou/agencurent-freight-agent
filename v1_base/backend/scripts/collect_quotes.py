"""Collecte les prix transport de base et les enregistre en BDD."""

from __future__ import annotations

import argparse

from db.collect import collect_all, collect_task
from db.connection import get_connection, init_schema
from db.quotes import load_all_quotes
from db.seed import seed_reference_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collecte transport de base (Стандарт, sans options)",
    )
    parser.add_argument(
        "--task-id",
        type=int,
        default=None,
        help="ID задачи (sinon toutes les routes actives)",
    )
    args = parser.parse_args()

    conn = get_connection()
    init_schema(conn)
    seed_reference_data(conn)

    if args.task_id:
        results = collect_task(conn, args.task_id)
    else:
        results = collect_all(conn)

    for item in results:
        if item["status"] == "ok":
            print(
                f"[OK] {item['route']} / {item['carrier']}: "
                f"{item['transport_price']:.2f} ₽, "
                f"{item['delivery_days']} дн."
            )
        else:
            print(
                f"[ERR] {item['route']} / {item['carrier']}: "
                f"{item['error_message']}"
            )

    print("\n--- quotes en BDD ---")
    for row in load_all_quotes(conn):
        price = row["transport_price"]
        price_txt = f"{price:.2f}" if price is not None else "—"
        print(
            f"{row['departure']} → {row['destination']} | "
            f"{row['carrier_code']}: {price_txt} ₽ | "
            f"{row['delivery_days']} дн. | {row['status']}"
        )

    conn.close()


if __name__ == "__main__":
    main()
