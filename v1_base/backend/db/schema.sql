-- Historique append-only des prix (transport de base, Стандарт).

CREATE TABLE IF NOT EXISTS carriers (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name_ru TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY,
    name_ru TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS city_aliases (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id),
    carrier_id INTEGER NOT NULL REFERENCES carriers(id),
    alias TEXT NOT NULL,
    UNIQUE(city_id, carrier_id)
);

CREATE TABLE IF NOT EXISTS collection_tasks (
    id INTEGER PRIMARY KEY,
    departure_id INTEGER NOT NULL REFERENCES cities(id),
    destination_id INTEGER NOT NULL REFERENCES cities(id),
    volume_m3 REAL NOT NULL DEFAULT 1,
    weight_kg REAL NOT NULL DEFAULT 1,
    places INTEGER NOT NULL DEFAULT 1,
    tariff_type TEXT NOT NULL DEFAULT 'Стандарт',
    is_active INTEGER NOT NULL DEFAULT 1
);

-- Pas de UNIQUE(task, carrier) : chaque collecte = nouveau snapshot t
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES collection_tasks(id),
    carrier_id INTEGER NOT NULL REFERENCES carriers(id),
    transport_price REAL,
    delivery_days INTEGER,
    status TEXT NOT NULL CHECK (status IN ('ok', 'error')),
    error_message TEXT,
    source TEXT NOT NULL DEFAULT 'collect'
        CHECK (source IN ('collect', 'live')),
    collected_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_quotes_task ON quotes(task_id);
CREATE INDEX IF NOT EXISTS idx_quotes_collected
    ON quotes(collected_at);
CREATE INDEX IF NOT EXISTS idx_quotes_task_carrier
    ON quotes(task_id, carrier_id, id);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    route_summary TEXT,
    content_md TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_session
    ON chat_messages(session_id, id);
