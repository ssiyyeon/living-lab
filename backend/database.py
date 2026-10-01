from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "runtime" / "dutory.sqlite3"


def database_path() -> Path:
    configured = os.getenv("DUTORY_DB_PATH", "").strip()
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE_PATH


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS admin_contacts (
                contact_id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                organization TEXT NOT NULL,
                label TEXT NOT NULL,
                phone TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                is_deleted INTEGER NOT NULL DEFAULT 0,
                updated_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(updated_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS guide_overrides (
                guide_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                sections_json TEXT NOT NULL,
                cautions_json TEXT NOT NULL,
                updated_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(updated_by) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
            ON sessions(expires_at);
            """
        )
