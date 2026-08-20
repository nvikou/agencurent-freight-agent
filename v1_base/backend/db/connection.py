"""Connexion SQLite et initialisation du schéma."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def default_db_path() -> Path:
    """Chemin BDD : DATABASE_PATH ou v1_base/data/database.db."""
    env = os.environ.get("DATABASE_PATH")
    if env:
        return Path(env)
    # backend/db → backend → v1_base/data
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "database.db"
    )


DEFAULT_DB_PATH = default_db_path()


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Ouvre une connexion SQLite avec row_factory."""
    path = Path(db_path) if db_path else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(
    conn: sqlite3.Connection,
    schema_path: Path | None = None,
) -> None:
    """Applique schema.sql."""
    sql = (schema_path or SCHEMA_PATH).read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
