from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.database import get_connection


PASSWORD_ITERATIONS = 310_000
SESSION_HOURS = 12


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _password_hash(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return base64.b64encode(digest).decode("ascii")


def _user_response(row: Any) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "displayName": str(row["display_name"]),
        "role": str(row["role"]),
    }


def needs_setup() -> bool:
    with get_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        return not row or int(row["count"]) == 0


def create_initial_admin(username: str, display_name: str, password: str) -> dict[str, Any] | None:
    normalized_username = username.strip()
    normalized_display_name = display_name.strip()
    salt = secrets.token_bytes(16)
    now = _iso(_now())

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT id FROM users LIMIT 1").fetchone():
            return None
        cursor = connection.execute(
            """
            INSERT INTO users (
                username, display_name, password_hash, password_salt,
                role, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'admin', ?, ?)
            """,
            (
                normalized_username,
                normalized_display_name,
                _password_hash(password, salt),
                base64.b64encode(salt).decode("ascii"),
                now,
                now,
            ),
        )
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _user_response(row)


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
    if not row:
        return None
    try:
        salt = base64.b64decode(str(row["password_salt"]))
    except ValueError:
        return None
    actual = _password_hash(password, salt)
    return _user_response(row) if hmac.compare_digest(str(row["password_hash"]), actual) else None


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    created_at = _now()
    expires_at = created_at + timedelta(hours=SESSION_HOURS)
    with get_connection() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (_iso(created_at),))
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token_hash, user_id, _iso(created_at), _iso(expires_at)),
        )
    return token


def user_for_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (token_hash, _iso(_now())),
        ).fetchone()
    return _user_response(row) if row else None


def delete_session(token: str | None) -> None:
    if not token:
        return
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with get_connection() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
