"""Tests extraction prix transport de base."""

from dellin.calculator import calculate_shipping

from db.extract import extract_base_transport_price


def test_dellin_base_transport_spb_moscow():
    result = calculate_shipping(
        departure_city="Санкт-Петербург",
        destination_city="Москва",
        volume_m3=1,
        weight_kg=1,
        places=1,
    )
    price = extract_base_transport_price("dellin", result)
    assert price == 6557
    assert result["total_cost"] == 6557


def test_pek_breakdown_has_autoperevozka():
    breakdown = [{"name": "Автоперевозка", "cost": 4720.0}]
    price = extract_base_transport_price(
        "pek",
        {"cost_breakdown": breakdown},
    )
    assert price == 4720.0
