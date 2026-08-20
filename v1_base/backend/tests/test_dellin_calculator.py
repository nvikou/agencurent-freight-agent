"""Tests Dellin — transport de base uniquement."""

from dellin.calculator import calculate_shipping
from dellin.lookup import find_volume_class, find_weight_class


def test_weight_class_lookup():
    assert find_weight_class(1)["id_classification_poids"] == 1
    assert find_weight_class(500)["id_classification_poids"] == 1
    assert find_weight_class(1500)["id_classification_poids"] == 2


def test_volume_class_lookup():
    assert find_volume_class(1)["id_classification_volume"] == 1
    assert find_volume_class(3)["id_classification_volume"] == 1


def test_spb_to_moscow_base_only():
    result = calculate_shipping(
        departure_city="Санкт-Петербург",
        destination_city="Москва",
        volume_m3=1,
        weight_kg=1,
        places=1,
    )
    assert result["departure_city"] == "Санкт-Петербург"
    assert result["destination_city"] == "Москва"
    assert result["delivery_days"] == 2
    assert result["tariff"] == "Стандарт"
    assert result["total_cost"] == 6557
    assert len(result["cost_breakdown"]) == 1
    assert result["cost_breakdown"][0]["name"].startswith(
        "Межтерминальная перевозка"
    )


def test_omsk_to_moscow_base_transport():
    result = calculate_shipping(
        departure_city="Омск",
        destination_city="Москва",
        volume_m3=1,
        weight_kg=1,
        places=1,
    )
    assert result["delivery_days"] == 7
    assert result["total_cost"] == 14332


def test_moscow_to_omsk_base_transport():
    result = calculate_shipping(
        departure_city="Москва",
        destination_city="Омск",
        volume_m3=1,
        weight_kg=1,
        places=1,
    )
    assert result["delivery_days"] == 5
    assert result["total_cost"] == 10100


def test_omsk_to_spb_base_transport():
    result = calculate_shipping(
        departure_city="Омск",
        destination_city="Санкт-Петербург",
        volume_m3=1,
        weight_kg=1,
        places=1,
    )
    assert result["delivery_days"] == 5
    assert result["total_cost"] == 8200
