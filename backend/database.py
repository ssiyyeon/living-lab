from __future__ import annotations

import sqlite3
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIR / "living_lab.db"
LEGACY_DATABASE_PATH = BACKEND_DIR.parent / "data" / "runtime" / "dutory.sqlite3"
LEGACY_PASSWORD_ITERATIONS = 310_000


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _legacy_table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


def _migrate_legacy_database(connection: sqlite3.Connection) -> None:
    """기존 feature/frontend DB를 새 백엔드 스키마로 한 번만 이전합니다."""
    if not LEGACY_DATABASE_PATH.exists():
        return

    current_user_count = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]
    if int(current_user_count) > 0:
        return

    legacy = sqlite3.connect(LEGACY_DATABASE_PATH)
    legacy.row_factory = sqlite3.Row
    try:
        tables = _legacy_table_names(legacy)
        if "users" not in tables:
            return

        for row in legacy.execute("SELECT * FROM users ORDER BY id"):
            legacy_password = (
                f"pbkdf2_sha256${LEGACY_PASSWORD_ITERATIONS}"
                f"${row['password_salt']}${row['password_hash']}"
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO users (
                    id, username, display_name, password_hash, role, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["username"],
                    row["display_name"],
                    legacy_password,
                    row["role"],
                    row["created_at"],
                ),
            )

        if "sessions" in tables:
            for row in legacy.execute("SELECT * FROM sessions"):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO sessions (
                        token_hash, user_id, created_at, expires_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["token_hash"],
                        row["user_id"],
                        row["created_at"],
                        row["expires_at"],
                    ),
                )

        if "admin_contacts" in tables:
            for row in legacy.execute(
                "SELECT * FROM admin_contacts WHERE is_deleted = 0 ORDER BY created_at"
            ):
                connection.execute(
                    """
                    INSERT INTO public_contacts (
                        contact_group, organization, label, phone, note,
                        source, source_url, is_hidden, created_at, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    """,
                    (
                        row["group_name"],
                        row["organization"],
                        row["label"],
                        row["phone"],
                        row["note"],
                        "이전 버전 관리자 등록",
                        row["source_url"],
                        row["created_at"],
                        row["updated_at"],
                        row["updated_by"],
                    ),
                )

        if "guide_overrides" in tables:
            for row in legacy.execute("SELECT * FROM guide_overrides"):
                connection.execute(
                    """
                    INSERT OR REPLACE INTO guide_overrides (
                        guide_id, title, description, sections_json, cautions_json,
                        created_at, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["guide_id"],
                        row["title"],
                        row["description"],
                        row["sections_json"],
                        row["cautions_json"],
                        row["created_at"],
                        row["updated_at"],
                        row["updated_by"],
                    ),
                )
    finally:
        legacy.close()


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

        # JSON 원본 연락처를 DB에 한 번만 연결하기 위한 등록부입니다.
        # 연락처가 관리 화면에서 수정되거나 숨김 처리되어도 seed_key가
        # 남아 있으므로 서버 재시작 때 원본이 중복 생성되지 않습니다.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_seed_registry (
                seed_key TEXT PRIMARY KEY,
                contact_id INTEGER NOT NULL,
                FOREIGN KEY (contact_id)
                    REFERENCES public_contacts(id)
                    ON DELETE CASCADE
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
            CREATE INDEX IF NOT EXISTS idx_contact_seed_registry_contact
            ON contact_seed_registry(contact_id)
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

        _migrate_legacy_database(connection)


initialize_database()
