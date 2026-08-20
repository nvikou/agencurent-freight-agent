"""OpenAI tools — ПЭК transport de base uniquement."""

from __future__ import annotations

import json
from typing import Any

from pek.calculator import (
    PekCalculatorError,
    calculate_shipping,
    format_calculation_result,
)

PEK_CALCULATOR_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculate_pek_shipping",
        "description": (
            "Расчёт ПЭК: только транспорт база (Автоперевозка), "
            "тариф Стандарт, без упаковки, документов и страховки. "
            "Города: Санкт-Петербург, Москва, Омск."
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

OPENAI_TOOLS = [PEK_CALCULATOR_TOOL]


def execute_tool(name: str, arguments: str | dict[str, Any]) -> str:
    """Exécute un tool ПЭК et renvoie du JSON pour le LLM."""
    if isinstance(arguments, str):
        payload = json.loads(arguments)
    else:
        payload = arguments

    if name == "calculate_pek_shipping":
        try:
            result = calculate_shipping(**payload)
        except PekCalculatorError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"error": f"Erreur API ПЭК: {exc}"},
                ensure_ascii=False,
            )
        clean = {
            key: value
            for key, value in result.items()
            if key != "raw"
        }
        return json.dumps(
            {
                "carrier": "ПЭК",
                "formatted": format_calculation_result(result),
                "result": clean,
            },
            ensure_ascii=False,
        )

    raise ValueError(f"Unknown tool: {name}")
