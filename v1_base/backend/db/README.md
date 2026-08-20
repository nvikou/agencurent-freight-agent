# Module `db` (v1_base)

SQLite pour la comparaison **transport de base** (Стандарт, sans options).

## Tables

- `carriers`, `cities`, `city_aliases` — référentiels
- `collection_tasks` — 6 routes pilotes (1 m³, 1 kg, 1 place)
- `quotes` — prix + délai + **`collected_at`**
- `reports` — rapports Markdown générés par `generate_report.py`

## Règle d’extraction

| Transporteur | Ligne |
|--------------|-------|
| ПЭК | Автоперевозка |
| Dellin / Baikal | Межтерминальная перевозка |

Voir aussi le README racine `v1_base/README.md`.
