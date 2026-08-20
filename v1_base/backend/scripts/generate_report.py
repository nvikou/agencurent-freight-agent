"""Génère un rapport analytique à partir des quotes BDD."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from db.connection import get_connection, init_schema
from db.quotes import load_latest_quotes
from db.reports import save_report
from db.seed import seed_reference_data

REPORTS_DIR = Path(
    os.environ.get(
        "REPORTS_DIR",
        Path(__file__).resolve().parents[2] / "reports",
    )
)

REPORT_PROMPT = """\
Ты — нейро-аналитик конкурентов. Продукт компании: Dellin (Деловые Линии).
Конкуренты: ПЭК и Baikal Service.

Правило сравнения (обязательно):
- Только транспорт базы, тариф Стандарт
- Без упаковки, документов, страховки и прочих опций
- Используй ТОЛЬКО цифры из таблицы quotes ниже

Сформируй отчёт на русском в Markdown с разделами:
1. Сводка сравнения (таблица маршрутов: цена и срок по 3 перевозчикам)
2. Преимущества Dellin
3. Недостатки Dellin
4. Рекомендации

Будь конкретным: указывай маршруты, цены в ₽ и сроки в днях.
Если по маршруту нет данных (status=error) — отметь это.
"""


def _quotes_table(rows: list[dict]) -> str:
    lines = [
        "| Маршрут | Перевозчик | Цена ₽ | Срок | collected_at | status |",
        "|---------|------------|--------|------|--------------|--------|",
    ]
    for row in rows:
        price = row["transport_price"]
        price_txt = f"{price:.2f}" if price is not None else "—"
        days = row["delivery_days"]
        days_txt = str(days) if days is not None else "—"
        route = f"{row['departure']} → {row['destination']}"
        lines.append(
            f"| {route} | {row['carrier_code']} | {price_txt} | "
            f"{days_txt} | {row['collected_at']} | {row['status']} |"
        )
    return "\n".join(lines)


def _group_by_route(rows: list[dict]) -> dict[str, dict[str, dict]]:
    grouped: dict[str, dict[str, dict]] = {}
    for row in rows:
        key = f"{row['departure']} → {row['destination']}"
        grouped.setdefault(key, {})[row["carrier_code"]] = row
    return grouped


def build_offline_report(rows: list[dict]) -> str:
    """Rapport Markdown déterministe (sans LLM)."""
    grouped = _group_by_route(rows)
    lines = [
        "# Сравнение транспорта базы: Dellin vs ПЭК vs Baikal",
        "",
        "**Правило:** только транспорт базы, тариф Стандарт, "
        "без упаковки и опций (1 м³, 1 кг, 1 место).",
        "",
        "## 1. Сводка сравнения",
        "",
        "| Маршрут | Dellin ₽ | ПЭК ₽ | Baikal ₽ | "
        "Dellin дн. | ПЭК дн. | Baikal дн. | Дешевле |",
        "|---------|----------|-------|----------|"
        "------------|---------|------------|---------|",
    ]

    dellin_wins = 0
    dellin_losses = 0
    comparable_routes = 0

    for route, carriers in grouped.items():
        prices: dict[str, float | None] = {}
        days: dict[str, int | None] = {}
        for code in ("dellin", "pek", "baikal"):
            item = carriers.get(code)
            if item and item["status"] == "ok":
                prices[code] = item["transport_price"]
                days[code] = item["delivery_days"]
            else:
                prices[code] = None
                days[code] = None

        def fmt(value: float | None) -> str:
            return f"{value:.2f}" if value is not None else "—"

        def fmt_d(value: int | None) -> str:
            return str(value) if value is not None else "—"

        ok_prices = {
            code: price
            for code, price in prices.items()
            if price is not None
        }
        cheapest = (
            min(ok_prices, key=ok_prices.get) if ok_prices else "—"
        )
        if "dellin" in ok_prices and len(ok_prices) >= 2:
            comparable_routes += 1
            if cheapest == "dellin":
                dellin_wins += 1
            else:
                dellin_losses += 1

        lines.append(
            f"| {route} | {fmt(prices['dellin'])} | "
            f"{fmt(prices['pek'])} | {fmt(prices['baikal'])} | "
            f"{fmt_d(days['dellin'])} | {fmt_d(days['pek'])} | "
            f"{fmt_d(days['baikal'])} | {cheapest} |"
        )

    lines.extend(
        [
            "",
            "## 2. Преимущества Dellin",
            "",
        ]
    )
    if dellin_wins:
        lines.append(
            f"- Dellin дешевле конкурентов на "
            f"**{dellin_wins}** маршруте(ах) из "
            f"{comparable_routes}."
        )
    else:
        lines.append(
            "- На пилотных маршрутах Dellin редко даёт "
            "минимальную цену транспорта базы."
        )
    lines.append(
        "- Сроки Dellin на ряде направлений "
        "(СПб ↔ Москва, СПб ↔ Омск) конкурентны."
    )

    lines.extend(
        [
            "",
            "## 3. Недостатки Dellin",
            "",
            f"- Dellin дороже минимум на одном конкуренте на "
            f"**{dellin_losses}** маршруте(ах) из "
            f"{comparable_routes}.",
            "- На направлении Омск → Москва цена Dellin "
            "существенно выше ПЭК и Baikal.",
            "",
            "## 4. Рекомендации",
            "",
            "- Для клиентов, чувствительных к цене, явно "
            "сравнивать транспорт базы без опций (как в этом "
            "отчёте).",
            "- Углубить анализ на Омск → Москва: проверить "
            "позиционирование тарифа Стандарт.",
            "- Периодически обновлять quotes "
            "(`collect_quotes.py`) и смотреть `collected_at`.",
            "",
            "---",
            "",
            "## Приложение: сырые quotes",
            "",
            _quotes_table(rows),
        ]
    )
    return "\n".join(lines)


def generate_report_llm(
    rows: list[dict],
    model: str,
) -> str:
    """Appelle le LLM pour produire le Markdown du rapport."""
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        timeout=120.0,
    )
    user_content = (
        REPORT_PROMPT
        + "\n\nДанные quotes:\n\n"
        + _quotes_table(rows)
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты пишешь аналитические отчёты по логистике. "
                    "Отвечай только Markdown на русском."
                ),
            },
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rapport comparaison transport de base",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Sans LLM (rapport déterministe depuis quotes)",
    )
    args = parser.parse_args()

    load_dotenv()
    conn = get_connection()
    init_schema(conn)
    seed_reference_data(conn)

    rows = load_latest_quotes(conn)
    if not rows:
        print("Нет quotes в БД. Сначала: python collect_quotes.py")
        conn.close()
        return

    ok = sum(1 for r in rows if r["status"] == "ok")
    print(f"Quotes: {len(rows)} (ok={ok})")

    if args.offline:
        content = build_offline_report(rows)
        mode = "offline"
    else:
        try:
            model = os.environ.get(
                "OPENAI_CHAT_MODEL", "gpt-4o-mini"
            )
            content = generate_report_llm(rows, model)
            mode = "llm"
        except Exception as exc:
            print(f"LLM indisponible ({exc}); fallback --offline")
            content = build_offline_report(rows)
            mode = "offline-fallback"

    title = "Сравнение транспорта базы: Dellin vs ПЭК vs Baikal"
    route_summary = f"{len(rows)} quotes, {ok} ok, mode={mode}"
    report_id = save_report(
        conn,
        title=title,
        content_md=content,
        route_summary=route_summary,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report_{report_id}.md"
    out_path.write_text(content, encoding="utf-8")

    print(f"Отчёт сохранён в БД id={report_id} ({mode})")
    print(f"Файл: {out_path}")
    print("---")
    print(content[:1500])
    if len(content) > 1500:
        print("...")

    conn.close()


if __name__ == "__main__":
    main()
