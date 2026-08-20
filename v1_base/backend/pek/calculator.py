"""Client for the PEK (ПЭК) shipping calculator JSON-RPC API."""

from __future__ import annotations

import random
import re
import time
from datetime import date
from typing import Any, Literal

import requests

BASE_URL = "https://pecom.ru"
CALCULATOR_URL = f"{BASE_URL}/services-are/shipping-request/"
CONFIG_URL = f"{BASE_URL}/werkuwehbcweiufyw/"
AJAX_URL = f"{BASE_URL}/ajax/"

PACKAGING_SERVICES = {
    "Защитная транспортировочная упаковка": (
        "7129460a-17af-4350-9839-a3de5898901a"
    ),
    "Палетирование": "ce2f31ee-37b2-11e6-b11a-00155d668909",
}

DOCUMENT_SERVICES = {
    "Организация перевозки сопроводительных документов": (
        "4f5dc945-ab25-11e4-bbf2-80c16e644d5d"
    ),
    "Возврат документов": "76a7dd5a-a154-4473-9d82-3e3f330fbceb",
}

INSURANCE_SERVICES = {
    "Страхование груза": "6b1a7738-07a2-11f0-b8a7-00155d30f534",
}

TARIFF_LABELS = {
    "Стандарт": "standard",
    "Экспресс-перевозка": "express",
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": CALCULATOR_URL,
    "Origin": BASE_URL,
    "Content-Type": "application/json",
}

_CITY_GUIDS: dict[str, str] = {
    "санкт-петербург": "de13ce1d-fcc5-4cd8-8543-a1ae3f1f5084",
    "спб": "de13ce1d-fcc5-4cd8-8543-a1ae3f1f5084",
    "москва": "8d94504d-2dca-481e-a4cf-39d353be465a",
    "омск": "a6f0e8b0-0d0a-11e5-80ce-00155d713b38",
}

_CITY_AFFILIATES: dict[str, dict[str, Any]] = {
    "санкт-петербург": {
        "city": "Санкт-Петербург",
        "geo": {"lat": "59.942818", "lng": "30.440896"},
        "affiliate": {
            "id": "c007f9bb-5a96-11e4-94e4-00155d9d920f",
            "name": "Санкт-Петербург",
            "address": (
                "Россия, Санкт-Петербург, улица Якорная, 17, литер Ш"
            ),
            "geo": {"lat": "59.942818", "lng": "30.440896"},
        },
    },
    "москва": {
        "city": "Москва",
        "geo": {"lat": "55.534204", "lng": "37.578127"},
        "affiliate": {
            "id": "4749f8b8-2a2a-11e9-80ce-00155d713b38",
            "name": "Москва Бутово",
            "address": (
                "Россия, Москва, 2-я Мелитопольская улица, 12Ас1"
            ),
            "geo": {"lat": "55.534204", "lng": "37.578127"},
        },
    },
    "омск": {
        "city": "Омск",
        "geo": {"lat": "54.987123", "lng": "73.48155"},
        "affiliate": {
            "id": "b3b35566-5a96-11e4-94e4-00155d9d920f",
            "name": "Омск",
            "address": (
                "Россия, Омск, Космический пр-т, 109 к1"
            ),
            "geo": {"lat": "54.987123", "lng": "73.48155"},
        },
    },
}


class PekCalculatorError(Exception):
    """Raised when the PEK calculator API returns an error."""


def _normalize_city_query(query: str) -> str:
    text = query.strip().lower()
    text = re.sub(r"\s+г\.?\s*$", "", text)
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    return text.strip()


def _match_city_key(query: str) -> str:
    normalized = _normalize_city_query(query)
    if normalized in _CITY_AFFILIATES:
        return normalized

    for key in _CITY_AFFILIATES:
        if key in normalized or normalized in key:
            return key

    raise PekCalculatorError(f"City not found: {query}")


def _match_city_guid(query: str) -> tuple[str, str]:
    key = _match_city_key(query)
    return _CITY_GUIDS.get(key, ""), _CITY_AFFILIATES[key]["city"]


def _price_value(price: dict[str, Any] | float | int | None) -> float:
    if price is None:
        return 0.0
    if isinstance(price, (int, float)):
        return float(price)
    return float(price.get("value", 0) or 0)


def _format_rub(amount: float) -> str:
    formatted = f"{amount:,.1f}".replace(",", " ").replace(".", ",")
    return f"{formatted} ₽"


def _days_label(count_days: list[int] | int | None) -> str:
    if count_days is None:
        return ""
    days = count_days[0] if isinstance(count_days, list) else count_days
    if days == 1:
        return "1 день"
    if 2 <= days <= 4:
        return f"{days} дня"
    return f"{days} дней"


class PekCalculatorClient:
    """HTTP client for PEK calculator JSON-RPC endpoints."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": DEFAULT_HEADERS["User-Agent"],
                "Accept": DEFAULT_HEADERS["Accept"],
                "Accept-Language": DEFAULT_HEADERS["Accept-Language"],
                "Referer": CALCULATOR_URL,
                "Origin": BASE_URL,
            }
        )
        self._sessid: str | None = None

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        attempts: int = 5,
    ) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self.session.request(
                    method,
                    url,
                    json=json_body,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(1.5 * (attempt + 1))
        raise PekCalculatorError(
            f"Network error contacting PEK API: {last_error}"
        ) from last_error

    def _ensure_sessid(self) -> str:
        if self._sessid:
            return self._sessid

        self._request_with_retry("GET", CALCULATOR_URL)
        response = self._request_with_retry("GET", CONFIG_URL)
        match = re.search(
            r"bitrix_sessid'\s*:\s*'([^']+)'",
            response.text,
        )
        if not match:
            raise PekCalculatorError("Session id not found in PEK config")
        self._sessid = match.group(1)
        return self._sessid

    def _rpc(self, method: str, params: Any) -> dict[str, Any]:
        body = {
            "id": random.randint(10**12, 10**13),
            "jsonrpc": "2.0",
            "method": method,
            "sessid": self._ensure_sessid(),
            "params": params,
        }
        response = self._request_with_retry(
            "POST",
            AJAX_URL,
            json_body=body,
            headers={"Content-Type": "application/json"},
        )
        payload = response.json()
        if "error" in payload:
            message = payload["error"].get("message", str(payload["error"]))
            raise PekCalculatorError(message)
        return payload

    def _get_affiliate_direction(self, city_query: str) -> dict[str, Any]:
        city_key = _match_city_key(city_query)
        city_data = _CITY_AFFILIATES[city_key]
        affiliate = city_data["affiliate"]
        return {
            "city": city_data["city"],
            "country": "Россия",
            "geo": city_data.get("geo", {}),
            "type": "affiliate",
            "address": f"Россия, {city_data['city']}",
            "addressParts": {
                "area": "",
                "country": "",
                "country_code": "",
                "kind": "",
                "house": "",
                "district": "",
                "locality": "",
                "postal_code": "",
                "province": "",
                "street": "",
            },
            "affiliate": dict(affiliate),
            "affiliateChangedManually": False,
            "isPvz": False,
            "comment": "",
            "mapAddressSelected": False,
        }

    def _build_calculate_params(
        self,
        *,
        departure: dict[str, Any],
        destination: dict[str, Any],
        volume_m3: float,
        weight_kg: float,
        places: int,
        cargo_type: str,
        declared_value: float,
        services: dict[str, Any] | None,
        plan_date: date,
    ) -> dict[str, Any]:
        return {
            "id": 0,
            "lid": "ZfFkKSV",
            "new": 1,
            "name": "",
            "activeLid": "ZfFkKSV",
            "ocrGuid": "45b4e548-6825-4f20-b973-64aba92a3a22",
            "cargoGuid": "",
            "cargoIndex": "",
            "insuranceInit": True,
            "ocrForLoadCheckedServices": {},
            "actionType": 1,
            "actionTypeStr": "",
            "step1": {
                "cargo": {
                    "tab": "cargo-tab1",
                    "tab1": {
                        "total_weight": weight_kg,
                        "total_volume": volume_m3,
                        "most_long": 0.1,
                        "places": places,
                    },
                    "tab2": {"items": []},
                    "total_weight": weight_kg,
                    "total_volume": volume_m3,
                    "total_place_count": places,
                    "price": declared_value,
                    "insure": 1,
                    "insure_price": 0,
                    "insurance_organization": 0,
                    "insurance_organization_price": 0,
                    "special": {
                        "type": "",
                        "cargoName": cargo_type,
                        "liquid": 0,
                        "fragile": 0,
                    },
                    "isOversized": 0,
                    "isAir": 0,
                    "isExpress": 0,
                    "planDate": plan_date.strftime("%d.%m.%Y"),
                    "planTime": "до 15:00",
                    "avisation": {"date": "", "time": ""},
                    "planDateChangedDirectly": 0,
                    "priceChangedDirectly": 0,
                    "orderNumber": "",
                },
                "direction": {
                    "from": departure,
                    "to": destination,
                },
                "calculationCurrencyCode": "643",
                "calculationCurrencyGuid": (
                    "6bc73ea8-a8b6-11dc-adc5-0017085a0478"
                ),
                "insurancePayerBranchGuid": "",
                "orderKind": "",
                "services": services or {},
                "customerTransportation": {
                    "owner": [],
                    "counterparts": [],
                    "roles": {
                        "sender": {
                            "uid": 1,
                            "name": "Отправитель",
                            "code": "sender",
                            "value": False,
                        },
                        "recipient": {
                            "uid": 2,
                            "name": "Получатель",
                            "code": "recipient",
                            "value": False,
                        },
                        "thirdPart": {
                            "uid": 3,
                            "name": "Плательщик",
                            "code": "thirdPart",
                            "value": False,
                        },
                        "notParticipant": {
                            "uid": 4,
                            "name": "Не участник перевозки",
                            "code": "notParticipant",
                            "value": False,
                        },
                    },
                    "value": "",
                },
                "counterpartClientCard": "",
            },
            "step2": {
                "agentType": "agent-fiz",
                "first_name": "",
                "last_name": "",
                "second_name": "",
                "document": {
                    "type": "type1",
                    "name": "",
                    "series": "",
                    "number": "",
                    "date": "",
                    "guid": "",
                },
                "email": "",
                "phone": "",
                "phone_country": "ru",
                "notify_email": 0,
                "notify_sms": 0,
                "poa_required": 0,
            },
            "step3": {
                "agentType": "agent-fiz",
                "first_name": "",
                "last_name": "",
                "second_name": "",
                "document": {
                    "type": "",
                    "name": "",
                    "series": "",
                    "number": "",
                    "date": "",
                    "guid": "",
                },
                "email": "",
                "phone": "",
                "phone_country": "",
                "notify_email": 0,
                "notify_sms": 0,
                "poa_required": 0,
            },
            "step4": {
                "tab": "pay-tab1",
                "one": {"payer": {"subject": "sender"}, "branch": {"subject": ""}},
                "many": {},
                "applier": {"subject": "sender"},
                "thirdPerson": {"agentData": {}},
                "comment": "",
                "sendDocs": 0,
                "email": "",
                "agree": 0,
                "notifyClientByIntakeCargo": {
                    "notifyMailByIntakeCargo": False,
                    "notifyMessengerByIntakeCargo": False,
                    "notifyManagerCallByIntakeCargo": False,
                },
                "nal_plat": 0,
                "isForwardersOrder": False,
            },
            "step5": {
                "agentType": "agent-fiz",
                "first_name": "",
                "last_name": "",
                "second_name": "",
                "document": {},
                "email": "",
                "phone": "",
                "phone_country": "",
                "notify_email": 0,
                "notify_sms": 0,
                "poa_required": 0,
                "counterpartClientCard": "",
            },
            "historyParts": {"intakeTimeInterval": ""},
            "multi": [],
            "action": "calculate",
        }

    @staticmethod
    def _selected_guids(
        packaging: list[str],
        documents: list[str],
        insurance: list[str],
    ) -> set[str]:
        guids: set[str] = set()
        for name in packaging:
            if name in PACKAGING_SERVICES:
                guids.add(PACKAGING_SERVICES[name])
        for name in documents:
            if name in DOCUMENT_SERVICES:
                guids.add(DOCUMENT_SERVICES[name])
        for name in insurance:
            if name in INSURANCE_SERVICES:
                guids.add(INSURANCE_SERVICES[name])
        return guids

    @staticmethod
    def _apply_service_selection(
        service_list: dict[str, Any],
        selected_guids: set[str],
    ) -> dict[str, Any]:
        services: dict[str, list[dict[str, Any]]] = {}
        for category in (
            "packingServices",
            "documentServices",
            "insuranceServices",
        ):
            items = service_list.get(category, [])
            if not items:
                continue
            updated_items = []
            for item in items:
                guid = item.get("guid")
                if guid not in selected_guids:
                    continue
                copied = dict(item)
                copied["isChecked"] = True
                updated_items.append(copied)
            if updated_items:
                services[category] = updated_items
        return services

    def calculate(
        self,
        *,
        departure_city: str,
        destination_city: str,
        volume_m3: float,
        weight_kg: float,
        places: int,
        cargo_type: str = "мебель",
        declared_value: float = 100,
        packaging: list[str] | None = None,
        documents: list[str] | None = None,
        insurance: list[str] | None = None,
        tariff: Literal["Стандарт", "Экспресс-перевозка"] = "Стандарт",
        plan_date: date | None = None,
    ) -> dict[str, Any]:
        # v1_base: transport de base uniquement (pas d'options)
        packaging = packaging or []
        documents = documents or []
        if insurance is None:
            insurance = []
        selected_guids = self._selected_guids(
            packaging, documents, insurance
        )

        departure = self._get_affiliate_direction(departure_city)
        destination = self._get_affiliate_direction(destination_city)
        calc_date = plan_date or date.today()

        bootstrap = self._rpc(
            "Order.Request.Update",
            self._build_calculate_params(
                departure=departure,
                destination=destination,
                volume_m3=volume_m3,
                weight_kg=weight_kg,
                places=places,
                cargo_type=cargo_type,
                declared_value=declared_value,
                services={},
                plan_date=calc_date,
            ),
        )
        calculate_data = bootstrap.get("result", {}).get("calculate")
        if not calculate_data:
            raise PekCalculatorError("Calculator returned no result")

        service_list = calculate_data.get("serviceList", {})
        services = self._apply_service_selection(service_list, selected_guids)

        payload = self._rpc(
            "Order.Request.Update",
            self._build_calculate_params(
                departure=departure,
                destination=destination,
                volume_m3=volume_m3,
                weight_kg=weight_kg,
                places=places,
                cargo_type=cargo_type,
                declared_value=declared_value,
                services=services,
                plan_date=calc_date,
            ),
        )
        calculate_data = payload.get("result", {}).get("calculate")
        if not calculate_data:
            raise PekCalculatorError("Calculator returned no result after services")

        return parse_calculation_result(
            calculate_data,
            departure_city=departure["city"],
            destination_city=destination["city"],
            volume_m3=volume_m3,
            weight_kg=weight_kg,
            places=places,
            tariff=tariff,
            raw=payload,
        )


def parse_calculation_result(
    calculate_data: dict[str, Any],
    *,
    departure_city: str,
    destination_city: str,
    volume_m3: float,
    weight_kg: float,
    places: int,
    tariff: str,
    raw: dict[str, Any],
) -> dict[str, Any]:
    auto = calculate_data.get("auto", {})
    express = calculate_data.get("express", {})

    auto_total = _price_value(auto.get("totalPriceWithCheckedServices"))
    express_total = _price_value(express.get("totalPriceWithCheckedServices"))

    services = calculate_data.get("services", [])
    transport = next(
        (item for item in services if item.get("name") == "Автоперевозка"),
        {},
    )
    auto_days = transport.get("countDays")
    express_days = express.get("countDays") or auto_days

    if tariff == "Экспресс-перевозка":
        selected_total = express_total or auto_total
        delivery_days = express_days
    else:
        selected_total = auto_total
        delivery_days = auto_days

    breakdown = []
    for item in services:
        if item.get("isShowInDetail") == 0:
            continue
        name = item.get("name", "")
        if name == "Автоперевозка":
            price = _price_value(item.get("priceBase")) or _price_value(
                item.get("priceExtra")
            )
        elif name == "Организация страхования груза":
            price = _price_value(item.get("price"))
            if price <= 0:
                continue
        else:
            if not item.get("isChecked"):
                continue
            price = _price_value(item.get("price"))
        if price <= 0:
            continue
        breakdown.append({"name": name, "cost": price})

    return {
        "departure_city": departure_city,
        "destination_city": destination_city,
        "volume_m3": volume_m3,
        "weight_kg": weight_kg,
        "places": places,
        "tariff": tariff,
        "delivery_days": (
            delivery_days[0]
            if isinstance(delivery_days, list) and delivery_days
            else delivery_days
        ),
        "delivery_term": _days_label(delivery_days),
        "cost_breakdown": breakdown,
        "total_cost": selected_total,
        "standard_cost": auto_total,
        "express_cost": express_total,
        "currency": "RUB",
        "raw": raw,
    }


def format_calculation_result(result: dict[str, Any]) -> str:
    tariff = result["tariff"]
    lines = [
        "### Маршрут и груз",
        f"* **Откуда**: {result['departure_city']}",
        f"* **Куда**: {result['destination_city']}",
        (
            f"* **Груз**: {result['volume_m3']} м³, "
            f"{result['weight_kg']} кг, {result['places']} место"
        ),
        "",
        "---",
        "",
        "### Тарифы",
        "",
    ]

    if tariff == "Стандарт":
        lines.extend(
            [
                "#### ⚡ Стандарт",
                f"* **Срок доставки**: {result['delivery_term']}",
                f"* **Стоимость**: {_format_rub(result['standard_cost'])}",
                "* *Самый выгодный*",
            ]
        )
    else:
        lines.extend(
            [
                "#### 🚀 Экспресс-перевозка",
                f"* **Срок доставки**: {result['delivery_term']}",
                f"* **Стоимость**: {_format_rub(result['express_cost'])}",
            ]
        )

    lines.extend(
        [
            "",
            "---",
            "",
            f"### Детализация стоимости ({tariff})",
        ]
    )
    for item in result["cost_breakdown"]:
        lines.append(f"* **{item['name']}**: {_format_rub(item['cost'])}")

    lines.extend(
        [
            "",
            "### Ориентировочная сумма:",
            f"**{_format_rub(result['total_cost'])}**",
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
    """ПЭК transport de base (Автоперевозка), Стандарт, sans options."""
    client = PekCalculatorClient()
    return client.calculate(
        departure_city=departure_city,
        destination_city=destination_city,
        volume_m3=volume_m3,
        weight_kg=weight_kg,
        places=places,
        cargo_type="мебель",
        declared_value=100,
        packaging=[],
        documents=[],
        insurance=[],
        tariff="Стандарт",
    )
