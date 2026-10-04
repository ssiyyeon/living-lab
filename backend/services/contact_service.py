from __future__ import annotations

from datetime import (
    date,
    datetime,
    timezone,
)

import json
from pathlib import Path

from typing import Any

from backend.database import (
    get_connection,
)


# ---------------------------------------------------------
# 기본 정보
# ---------------------------------------------------------

CONTACT_SOURCE = "관리자 등록"

CONTACT_NOTICE = (
    "공용 업무 연락처입니다. "
    "개인 연락처는 등록하지 말고 "
    "부서 또는 기관의 공개 연락처만 사용해 주세요."
)

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DEPARTMENT_CONTACTS_PATH = (
    ROOT_DIR
    / "data"
    / "contacts"
    / "department_contacts.json"
)

QUICK_GUIDES_PATH = (
    ROOT_DIR
    / "data"
    / "manual"
    / "quick_guides.json"
)

PUBLIC_DIRECTORY_SOURCE = "유성구 공개 부서 연락처"
MANUAL_CONTACT_SOURCE = "당직 근무요령 및 상황별 매뉴얼"


# ---------------------------------------------------------
# 시간 관련 함수
# ---------------------------------------------------------

def _now_iso() -> str:
    """
    DB 저장용 현재 UTC 시간
    """

    return datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )


def _today() -> str:
    """
    화면 표시용 날짜
    """

    return (
        date.today()
        .isoformat()
    )


# ---------------------------------------------------------
# 문자열 정리
# ---------------------------------------------------------

def _clean(
    value: Any,
) -> str:
    """
    None 등을 안전하게 빈 문자열로 변환하고
    앞뒤 공백을 제거합니다.
    """

    if value is None:
        return ""

    return str(
        value
    ).strip()


# ---------------------------------------------------------
# 프론트에서 사용하는 contact ID 처리
#
# DB:
# 1
#
# 프론트:
# contact_1
# ---------------------------------------------------------

def _make_contact_id(
    database_id: int,
) -> str:

    return (
        f"contact_{database_id}"
    )


def _parse_contact_id(
    contact_id: str,
) -> int:
    """
    contact_3 → 3

    잘못된 ID라면 ValueError 발생
    """

    value = (
        contact_id
        .strip()
    )

    if value.startswith(
        "contact_"
    ):

        value = value[
            len(
                "contact_"
            ):
        ]

    try:

        database_id = int(
            value
        )

    except ValueError as exc:

        raise ValueError(
            "올바르지 않은 연락처 ID입니다."
        ) from exc


    if database_id <= 0:

        raise ValueError(
            "올바르지 않은 연락처 ID입니다."
        )

    return database_id


# ---------------------------------------------------------
# ContactService
# ---------------------------------------------------------

class ContactService:

    def __init__(self) -> None:
        self.verified_at = _today()
        self.notice = CONTACT_NOTICE
        self._seed_default_contacts()


    # -----------------------------------------------------
    # 기존 JSON 전화번호부를 새 DB에 한 번만 등록
    # -----------------------------------------------------

    def _load_json(
        self,
        path: Path,
    ) -> dict[str, Any]:

        if not path.exists():
            return {}

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        return data if isinstance(data, dict) else {}


    def _default_contacts(
        self,
    ) -> list[dict[str, str]]:

        department_data = self._load_json(
            DEPARTMENT_CONTACTS_PATH
        )

        quick_guide_data = self._load_json(
            QUICK_GUIDES_PATH
        )

        self.verified_at = _clean(
            department_data.get(
                "verifiedAt",
                "",
            )
        ) or _today()

        source_notice = _clean(
            department_data.get(
                "notice",
                "",
            )
        )

        if source_notice:
            self.notice = (
                f"{source_notice} "
                "직원 개인 연락처와 비공개 비상연락망은 포함하지 않습니다."
            )

        contacts: list[dict[str, str]] = []

        default_contact = department_data.get(
            "defaultContact"
        )

        if isinstance(default_contact, dict):
            contacts.append(
                {
                    "seedKey": "department:default",
                    "group": "대표·당직",
                    "organization": _clean(
                        default_contact.get(
                            "department",
                            "유성구청",
                        )
                    ),
                    "label": _clean(
                        default_contact.get(
                            "label",
                            "대표전화",
                        )
                    ),
                    "phone": _clean(
                        default_contact.get(
                            "phone",
                            "",
                        )
                    ),
                    "note": _clean(
                        default_contact.get(
                            "note",
                            "",
                        )
                    ),
                    "source": PUBLIC_DIRECTORY_SOURCE,
                    "sourceUrl": _clean(
                        default_contact.get(
                            "sourceUrl",
                            "",
                        )
                    ),
                }
            )

        guides = quick_guide_data.get(
            "guides",
            [],
        )

        if isinstance(guides, list):
            emergency_guide = next(
                (
                    guide
                    for guide in guides
                    if isinstance(guide, dict)
                    and guide.get("id") == "emergency_contacts"
                ),
                {},
            )

            emergency_contacts = emergency_guide.get(
                "contacts",
                [],
            ) if isinstance(emergency_guide, dict) else []

            if isinstance(emergency_contacts, list):
                for index, contact in enumerate(
                    emergency_contacts
                ):
                    if not isinstance(contact, dict):
                        continue

                    contacts.append(
                        {
                            "seedKey": f"emergency:{index}",
                            "group": _clean(
                                contact.get(
                                    "group",
                                    "대표·당직",
                                )
                            ),
                            "organization": _clean(
                                contact.get(
                                    "organization",
                                    "",
                                )
                            ),
                            "label": _clean(
                                contact.get(
                                    "label",
                                    "",
                                )
                            ),
                            "phone": _clean(
                                contact.get(
                                    "phone",
                                    "",
                                )
                            ),
                            "note": _clean(
                                contact.get(
                                    "note",
                                    "",
                                )
                            ),
                            "source": MANUAL_CONTACT_SOURCE,
                            "sourceUrl": "",
                        }
                    )

        department_contacts = department_data.get(
            "contacts",
            [],
        )

        if isinstance(department_contacts, list):
            for index, contact in enumerate(
                department_contacts
            ):
                if not isinstance(contact, dict):
                    continue

                contacts.append(
                    {
                        "seedKey": f"department:{index}",
                        "group": "담당 부서",
                        "organization": _clean(
                            contact.get(
                                "department",
                                "",
                            )
                        ),
                        "label": _clean(
                            contact.get(
                                "label",
                                "",
                            )
                        ),
                        "phone": _clean(
                            contact.get(
                                "phone",
                                "",
                            )
                        ),
                        "note": _clean(
                            contact.get(
                                "note",
                                "",
                            )
                        ),
                        "source": PUBLIC_DIRECTORY_SOURCE,
                        "sourceUrl": _clean(
                            contact.get(
                                "sourceUrl",
                                "",
                            )
                        ),
                    }
                )

        return [
            contact
            for contact in contacts
            if contact["organization"]
            and contact["label"]
            and contact["phone"]
        ]


    def _seed_default_contacts(
        self,
    ) -> None:

        contacts = self._default_contacts()

        if not contacts:
            return

        now = _now_iso()

        with get_connection() as connection:
            for contact in contacts:
                registered = connection.execute(
                    """
                    SELECT contact_id
                    FROM contact_seed_registry
                    WHERE seed_key = ?
                    """,
                    (
                        contact["seedKey"],
                    ),
                ).fetchone()

                if registered is not None:
                    continue

                existing = connection.execute(
                    """
                    SELECT id
                    FROM public_contacts
                    WHERE organization = ?
                      AND label = ?
                      AND phone = ?
                    ORDER BY id
                    LIMIT 1
                    """,
                    (
                        contact["organization"],
                        contact["label"],
                        contact["phone"],
                    ),
                ).fetchone()

                if existing is None:
                    cursor = connection.execute(
                        """
                        INSERT INTO public_contacts (
                            contact_group,
                            organization,
                            label,
                            phone,
                            note,
                            source,
                            source_url,
                            is_hidden,
                            created_at,
                            updated_at,
                            updated_by
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, NULL)
                        """,
                        (
                            contact["group"],
                            contact["organization"],
                            contact["label"],
                            contact["phone"],
                            contact["note"],
                            contact["source"],
                            contact["sourceUrl"],
                            now,
                            now,
                        ),
                    )

                    contact_id = int(
                        cursor.lastrowid
                    )
                else:
                    contact_id = int(
                        existing["id"]
                    )

                connection.execute(
                    """
                    INSERT INTO contact_seed_registry (
                        seed_key,
                        contact_id
                    )
                    VALUES (?, ?)
                    """,
                    (
                        contact["seedKey"],
                        contact_id,
                    ),
                )

    # -----------------------------------------------------
    # DB row → 프론트용 데이터
    # -----------------------------------------------------

    def _row_to_contact(
        self,
        row: Any,
    ) -> dict[str, Any]:

        return {

            "id": _make_contact_id(
                int(
                    row["id"]
                )
            ),

            "group": _clean(
                row[
                    "contact_group"
                ]
            ),

            "organization": _clean(
                row[
                    "organization"
                ]
            ),

            "label": _clean(
                row[
                    "label"
                ]
            ),

            "phone": _clean(
                row[
                    "phone"
                ]
            ),

            "note": _clean(
                row[
                    "note"
                ]
            ),

            "source": _clean(
                row[
                    "source"
                ]
            ),

            "sourceUrl": _clean(
                row[
                    "source_url"
                ]
            ),
        }


    # -----------------------------------------------------
    # 일반 사용자용 연락처 목록
    #
    # 숨김 처리된 연락처는 제외
    # -----------------------------------------------------

    def list_contacts(
        self,
    ) -> list[
        dict[str, Any]
    ]:

        with get_connection() as connection:

            rows = connection.execute(
                """
                SELECT
                    id,
                    contact_group,
                    organization,
                    label,
                    phone,
                    note,
                    source,
                    source_url

                FROM public_contacts

                WHERE is_hidden = 0

                ORDER BY
                    contact_group ASC,
                    organization ASC,
                    label ASC,
                    id ASC
                """
            ).fetchall()


        return [

            self._row_to_contact(
                row
            )

            for row
            in rows
        ]


    # -----------------------------------------------------
    # 프론트 전체 응답용 정보
    # -----------------------------------------------------

    def response_data(
        self,
    ) -> dict[str, Any]:

        return {

            "source": (
                "공식 공개 연락처 및 관리자 관리 공용 전화번호부"
            ),

            "verifiedAt": (
                self.verified_at
            ),

            "notice": (
                self.notice
            ),

            "contacts": (
                self
                .list_contacts()
            ),
        }


    # -----------------------------------------------------
    # 특정 연락처 조회
    # -----------------------------------------------------

    def get_contact(
        self,
        contact_id: str,
    ) -> (
        dict[str, Any]
        | None
    ):

        database_id = (
            _parse_contact_id(
                contact_id
            )
        )


        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT
                    id,
                    contact_group,
                    organization,
                    label,
                    phone,
                    note,
                    source,
                    source_url

                FROM public_contacts

                WHERE
                    id = ?

                AND
                    is_hidden = 0
                """,
                (
                    database_id,
                ),
            ).fetchone()


        if row is None:

            return None


        return (
            self
            ._row_to_contact(
                row
            )
        )


    # -----------------------------------------------------
    # 연락처 추가
    # -----------------------------------------------------

    def create_contact(
        self,
        payload: dict[
            str,
            Any,
        ],
        user_id: int,
    ) -> dict[str, Any]:

        contact_group = _clean(
            payload.get(
                "group"
            )
        )

        organization = _clean(
            payload.get(
                "organization"
            )
        )

        label = _clean(
            payload.get(
                "label"
            )
        )

        phone = _clean(
            payload.get(
                "phone"
            )
        )

        note = _clean(
            payload.get(
                "note"
            )
        )

        source_url = _clean(
            payload.get(
                "sourceUrl"
            )
        )


        if not contact_group:

            raise ValueError(
                "연락처 분류를 입력해 주세요."
            )


        if not organization:

            raise ValueError(
                "기관 또는 부서명을 입력해 주세요."
            )


        if not label:

            raise ValueError(
                "담당 업무를 입력해 주세요."
            )


        if not phone:

            raise ValueError(
                "전화번호를 입력해 주세요."
            )


        now = (
            _now_iso()
        )


        with get_connection() as connection:

            cursor = connection.execute(
                """
                INSERT INTO public_contacts (
                    contact_group,
                    organization,
                    label,
                    phone,
                    note,
                    source,
                    source_url,
                    is_hidden,
                    created_at,
                    updated_at,
                    updated_by
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    contact_group,
                    organization,
                    label,
                    phone,
                    note,
                    CONTACT_SOURCE,
                    source_url,
                    now,
                    now,
                    user_id,
                ),
            )


            database_id = int(
                cursor.lastrowid
            )


        created = (
            self
            .get_contact(
                _make_contact_id(
                    database_id
                )
            )
        )


        if created is None:

            raise RuntimeError(
                "연락처 저장 후 조회에 실패했습니다."
            )


        return created


    # -----------------------------------------------------
    # 연락처 수정
    # -----------------------------------------------------

    def update_contact(
        self,
        contact_id: str,
        payload: dict[
            str,
            Any,
        ],
        user_id: int,
    ) -> dict[str, Any]:

        database_id = (
            _parse_contact_id(
                contact_id
            )
        )


        contact_group = _clean(
            payload.get(
                "group"
            )
        )

        organization = _clean(
            payload.get(
                "organization"
            )
        )

        label = _clean(
            payload.get(
                "label"
            )
        )

        phone = _clean(
            payload.get(
                "phone"
            )
        )

        note = _clean(
            payload.get(
                "note"
            )
        )

        source_url = _clean(
            payload.get(
                "sourceUrl"
            )
        )


        if not contact_group:

            raise ValueError(
                "연락처 분류를 입력해 주세요."
            )


        if not organization:

            raise ValueError(
                "기관 또는 부서명을 입력해 주세요."
            )


        if not label:

            raise ValueError(
                "담당 업무를 입력해 주세요."
            )


        if not phone:

            raise ValueError(
                "전화번호를 입력해 주세요."
            )


        with get_connection() as connection:

            existing = connection.execute(
                """
                SELECT id

                FROM public_contacts

                WHERE
                    id = ?

                AND
                    is_hidden = 0
                """,
                (
                    database_id,
                ),
            ).fetchone()


            if existing is None:

                raise KeyError(
                    contact_id
                )


            connection.execute(
                """
                UPDATE public_contacts

                SET
                    contact_group = ?,
                    organization = ?,
                    label = ?,
                    phone = ?,
                    note = ?,
                    source_url = ?,
                    updated_at = ?,
                    updated_by = ?

                WHERE id = ?
                """,
                (
                    contact_group,
                    organization,
                    label,
                    phone,
                    note,
                    source_url,
                    _now_iso(),
                    user_id,
                    database_id,
                ),
            )


        updated = (
            self
            .get_contact(
                contact_id
            )
        )


        if updated is None:

            raise RuntimeError(
                "연락처 수정 후 조회에 실패했습니다."
            )


        return updated


    # -----------------------------------------------------
    # 연락처 숨김
    #
    # 실제 DB 행을 지우지 않고
    # is_hidden = 1 로 변경합니다.
    #
    # 프론트 관리자 페이지의
    # "전체 사용자 화면에서 숨길까요?"
    # 동작과 맞춘 방식입니다.
    # -----------------------------------------------------

    def hide_contact(
        self,
        contact_id: str,
        user_id: int,
    ) -> None:

        database_id = (
            _parse_contact_id(
                contact_id
            )
        )


        with get_connection() as connection:

            existing = connection.execute(
                """
                SELECT id

                FROM public_contacts

                WHERE
                    id = ?

                AND
                    is_hidden = 0
                """,
                (
                    database_id,
                ),
            ).fetchone()


            if existing is None:

                raise KeyError(
                    contact_id
                )


            connection.execute(
                """
                UPDATE public_contacts

                SET
                    is_hidden = 1,
                    updated_at = ?,
                    updated_by = ?

                WHERE id = ?
                """,
                (
                    _now_iso(),
                    user_id,
                    database_id,
                ),
            )


# ---------------------------------------------------------
# 공통 서비스 객체
# ---------------------------------------------------------

contact_service = (
    ContactService()
)
