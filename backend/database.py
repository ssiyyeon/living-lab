from __future__ import annotations

import sqlite3
from pathlib import Path


# ---------------------------------------------------------
# DB 파일 위치
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    BACKEND_DIR
    / "living_lab.db"
)


# ---------------------------------------------------------
# DB 연결
# ---------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    SQLite DB 연결을 반환합니다.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    # row["username"] 형태로 사용할 수 있게 설정
    connection.row_factory = sqlite3.Row

    # 외래키 기능 활성화
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ---------------------------------------------------------
# DB 초기화
# ---------------------------------------------------------

def initialize_database() -> None:
    """
    프로그램에서 필요한 테이블을 생성합니다.

    이미 존재하는 테이블은 유지되며,
    없는 테이블만 새로 만들어집니다.
    """

    BACKEND_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with get_connection() as connection:

        # -------------------------------------------------
        # 1. 사용자 계정
        # -------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT NOT NULL UNIQUE,

                display_name TEXT NOT NULL,

                password_hash TEXT NOT NULL,

                role TEXT NOT NULL
                    CHECK (
                        role IN ('admin', 'staff')
                    ),

                created_at TEXT NOT NULL
            )
            """
        )


        # -------------------------------------------------
        # 2. 로그인 세션
        # -------------------------------------------------

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


        # -------------------------------------------------
        # 3. 관리자가 수정한 업무 안내
        # -------------------------------------------------

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


        # -------------------------------------------------
        # 4. 관리자가 새로 추가한 안내 단계 날짜
        # -------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guide_section_metadata (
                guide_id TEXT NOT NULL,

                section_index INTEGER NOT NULL,

                added_at TEXT NOT NULL,

                PRIMARY KEY (
                    guide_id,
                    section_index
                )
            )
            """
        )


        # -------------------------------------------------
        # 5. 공용 전화번호부
        #
        # 관리자 페이지에서 추가/수정하고
        # 일반 사용자도 조회할 수 있습니다.
        # -------------------------------------------------

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


        # -------------------------------------------------
        # 세션 만료시간 조회용 인덱스
        # -------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_sessions_expires_at
            ON sessions(expires_at)
            """
        )


        # -------------------------------------------------
        # 연락처 조회용 인덱스
        # -------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_public_contacts_hidden
            ON public_contacts(is_hidden)
            """
        )


# ---------------------------------------------------------
# import 시 DB 자동 초기화
# ---------------------------------------------------------

initialize_database()