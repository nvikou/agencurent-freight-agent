"""Recherche dans les données internes Dellin."""

from __future__ import annotations

import re
from typing import Any

from dellin.resources import (
    DIRECTIONS,
    OTHER_PRICES,
    PACKAGING,
    PLACE_COUNTS,
    PRICES,
    VOLUME_CLASSIFICATIONS,
    WEIGHT_CLASSIFICATIONS,
)


class DellinLookupError(Exception):
    """Donnée introuvable dans la ressource interne."""


def _normalize_city(name: str) -> str:
    text = name.strip().lower()
    text = re.sub(r"\s+г\.?\s*$", "", text)
    return text.strip()


def find_weight_class(weight_kg: float) -> dict[str, Any]:
    for item in WEIGHT_CLASSIFICATIONS:
        if item["min_kg"] <= weight_kg <= item["max_kg"]:
            return item
    raise DellinLookupError(f"Poids hors grille: {weight_kg} kg")


def find_volume_class(volume_m3: float) -> dict[str, Any]:
    for item in VOLUME_CLASSIFICATIONS:
        if item["min_m3"] <= volume_m3 <= item["max_m3"]:
            return item
    raise DellinLookupError(f"Volume hors grille: {volume_m3} m³")


def find_direction(
    departure_city: str,
    destination_city: str,
) -> dict[str, Any]:
    dep = _normalize_city(departure_city)
    dest = _normalize_city(destination_city)
    for item in DIRECTIONS:
        exp = _normalize_city(item["ville_expediteur"])
        arr = _normalize_city(item["ville_arrivee"])
        if dep in exp or exp in dep:
            if dest in arr or arr in dest:
                return item
    raise DellinLookupError(
        f"Direction introuvable: {departure_city} → {destination_city}"
    )


def find_base_price(
    *,
    id_direction: int,
    id_classification_poids: int,
    id_classification_volume: int,
    id_kolichestvo_mest: int = 1,
    id_methode: int = 1,
    id_type: int = 1,
) -> dict[str, Any]:
    for item in PRICES:
        if (
            item["id_direction"] == id_direction
            and item["id_classification_poids"] == id_classification_poids
            and item["id_classification_volume"] == id_classification_volume
            and item["id_kolichestvo_mest"] == id_kolichestvo_mest
            and item["id_methode"] == id_methode
            and item["id_type"] == id_type
        ):
            return item
    raise DellinLookupError(
        "Tarif de base introuvable pour cette combinaison "
        f"(direction={id_direction}, poids={id_classification_poids}, "
        f"volume={id_classification_volume}, type={id_type})"
    )


def find_packaging(names: list[str]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for name in names:
        match = next(
            (p for p in PACKAGING if p["upakovka"] == name),
            None,
        )
        if match is None:
            raise DellinLookupError(f"Упаковка inconnue: {name}")
        found.append(match)
    return found


def find_other_services(names: list[str]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for name in names:
        match = next(
            (s for s in OTHER_PRICES if s["service"] == name),
            None,
        )
        if match is None:
            raise DellinLookupError(f"Service inconnu: {name}")
        found.append(match)
    return found


def default_place_count() -> dict[str, Any]:
    return PLACE_COUNTS[0]
