"""Client for the Baikal Service shipping calculator API."""

from __future__ import annotations

import re
import time
from datetime import date
from typing import Any
from urllib.parse import urlencode

import requests

BASE_URL = "https://request.baikalsr.ru"
CALCULATOR_URL = (
    f"{BASE_URL}/calculator/"
    "?guid=3075d257-f4e2-2f25-ab16-21cc8a557d57"
)

PACKAGING_SERVICES = {
    "Жесткая упаковка": 3228,
    "Паллетный борт (индивидуальный)": 2797,
    "Паллетирование": 19,
    "Пузырчатая пленка": 21,
    "Мешки": 1,
}

DOCUMENT_SERVICES = {
    "Требуется перевозка сопроводительных документов": 2910,
    "Требуется возврат документов": 16,
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Referer": CALCULATOR_URL,
    "Origin": BASE_URL,
}

API_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


class BaikalCalculatorError(Exception):
    """Raised when the Baikal calculator API returns an error."""


def _extract_csrf_token(html: str) -> str:
    match = re.search(
        r'<meta name="csrf-token" content="([^"]+)"',
        html,
    )
    if not match:
        raise BaikalCalculatorError("CSRF token not found on calculator page")
    return match.group(1)


def _build_service_objects(service_ids: list[int]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(service_id),
            "fields": [{"id": str(service_id), "value": "1"}],
        }
        for service_id in service_ids
    ]


def _encode_nested(data: dict[str, Any], prefix: str = "") -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for key, value in data.items():
        full_key = f"{prefix}[{key}]" if prefix else str(key)
        if isinstance(value, dict):
            pairs.extend(_encode_nested(value, full_key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                item_key = f"{full_key}[{index}]"
                if isinstance(item, dict):
                    pairs.extend(_encode_nested(item, item_key))
                else:
                    pairs.append((item_key, str(item)))
        else:
            pairs.append((full_key, "" if value is None else str(value)))
    return pairs


class BaikalCalculatorClient:
    """HTTP client for Baikal calculator endpoints."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._csrf_token: str | None = None

    def _ensure_session(self) -> str:
        if self._csrf_token:
            return self._csrf_token

        try:
            self.session.get(
                "https://www.baikalsr.ru/",
                timeout=30,
                headers={"Referer": "https://www.baikalsr.ru/"},
            )
            response = self.session.get(CALCULATOR_URL, timeout=30)
            response.raise_for_status()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 403:
                raise BaikalCalculatorError(
                    "Baikal: доступ запрещён (403). "
                    "Часто на Google Colab — IP датацентра блокируют. "
                    "Запустите локально или сравните Dellin + ПЭК."
                ) from exc
            raise BaikalCalculatorError(f"Erreur HTTP Baikal: {exc}") from exc
        except requests.RequestException as exc:
            raise BaikalCalculatorError(
                f"Erreur réseau Baikal: {exc}"
            ) from exc

        self._csrf_token = _extract_csrf_token(response.text)
        return self._csrf_token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        token = self._ensure_session()
        headers = {"X-CSRF-Token": token, **API_HEADERS}
        if data is not None:
            headers["Content-Type"] = (
                "application/x-www-form-urlencoded; charset=UTF-8"
            )
            payload = urlencode(_encode_nested(data))
        else:
            payload = None

        response = self.session.request(
            method,
            f"{BASE_URL}{path}",
            params=params,
            data=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def search_city(self, query: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/json/fias-cities",
            params={"text": query},
        )

    def resolve_city(self, query: str) -> dict[str, Any]:
        cities = self.search_city(query)
        if not cities:
            raise BaikalCalculatorError(f"City not found: {query}")

        normalized = query.strip().lower()
        for city in cities:
            if city.get("title", "").strip().lower() == normalized:
                return city

        for city in cities:
            if city.get("name", "").strip().lower() in normalized:
                return city

        return cities[0]

    def get_default_terminal(self, city_guid: str) -> int:
        data = self._request(
            "POST",
            "/json/fias-station-data",
            data={"guid": city_guid},
        )
        terminals = data["affiliate"]["terminals"]
        base_terminal = next(
            (terminal for terminal in terminals if terminal.get("base") == 1),
            terminals[0],
        )
        return int(base_terminal["id"])

    def calculate(
        self,
        *,
        departure_city: str,
        destination_city: str,
        volume_m3: float,
        weight_kg: float,
        places: int,
        cargo_type: str = "мебель",
        packaging: list[str] | None = None,
        documents: list[str] | None = None,
        departure_date: date | None = None,
    ) -> dict[str, Any]:
        departure = self.resolve_city(departure_city)
        destination = self.resolve_city(destination_city)
        departure_terminal = self.get_default_terminal(departure["guid"])
        destination_terminal = self.get_default_terminal(destination["guid"])

        packaging = packaging or []
        documents = documents or []
        service_ids = [
            PACKAGING_SERVICES[name]
            for name in packaging
            if name in PACKAGING_SERVICES
        ]
        service_ids.extend(
            DOCUMENT_SERVICES[name]
            for name in documents
            if name in DOCUMENT_SERVICES
        )

        calc_date = departure_date or date.today()
        request_id = f"sncy_{int(time.time() * 1000)}_{int(time.time() * 1000)}"
        payload = {
            "departure": {
                "cityguid": departure["guid"],
                "terminal": departure_terminal,
                "date": f"{calc_date.isoformat()}T00:00:00",
            },
            "destination": {
                "cityguid": destination["guid"],
                "terminal": destination_terminal,
            },
            "transport": ["auto"],
            "cargo": {
                "summarycargo": {
                    "length": "",
                    "width": "",
                    "height": "",
                    "maxweight": "",
                    "volume": volume_m3,
                    "weight": weight_kg,
                    "units": places,
                    "type": cargo_type,
                    "oversized": 0,
                    "estimatedcost": "",
                    "servicesobject": _build_service_objects(service_ids),
                }
            },
            "id": request_id,
        }

        raw = self._request("POST", "/json/calculator", data=payload)
        if raw.get("error"):
            messages = [
                item.get("description", str(item))
                for item in raw["error"]
            ]
            raise BaikalCalculatorError("; ".join(messages))
        return parse_calculation_result(raw)


def parse_calculation_result(raw: dict[str, Any]) -> dict[str, Any]:
    auto = raw["transport"]["auto"]
    departure_title = auto["departure"]["title"]
    destination_title = auto["destination"]["title"]
    route = f"{departure_title} — {destination_title}"

    cargo_services = [
        {
            "name": service["name"],
            "cost": service["cost"],
        }
        for service in auto["cargo"]["services"]
        if service.get("cost")
    ]
    destination_services = [
        {
            "name": service["name"],
            "cost": service["cost"],
        }
        for service in auto["destination"].get("services", [])
        if service.get("cost")
    ]

    cost_breakdown = cargo_services + destination_services
    transit_days = auto["transit"]["int"] if auto.get("transit") else None
    transit_label = auto["transit"]["day24"] if auto.get("transit") else ""

    return {
        "route": route,
        "delivery_days": transit_days,
        "delivery_term": (
            f"{transit_days} {transit_label}" if transit_days else None
        ),
        "cargo_description": auto["cargo"]["description"],
        "cost_breakdown": cost_breakdown,
        "total_cost": auto["total"],
        "currency": "RUB",
        "raw": raw,
    }


def format_calculation_result(result: dict[str, Any]) -> str:
    lines = [
        result["route"],
        f"Срок доставки {result['delivery_term']}",
        f"{result['total_cost']:.2f} ₽",
        "",
        "### Параметры груза",
        f"* {result['cargo_description']}",
        "",
        "### Расчет стоимости",
    ]
    for item in result["cost_breakdown"]:
        lines.append(f"* **{item['name']}**: {item['cost']:.2f} ₽")

    lines.extend(
        [
            "",
            f"Срок доставки {result['delivery_term']}",
            "",
            "### Общая стоимость",
            f"**{result['total_cost']:.2f} ₽**",
        ]
    )
    return "\n".join(lines)


def calculate_shipping(
    departure_city: str,
    destination_city: str,
    volume_m3: float = 1,
    weight_kg: float = 1,
    places: int = 1,
) -> dict[str, Any]:
    """Baikal transport de base, sans упаковка ni documents."""
    client = BaikalCalculatorClient()
    return client.calculate(
        departure_city=departure_city,
        destination_city=destination_city,
        volume_m3=volume_m3,
        weight_kg=weight_kg,
        places=places,
        cargo_type="мебель",
        packaging=[],
        documents=[],
    )
