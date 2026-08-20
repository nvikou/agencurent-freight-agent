"""Extraction du prix transport de base (sans options)."""

from __future__ import annotations

from typing import Any

PEK_TRANSPORT_LINE = "Автоперевозка"
INTER_TERMINAL_PREFIX = "Межтерминальная перевозка"


def extract_base_transport_price(
    carrier_code: str,
    result: dict[str, Any],
) -> float:
    """
    Retourne uniquement la ligne transport de base.

    ПЭК — «Автоперевозка» (priceBase).
    Dellin / Baikal — «Межтерминальная перевозка…».
    """
    code = carrier_code.lower()
    breakdown = result.get("cost_breakdown") or []

    if code == "pek":
        for item in breakdown:
            if item.get("name") == PEK_TRANSPORT_LINE:
                return float(item["cost"])
        raise ValueError(
            f"Линия «{PEK_TRANSPORT_LINE}» не найдена в cost_breakdown"
        )

    if code in ("dellin", "baikal"):
        for item in breakdown:
            name = item.get("name", "")
            if name.startswith(INTER_TERMINAL_PREFIX):
                return float(item["cost"])
        raise ValueError(
            f"Линия «{INTER_TERMINAL_PREFIX}» не найдена в cost_breakdown"
        )

    raise ValueError(f"Неизвестный перевозчик: {carrier_code}")
