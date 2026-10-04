from __future__ import annotations

import sqlite3
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIR / "living_lab.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    BACKEND_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guide_overrides (
                guide_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                sections_json TEXT NOT NULL,
                cautions_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY (updated_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guide_section_metadata (
                guide_id TEXT NOT NULL,
                section_index INTEGER NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (guide_id, section_index)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS public_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_group TEXT NOT NULL,
                organization TEXT NOT NULL,
                label TEXT NOT NULL,
                phone TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '관리자 등록',
                source_url TEXT NOT NULL DEFAULT '',
                is_hidden INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY (updated_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        # 기존 전체 매뉴얼을 관리자가 수정한 경우
        # 원본 JSON은 건드리지 않고 수정본만 저장
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_overrides (
                entry_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY (updated_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        # 관리자가 새로 추가한 민원/매뉴얼 항목
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_custom_entries (
                entry_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by INTEGER,
                FOREIGN KEY (updated_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
            ON sessions(expires_at)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_public_contacts_hidden
            ON public_contacts(is_hidden)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_manual_overrides_updated_at
            ON manual_overrides(updated_at)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_manual_custom_entries_updated_at
            ON manual_custom_entries(updated_at)
            """
        )


initialize_database()