from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import sqlite3

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from typing import Any

from backend.database import (
    get_connection,
)


# 로그인 유지 시간: 12시간
SESSION_MAX_AGE_SECONDS = (
    12 * 60 * 60
)


# 비밀번호 해시에 사용할 scrypt 설정
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def _utc_now() -> datetime:
    """
    현재 UTC 시간을 반환
    """

    return datetime.now(
        timezone.utc
    )


def _iso(
    value: datetime,
) -> str:
    """
    datetime을 DB 저장용 문자열로 변환
    """

    return value.isoformat(
        timespec="seconds"
    )


def _encode(
    value: bytes,
) -> str:
    """
    bytes를 문자열 형태로 저장하기 위한 변환
    """

    return (
        base64
        .urlsafe_b64encode(value)
        .decode("ascii")
    )


def _decode(
    value: str,
) -> bytes:
    """
    저장된 문자열을 다시 bytes로 변환
    """

    return (
        base64
        .urlsafe_b64decode(
            value.encode("ascii")
        )
    )


def _hash_password(
    password: str,
) -> str:
    """
    비밀번호를 평문으로 저장하지 않고
    scrypt 방식으로 해시
    """

    salt = os.urandom(16)

    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )

    return (
        f"scrypt"
        f"${SCRYPT_N}"
        f"${SCRYPT_R}"
        f"${SCRYPT_P}"
        f"${_encode(salt)}"
        f"${_encode(digest)}"
    )


def _verify_password(
    password: str,
    stored_password: str,
) -> bool:
    """
    사용자가 입력한 비밀번호와
    DB에 저장된 해시 비밀번호를 비교
    """

    try:

        (
            algorithm,
            n,
            r,
            p,
            salt,
            expected,
        ) = stored_password.split(
            "$",
            5,
        )

        if algorithm != "scrypt":
            return False

        digest = hashlib.scrypt(
            password.encode(
                "utf-8"
            ),
            salt=_decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
        )

        return hmac.compare_digest(
            digest,
            _decode(expected),
        )

    except (
        ValueError,
        TypeError,
    ):
        return False


def _hash_session_token(
    token: str,
) -> str:
    """
    로그인 세션 토큰도 그대로 DB에 저장하지 않고
    SHA-256 해시값으로 저장
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _user_dict(
    row: Any,
) -> dict[str, Any]:
    """
    DB 조회 결과를 프론트에서 사용하는 형식으로 변환
    """

    return {
        "id": int(
            row["id"]
        ),

        "username": str(
            row["username"]
        ),

        "displayName": str(
            row["display_name"]
        ),

        "role": str(
            row["role"]
        ),
    }


class AuthService:

    def needs_setup(
        self,
    ) -> bool:
        """
        아직 사용자 계정이 하나도 없으면
        최초 관리자 설정이 필요하다고 판단
        """

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM users
                """
            ).fetchone()

        return (
            int(row["count"]) == 0
        )

    def setup_admin(
        self,
        display_name: str,
        username: str,
        password: str,
    ) -> tuple[
        dict[str, Any],
        str,
    ]:
        """
        최초 관리자 계정 생성
        """

        now = _utc_now()

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM users
                """
            ).fetchone()

            if int(row["count"]) > 0:

                raise ValueError(
                    "초기 관리자 설정이 이미 완료되었습니다."
                )

            try:

                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        username,
                        display_name,
                        password_hash,
                        role,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        username.strip(),
                        display_name.strip(),

                        _hash_password(
                            password
                        ),

                        "admin",

                        _iso(
                            now
                        ),
                    ),
                )

            except sqlite3.IntegrityError as exc:

                raise ValueError(
                    "이미 사용 중인 아이디입니다."
                ) from exc

            user_id = int(
                cursor.lastrowid
            )

            user_row = connection.execute(
                """
                SELECT
                    id,
                    username,
                    display_name,
                    role
                FROM users
                WHERE id = ?
                """,
                (
                    user_id,
                ),
            ).fetchone()

        token = (
            self.create_session(
                user_id
            )
        )

        return (
            _user_dict(
                user_row
            ),
            token,
        )

    def login(
        self,
        username: str,
        password: str,
    ) -> (
        tuple[
            dict[str, Any],
            str,
        ]
        | None
    ):
        """
        로그인 처리
        """

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT
                    id,
                    username,
                    display_name,
                    role,
                    password_hash
                FROM users
                WHERE username = ?
                """,
                (
                    username.strip(),
                ),
            ).fetchone()

        if row is None:
            return None

        if not _verify_password(
            password,
            str(
                row["password_hash"]
            ),
        ):
            return None

        user = (
            _user_dict(
                row
            )
        )

        token = (
            self.create_session(
                user["id"]
            )
        )

        return (
            user,
            token,
        )

    def create_session(
        self,
        user_id: int,
    ) -> str:
        """
        로그인 성공 시 세션 토큰 생성
        """

        token = (
            secrets
            .token_urlsafe(32)
        )

        now = (
            _utc_now()
        )

        expires_at = (
            now
            + timedelta(
                seconds=(
                    SESSION_MAX_AGE_SECONDS
                )
            )
        )

        with get_connection() as connection:

            # 이미 만료된 세션 제거
            connection.execute(
                """
                DELETE FROM sessions
                WHERE expires_at <= ?
                """,
                (
                    _iso(
                        now
                    ),
                ),
            )

            # 새 세션 저장
            connection.execute(
                """
                INSERT INTO sessions (
                    token_hash,
                    user_id,
                    created_at,
                    expires_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    _hash_session_token(
                        token
                    ),

                    user_id,

                    _iso(
                        now
                    ),

                    _iso(
                        expires_at
                    ),
                ),
            )

        return token

    def current_user(
        self,
        token: str | None,
    ) -> dict[
        str,
        Any,
    ] | None:
        """
        쿠키에 있는 세션 토큰을 이용해
        현재 로그인 사용자를 확인
        """

        if not token:
            return None

        now = (
            _iso(
                _utc_now()
            )
        )

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT
                    users.id,
                    users.username,
                    users.display_name,
                    users.role

                FROM sessions

                JOIN users
                    ON users.id =
                    sessions.user_id

                WHERE
                    sessions.token_hash = ?

                AND
                    sessions.expires_at > ?
                """,
                (
                    _hash_session_token(
                        token
                    ),

                    now,
                ),
            ).fetchone()

            # 만료된 세션 정리
            connection.execute(
                """
                DELETE FROM sessions
                WHERE expires_at <= ?
                """,
                (
                    now,
                ),
            )

        if row is None:
            return None

        return (
            _user_dict(
                row
            )
        )

    def logout(
        self,
        token: str | None,
    ) -> None:
        """
        로그아웃 시 해당 세션 삭제
        """

        if not token:
            return

        with get_connection() as connection:

            connection.execute(
                """
                DELETE FROM sessions
                WHERE token_hash = ?
                """,
                (
                    _hash_session_token(
                        token
                    ),
                ),
            )


auth_service = (
    AuthService()
)