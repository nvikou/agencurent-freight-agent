"""Données internes Dellin (dictionnaires, sans base de données)."""

from __future__ import annotations

from typing import Any

# --- Villes (3 exemples) ---

CITIES: list[dict[str, Any]] = [
    {"id_ville": 1, "ville": "Санкт-Петербург"},
    {"id_ville": 2, "ville": "Москва"},
    {"id_ville": 3, "ville": "Омск"},
]

# --- Directions ---

DIRECTIONS: list[dict[str, Any]] = [
    {
        "id_direction": 1,
        "id_ville_expediteur": 1,
        "id_ville_arrivee": 2,
        "ville_expediteur": "Санкт-Петербург",
        "ville_arrivee": "Москва",
        "delai_jours": 2,
    },
    {
        "id_direction": 2,
        "id_ville_expediteur": 2,
        "id_ville_arrivee": 1,
        "ville_expediteur": "Москва",
        "ville_arrivee": "Санкт-Петербург",
        "delai_jours": 2,
    },
    {
        "id_direction": 3,
        "id_ville_expediteur": 1,
        "id_ville_arrivee": 3,
        "ville_expediteur": "Санкт-Петербург",
        "ville_arrivee": "Омск",
        "delai_jours": 5,
    },
    {
        "id_direction": 4,
        "id_ville_expediteur": 3,
        "id_ville_arrivee": 1,
        "ville_expediteur": "Омск",
        "ville_arrivee": "Санкт-Петербург",
        "delai_jours": 5,
    },
    {
        "id_direction": 5,
        "id_ville_expediteur": 2,
        "id_ville_arrivee": 3,
        "ville_expediteur": "Москва",
        "ville_arrivee": "Омск",
        "delai_jours": 5,
    },
    {
        "id_direction": 6,
        "id_ville_expediteur": 3,
        "id_ville_arrivee": 2,
        "ville_expediteur": "Омск",
        "ville_arrivee": "Москва",
        "delai_jours": 7,
    },
]

# --- Classification poids (Весовой груз, кг) ---

WEIGHT_CLASSIFICATIONS: list[dict[str, Any]] = [
    {
        "id_classification_poids": 1,
        "label": "0 – 1 499",
        "min_kg": 0,
        "max_kg": 1499,
    },
    {
        "id_classification_poids": 2,
        "label": "1 500 – 2 499",
        "min_kg": 1500,
        "max_kg": 2499,
    },
    {
        "id_classification_poids": 3,
        "label": "2 500 – 4 999",
        "min_kg": 2500,
        "max_kg": 4999,
    },
    {
        "id_classification_poids": 4,
        "label": "5 000 – 9 999",
        "min_kg": 5000,
        "max_kg": 9999,
    },
    {
        "id_classification_poids": 5,
        "label": "10 000 – 25 000",
        "min_kg": 10000,
        "max_kg": 25000,
    },
]

# --- Classification volume (Объёмный груз, м³) ---

VOLUME_CLASSIFICATIONS: list[dict[str, Any]] = [
    {
        "id_classification_volume": 1,
        "label": "0- 3",
        "min_m3": 0,
        "max_m3": 3,
    },
    {
        "id_classification_volume": 2,
        "label": "0 – 8,32",
        "min_m3": 0,
        "max_m3": 8.32,
    },
    {
        "id_classification_volume": 3,
        "label": "8,33 – 14,99",
        "min_m3": 8.33,
        "max_m3": 14.99,
    },
    {
        "id_classification_volume": 4,
        "label": "15,00 – 21,99",
        "min_m3": 15.0,
        "max_m3": 21.99,
    },
    {
        "id_classification_volume": 5,
        "label": "22,00 – 34,99",
        "min_m3": 22.0,
        "max_m3": 34.99,
    },
    {
        "id_classification_volume": 6,
        "label": "35,00 – 110,00",
        "min_m3": 35.0,
        "max_m3": 110.0,
    },
]

# --- Количество мест ---

PLACE_COUNTS: list[dict[str, Any]] = [
    {"id_kolichestvo_mest": 1, "kolichestvo_mest": 1},
]

# --- Méthode de calcul ---

METHODS: list[dict[str, Any]] = [
    {"id_methode": 1, "methode": "одно грузоместо"},
]

# --- Type de tarif ---

TYPES: list[dict[str, Any]] = [
    {"id_type": 1, "type": "Стандарт"},
    {"id_type": 2, "type": "Экспресс-перевозка"},
]

# --- Упаковка ---

PACKAGING: list[dict[str, Any]] = [
    {
        "id_upakovka": 1,
        "upakovka": "Комплекс «палетный борт + амортизация»",
        "prix": 1080.0,
    },
    {
        "id_upakovka": 2,
        "upakovka": "палетный борт (только до терминала-получателя)",
        "prix": 720.0,
    },
    {
        "id_upakovka": 3,
        "upakovka": "деревянная обрешётка",
        "prix": 2500.0,
    },
    {
        "id_upakovka": 4,
        "upakovka": "Комплекс «обрешётка + амортизация»",
        "prix": 2800.0,
    },
    {
        "id_upakovka": 5,
        "upakovka": "амортизирующая упаковка",
        "prix": 500.0,
    },
    {
        "id_upakovka": 6,
        "upakovka": "воздушно-пузырьковая плёнка",
        "prix": 300.0,
    },
]

# --- Autres services (documents, etc.) ---

OTHER_PRICES: list[dict[str, Any]] = [
    {
        "id_autre": 1,
        "service": "отправить сопроводительные документы",
        "prix": 255.0,
    },
    {
        "id_autre": 2,
        "service": "Вернуть документы",
        "prix": 255.0,
    },
    {
        "id_autre": 3,
        "service": "Информирование о статусе доставки",
        "prix": 15.0,
    },
    {
        "id_autre": 4,
        "service": "Страхование груза и срока",
        "prix": 960.0,
    },
]

# --- Grille tarifaire (prix de base transport) ---
# Clés: direction, poids, volume, places, type
# Tarifs pilotes diplôme (1 m³, 1 kg, 1 place, Стандарт).
# СПб ↔ Москва — symétrique ; СПб ↔ Омск — symétrique.

PRICES: list[dict[str, Any]] = [
    # Санкт-Петербург → Москва, 1 kg, 1 m³, Стандарт
    {
        "id_prix": 1,
        "id_direction": 1,
        "id_classification_poids": 1,
        "id_classification_volume": 1,
        "id_kolichestvo_mest": 1,
        "id_methode": 1,
        "id_type": 1,
        "prix": 6557.0,
    },
    # Москва → Санкт-Петербург, 1 kg, 1 m³, Стандарт
    {
        "id_prix": 2,
        "id_direction": 2,
        "id_classification_poids": 1,
        "id_classification_volume": 1,
        "id_kolichestvo_mest": 1,
        "id_methode": 1,
        "id_type": 1,
        "prix": 6557.0,
    },
    # Санкт-Петербург → Омск, 1 kg, 1 m³, Стандарт
    {
        "id_prix": 3,
        "id_direction": 3,
        "id_classification_poids": 1,
        "id_classification_volume": 1,
        "id_kolichestvo_mest": 1,
        "id_methode": 1,
        "id_type": 1,
        "prix": 8200.0,
    },
    # Омск → Санкт-Петербург, 1 kg, 1 m³, Стандарт
    {
        "id_prix": 4,
        "id_direction": 4,
        "id_classification_poids": 1,
        "id_classification_volume": 1,
        "id_kolichestvo_mest": 1,
        "id_methode": 1,
        "id_type": 1,
        "prix": 8200.0,
    },
    # Москва → Омск, 1 kg, 1 m³, Стандарт
    {
        "id_prix": 5,
        "id_direction": 5,
        "id_classification_poids": 1,
        "id_classification_volume": 1,
        "id_kolichestvo_mest": 1,
        "id_methode": 1,
        "id_type": 1,
        "prix": 10100.0,
    },
    # Омск → Москва, 1 kg, 1 m³, Стандарт
    {
        "id_prix": 6,
        "id_direction": 6,
        "id_classification_poids": 1,
        "id_classification_volume": 1,
        "id_kolichestvo_mest": 1,
        "id_methode": 1,
        "id_type": 1,
        "prix": 14332.0,
    },
]

# Export JSON-compatible (pour édition / import futur)

RESOURCES: dict[str, list[dict[str, Any]]] = {
    "cities": CITIES,
    "directions": DIRECTIONS,
    "weight_classifications": WEIGHT_CLASSIFICATIONS,
    "volume_classifications": VOLUME_CLASSIFICATIONS,
    "place_counts": PLACE_COUNTS,
    "methods": METHODS,
    "types": TYPES,
    "packaging": PACKAGING,
    "other_prices": OTHER_PRICES,
    "prices": PRICES,
}
