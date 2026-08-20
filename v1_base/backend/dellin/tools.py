"""OpenAI tools — Dellin transport de base uniquement."""

from __future__ import annotations

import json
from typing import Any

from dellin.calculator import (
    calculate_shipping,
    format_calculation_result,
)
from dellin.lookup import DellinLookupError

DELLIN_CALCULATOR_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculate_dellin_shipping",
        "description": (
            "Расчёт Dellin: только транспорт база "
            "(Межтерминальная перевозка), тариф Стандарт, "
            "без упаковки и доп. услуг. Города: "
            "Санкт-Петербург, Москва, Омск."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "departure_city": {
                    "type": "string",
                    "description": "Город отправления",
                },
                "destination_city": {
                    "type": "string",
                    "description": "Город назначения",
                },
                "volume_m3": {
                    "type": "number",
                    "description": "Объём м³ (по умолчанию 1)",
                },
                "weight_kg": {
                    "type": "number",
                    "description": "Вес кг (по умолчанию 1)",
                },
                "places": {
                    "type": "integer",
                    "description": "Мест (только 1)",
                    "default": 1,
                },
            },
            "required": [
                "departure_city",
                "destination_city",
                "volume_m3",
                "weight_kg",
                "places",
            ],
        },
    },
}

OPENAI_TOOLS = [DELLIN_CALCULATOR_TOOL]


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Exécute un tool Dellin et renvoie du JSON pour le LLM."""
    if isinstance(arguments, str):
        payload = json.loads(arguments)
    else:
        payload = arguments

    if name == "calculate_dellin_shipping":
        try:
            result = calculate_shipping(**payload)
        except DellinLookupError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"error": f"Erreur calculateur Dellin: {exc}"},
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "carrier": "Dellin",
                "formatted": format_calculation_result(result),
                "result": result,
            },
            ensure_ascii=False,
        )

    raise ValueError(f"Unknown tool: {name}")
