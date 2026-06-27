from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]

DB_CANDIDATES = [
    BASE_DIR / 'buildlogicpcs.db',
    BASE_DIR / 'data' / 'buildlogicpcs.db',
]

SCHEMA_PATH = BASE_DIR / 'sql' / 'schema.sql'
SEED_PATH = BASE_DIR / 'sql' / 'seed.sql'

# Also look relative to the backend directory
_SCHEMA_ALT = Path(__file__).resolve().parent.parent / 'sql' / 'schema.sql'
_SEED_ALT = Path(__file__).resolve().parent.parent / 'sql' / 'seed.sql'


def _resolve_db_path() -> Path:
    for candidate in DB_CANDIDATES:
        if candidate.exists():
            return candidate
    return DB_CANDIDATES[0]


def get_connection() -> sqlite3.Connection:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def init_database(force_reset: bool = False) -> None:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and not force_reset:
        return

    if db_path.exists() and force_reset:
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')

    try:
        schema = SCHEMA_PATH if SCHEMA_PATH.exists() else _SCHEMA_ALT
        seed = SEED_PATH if SEED_PATH.exists() else _SEED_ALT
        conn.executescript(schema.read_text(encoding='utf-8'))
        conn.executescript(seed.read_text(encoding='utf-8'))
        conn.commit()
    finally:
        conn.close()


def fetch_all(table_name: str) -> list[dict[str, Any]]:
    allowed = {
        'CPU',
        'GPU',
        'MOTHERBOARD',
        'RAM',
        'PSU',
        'CASE',
        'GAMES',
        'GAMES_PRESET_APPLIED',
        'BUILD',
        'COMPATIBILITY_RULES',
    }
    if table_name not in allowed:
        raise ValueError(f'Unsupported table: {table_name}')

    conn = get_connection()
    try:
        query_name = '"CASE"' if table_name == 'CASE' else table_name
        rows = conn.execute(f'SELECT * FROM {query_name}').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()