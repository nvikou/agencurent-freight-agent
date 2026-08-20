"""Calculateur Dellin — transport de base uniquement (Стандарт)."""

from __future__ import annotations

from typing import Any

from dellin.lookup import (
    DellinLookupError,
    default_place_count,
    find_base_price,
    find_direction,
    find_volume_class,
    find_weight_class,
)
from dellin.resources import TYPES

TARIFF_TYPES = {t["type"]: t["id_type"] for t in TYPES}


def _format_rub(amount: float) -> str:
    if abs(amount - round(amount)) < 0.01:
        formatted = f"{round(amount):,.0f}".replace(",", " ")
        return f"{formatted} ₽"
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} ₽"


def _days_label(days: int | None) -> str:
    if days is None:
        return ""
    if days == 1:
        return "1 день"
    if 2 <= days <= 4:
        return f"{days} дня"
    return f"{days} дней"


def calculate_shipping(
    departure_city: str,
    destination_city: str,
    volume_m3: float = 1,
    weight_kg: float = 1,
    places: int = 1,
) -> dict[str, Any]:
    """Devis transport de base (Межтерминальная перевозка), Стандарт."""
    if places != 1:
        raise DellinLookupError(
            "Seul kolichestvo_mest=1 est supporté pour le moment"
        )

    direction = find_direction(departure_city, destination_city)
    weight_cls = find_weight_class(weight_kg)
    volume_cls = find_volume_class(volume_m3)
    place = default_place_count()
    id_type = TARIFF_TYPES["Стандарт"]

    base = find_base_price(
        id_direction=direction["id_direction"],
        id_classification_poids=weight_cls["id_classification_poids"],
        id_classification_volume=volume_cls["id_classification_volume"],
        id_kolichestvo_mest=place["id_kolichestvo_mest"],
        id_methode=1,
        id_type=id_type,
    )

    breakdown: list[dict[str, Any]] = [
        {
            "name": (
                f"Межтерминальная перевозка "
                f"{direction['ville_expediteur']} - "
                f"{direction['ville_arrivee']}"
            ),
            "cost": float(base["prix"]),
        }
    ]

    total = sum(item["cost"] for item in breakdown)
    delivery_days = direction.get("delai_jours")

    return {
        "departure_city": direction["ville_expediteur"],
        "destination_city": direction["ville_arrivee"],
        "volume_m3": volume_m3,
        "weight_kg": weight_kg,
        "places": places,
        "tariff": "Стандарт",
        "delivery_days": delivery_days,
        "delivery_term": _days_label(delivery_days),
        "cost_breakdown": breakdown,
        "total_cost": total,
        "currency": "RUB",
        "weight_class": weight_cls["label"],
        "volume_class": volume_cls["label"],
    }


def format_calculation_result(result: dict[str, Any]) -> str:
    lines = [
        "### Маршрут и груз (транспорт база)",
        f"* **Откуда**: {result['departure_city']}",
        f"* **Куда**: {result['destination_city']}",
        (
            f"* **Груз**: {result['volume_m3']} м³, "
            f"{result['weight_kg']} кг, {result['places']} место"
        ),
        f"* **Тариф**: {result['tariff']}",
        "",
        "---",
        "",
        "### Стоимость (без опций)",
        "",
    ]
    for item in result["cost_breakdown"]:
        lines.append(
            f"* **{item['name']}**: {_format_rub(item['cost'])}"
        )

    lines.extend(
        [
            "",
            f"* **Сроки**: {result['delivery_term']}",
            "",
            "### Транспорт база:",
            f"**{_format_rub(result['total_cost'])}**",
        ]
    )
    return "\n".join(lines)
