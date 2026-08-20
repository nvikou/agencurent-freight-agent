"""OpenAI tools — Baikal transport de base uniquement."""

from __future__ import annotations

import json
from typing import Any

from baikal.calculator import (
    BaikalCalculatorError,
    calculate_shipping,
    format_calculation_result,
)

BAIKAL_CALCULATOR_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculate_baikal_shipping",
        "description": (
            "Расчёт Baikal: только транспорт база "
            "(Межтерминальная перевозка), без упаковки и документов. "
            "Города: Санкт-Петербург, Москва, Омск."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "departure_city": {
                    "type": "string",
                    "description": (
                        "Город отправления, напр. 'Санкт-Петербург'"
                    ),
                },
                "destination_city": {
                    "type": "string",
                    "description": "Город назначения, напр. 'Москва'",
                },
                "volume_m3": {
                    "type": "number",
                    "description": "Объём м³",
                },
                "weight_kg": {
                    "type": "number",
                    "description": "Вес кг",
                },
                "places": {
                    "type": "integer",
                    "description": "Количество мест",
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

OPENAI_TOOLS = [BAIKAL_CALCULATOR_TOOL]


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Exécute un tool Baikal et renvoie du JSON pour le LLM."""
    if isinstance(arguments, str):
        payload = json.loads(arguments)
    else:
        payload = arguments

    if name == "calculate_baikal_shipping":
        try:
            result = calculate_shipping(**payload)
        except BaikalCalculatorError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"error": f"Erreur API Baikal: {exc}"},
                ensure_ascii=False,
            )
        clean = {
            key: value
            for key, value in result.items()
            if key != "raw"
        }
        return json.dumps(
            {
                "carrier": "Baikal",
                "formatted": format_calculation_result(result),
                "result": clean,
            },
            ensure_ascii=False,
        )

    raise ValueError(f"Unknown tool: {name}")
