from __future__ import annotations

import json
import re

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.database import (
    get_connection,
)


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DATA_DIR = (
    ROOT_DIR
    / "data"
    / "manual"
)

MANUAL_SECTIONS_PATH = (
    DATA_DIR
    / "manual_sections.json"
)

MANUAL_CASES_PATH = (
    DATA_DIR
    / "manual_cases.json"
)


DEFAULT_SOURCE = (
    "당직 근무요령 및 상황별 매뉴얼 "
    "(대전광역시 유성구, 2026.5.)"
)


GROUP_ORDER = [
    "당직근무자 준수사항",
    "청사 보안·시건",
    "비상 발령·소집",
    "재난유형별 대응",
    "민원유형별 대응",
    "부록",
]


MANUAL_EDITABLE_FIELDS = [
    "entryType",
    "group",
    "topic",
    "title",
    "breadcrumb",
    "sourcePages",
    "departments",
    "summary",
    "content",
    "intakeQuestions",
    "immediateActions",
    "decisionBranches",
    "responseScripts",
    "escalationRules",
    "cautions",
]


def _now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )


def _clean(
    value: Any,
) -> str:
    if value is None:
        return ""

    return re.sub(
        r"[ \t]+",
        " ",
        str(value),
    ).strip()


def _string_list(
    value: Any,
) -> list[str]:
    if not isinstance(
        value,
        list,
    ):
        return []

    result: list[str] = []

    for item in value:
        text = _clean(item)

        if (
            text
            and text not in result
        ):
            result.append(text)

    return result


def _int_list(
    value: Any,
) -> list[int]:
    if not isinstance(
        value,
        list,
    ):
        return []

    result: list[int] = []

    for item in value:
        if isinstance(
            item,
            bool,
        ):
            continue

        try:
            number = int(item)

        except (
            TypeError,
            ValueError,
        ):
            continue

        if (
            number >= 0
            and number not in result
        ):
            result.append(number)

    return sorted(result)


def _load_json(
    path: Path,
) -> list[
    dict[str, Any]
]:
    if not path.exists():
        return []

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
        return []

    if not isinstance(
        data,
        list,
    ):
        return []

    return [
        item
        for item in data
        if isinstance(
            item,
            dict,
        )
    ]


def _json_dict(
    value: Any,
) -> dict[str, Any]:
    try:
        parsed = json.loads(
            str(value)
        )

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(
        parsed,
        dict,
    ):
        return {}

    return parsed


class ManualService:
    def __init__(
        self,
    ) -> None:
        self.sections: list[
            dict[str, Any]
        ] = []

        self.cases: list[
            dict[str, Any]
        ] = []

        self.source = (
            DEFAULT_SOURCE
        )

        self.load_error: (
            str
            | None
        ) = None

        self._load()


    # -----------------------------------------------------
    # 원본 JSON 로드
    # -----------------------------------------------------

    def _load(
        self,
    ) -> None:
        errors: list[str] = []

        if not (
            MANUAL_SECTIONS_PATH
            .exists()
        ):
            errors.append(
                "manual_sections.json 파일이 없습니다."
            )

        if not (
            MANUAL_CASES_PATH
            .exists()
        ):
            errors.append(
                "manual_cases.json 파일이 없습니다."
            )

        self.sections = (
            _load_json(
                MANUAL_SECTIONS_PATH
            )
        )

        self.cases = (
            _load_json(
                MANUAL_CASES_PATH
            )
        )

        for item in (
            self.sections
            + self.cases
        ):
            source = _clean(
                item.get(
                    "source"
                )
            )

            if source:
                self.source = source
                break

        self.load_error = (
            " | ".join(errors)
            if errors
            else None
        )


    @property
    def is_ready(
        self,
    ) -> bool:
        return bool(
            self.sections
            or self.cases
            or self._custom_entry_count() > 0
        )


    def _custom_entry_count(
        self,
    ) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM manual_custom_entries
                """
            ).fetchone()

        return (
            int(
                row["count"]
            )
            if row
            else 0
        )


    # -----------------------------------------------------
    # 기존 매뉴얼 분류
    # -----------------------------------------------------

    def _classify_group(
        self,
        item: dict[str, Any],
    ) -> str:
        breadcrumb = (
            _string_list(
                item.get(
                    "breadcrumb"
                )
            )
        )

        classification_text = (
            " ".join(
                [
                    _clean(
                        item.get(
                            "section"
                        )
                    ),
                    _clean(
                        item.get(
                            "title"
                        )
                    ),
                    _clean(
                        item.get(
                            "category"
                        )
                    ),
                    " ".join(
                        breadcrumb
                    ),
                ]
            )
            .lower()
        )

        if any(
            keyword
            in classification_text

            for keyword
            in (
                "재난",
                "태풍",
                "호우",
                "대설",
                "지진",
                "화재",
            )
        ):
            return (
                "재난유형별 대응"
            )

        if any(
            keyword
            in classification_text

            for keyword
            in (
                "민원",
                "주정차",
                "유기동물",
                "소음",
            )
        ):
            return (
                "민원유형별 대응"
            )

        if any(
            keyword
            in classification_text

            for keyword
            in (
                "시건",
                "보안",
                "청사",
                "순찰",
            )
        ):
            return (
                "청사 보안·시건"
            )

        if any(
            keyword
            in classification_text

            for keyword
            in (
                "비상발령",
                "비상 발령",
                "비상소집",
                "비상 소집",
                "비상근무",
            )
        ):
            return (
                "비상 발령·소집"
            )

        if any(
            keyword
            in classification_text

            for keyword
            in (
                "당직",
                "준수사항",
                "타임라인",
            )
        ):
            return (
                "당직근무자 준수사항"
            )

        return "부록"


    # -----------------------------------------------------
    # 일반 section → API 데이터
    # -----------------------------------------------------

    def _section_entry(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        section_title = (
            _clean(
                item.get(
                    "section"
                )
            )
            or "제목 없음"
        )

        breadcrumb = (
            _string_list(
                item.get(
                    "breadcrumb"
                )
            )
        )

        page = item.get(
            "page"
        )

        source_pages = (
            [page]
            if isinstance(
                page,
                int,
            )
            else []
        )

        topic = (
            breadcrumb[-1]
            if breadcrumb
            else section_title
        )

        return {
            "id": (
                _clean(
                    item.get(
                        "id"
                    )
                )
                or
                f"manual_section_{page or 0}"
            ),

            "entryType": (
                "section"
            ),

            "group": (
                self
                ._classify_group(
                    item
                )
            ),

            "topic": topic,

            "title": (
                section_title
            ),

            "breadcrumb": (
                breadcrumb
            ),

            "sourcePages": (
                source_pages
            ),

            "departments": (
                _string_list(
                    item.get(
                        "departments"
                    )
                )
            ),

            "summary": "",

            "content": (
                _clean(
                    item.get(
                        "content"
                    )
                )
            ),

            "intakeQuestions": [],

            "immediateActions": [],

            "decisionBranches": [],

            "responseScripts": [],

            "escalationRules": [],

            "cautions": [],

            "isCustom": False,

            "isModified": False,

            "addedAt": None,

            "updatedAt": None,
        }


    # -----------------------------------------------------
    # case 원문 합치기
    # -----------------------------------------------------

    def _case_content(
        self,
        item: dict[str, Any],
    ) -> str:
        page_items = item.get(
            "content_by_page",
            [],
        )

        if not isinstance(
            page_items,
            list,
        ):
            return ""

        contents: list[str] = []

        for page_item in page_items:
            if not isinstance(
                page_item,
                dict,
            ):
                continue

            text = _clean(
                page_item.get(
                    "text"
                )
            )

            if text:
                contents.append(
                    text
                )

        return "\n\n".join(
            contents
        )


    def _case_pages(
        self,
        item: dict[str, Any],
    ) -> list[int]:
        page_start = item.get(
            "page_start"
        )

        page_end = item.get(
            "page_end"
        )

        if (
            isinstance(
                page_start,
                int,
            )
            and isinstance(
                page_end,
                int,
            )
            and page_end >= page_start
        ):
            return list(
                range(
                    page_start,
                    page_end + 1,
                )
            )

        result: list[int] = []

        page_items = item.get(
            "content_by_page",
            [],
        )

        if isinstance(
            page_items,
            list,
        ):
            for page_item in page_items:
                if not isinstance(
                    page_item,
                    dict,
                ):
                    continue

                page = page_item.get(
                    "page"
                )

                if (
                    isinstance(
                        page,
                        int,
                    )
                    and page not in result
                ):
                    result.append(
                        page
                    )

        return sorted(
            result
        )


    # -----------------------------------------------------
    # 구조화 필드 정리
    # -----------------------------------------------------

    def _decision_branches(
        self,
        value: Any,
    ) -> list[
        dict[str, Any]
    ]:
        if not isinstance(
            value,
            list,
        ):
            return []

        result: list[
            dict[str, Any]
        ] = []

        for item in value:
            if not isinstance(
                item,
                dict,
            ):
                continue

            condition = _clean(
                item.get(
                    "condition"
                )
            )

            actions = (
                _string_list(
                    item.get(
                        "actions"
                    )
                )
            )

            response = _clean(
                item.get(
                    "response"
                )
            )

            if (
                condition
                or actions
                or response
            ):
                result.append(
                    {
                        "condition": condition,
                        "actions": actions,
                        "response": response,
                    }
                )

        return result


    def _escalation_rules(
        self,
        value: Any,
    ) -> list[
        dict[str, str]
    ]:
        if not isinstance(
            value,
            list,
        ):
            return []

        result: list[
            dict[str, str]
        ] = []

        for item in value:
            if not isinstance(
                item,
                dict,
            ):
                continue

            condition = _clean(
                item.get(
                    "condition"
                )
            )

            action = _clean(
                item.get(
                    "action"
                )
            )

            if (
                condition
                or action
            ):
                result.append(
                    {
                        "condition": condition,
                        "action": action,
                    }
                )

        return result


    # -----------------------------------------------------
    # case → API 데이터
    # -----------------------------------------------------

    def _case_entry(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        title = (
            _clean(
                item.get(
                    "title"
                )
            )
            or "제목 없음"
        )

        category = _clean(
            item.get(
                "category"
            )
        )

        breadcrumb = (
            _string_list(
                item.get(
                    "breadcrumb"
                )
            )
        )

        full_content = (
            self
            ._case_content(
                item
            )
        )

        summary = (
            _clean(
                item.get(
                    "summary"
                )
            )
            or full_content
        )

        return {
            "id": (
                _clean(
                    item.get(
                        "id"
                    )
                )
                or
                "manual_case_unknown"
            ),

            "entryType": (
                "case"
            ),

            "group": (
                self
                ._classify_group(
                    item
                )
            ),

            "topic": (
                category
                or (
                    breadcrumb[-1]
                    if breadcrumb
                    else title
                )
            ),

            "title": title,

            "breadcrumb": (
                breadcrumb
            ),

            "sourcePages": (
                self
                ._case_pages(
                    item
                )
            ),

            "departments": (
                _string_list(
                    item.get(
                        "departments"
                    )
                )
            ),

            "summary": (
                summary
            ),

            "content": (
                full_content
            ),

            "intakeQuestions": (
                _string_list(
                    item.get(
                        "intakeQuestions",
                        item.get(
                            "intake_questions",
                            [],
                        ),
                    )
                )
            ),

            "immediateActions": (
                _string_list(
                    item.get(
                        "immediateActions",
                        item.get(
                            "immediate_actions",
                            [],
                        ),
                    )
                )
            ),

            "decisionBranches": (
                self
                ._decision_branches(
                    item.get(
                        "decisionBranches",
                        item.get(
                            "decision_branches",
                            [],
                        ),
                    )
                )
            ),

            "responseScripts": (
                _string_list(
                    item.get(
                        "responseScripts",
                        item.get(
                            "response_scripts",
                            [],
                        ),
                    )
                )
            ),

            "escalationRules": (
                self
                ._escalation_rules(
                    item.get(
                        "escalationRules",
                        item.get(
                            "escalation_rules",
                            [],
                        ),
                    )
                )
            ),

            "cautions": (
                _string_list(
                    item.get(
                        "cautions",
                        [],
                    )
                )
            ),

            "isCustom": False,

            "isModified": False,

            "addedAt": None,

            "updatedAt": None,
        }


    # -----------------------------------------------------
    # 원본 전체 목록
    # -----------------------------------------------------

    def _base_entries(
        self,
    ) -> list[
        dict[str, Any]
    ]:
        entries: list[
            dict[str, Any]
        ] = []

        for item in self.sections:
            entries.append(
                self._section_entry(
                    item
                )
            )

        for item in self.cases:
            entries.append(
                self._case_entry(
                    item
                )
            )

        return entries


    def _base_entry_map(
        self,
    ) -> dict[
        str,
        dict[str, Any],
    ]:
        return {
            str(
                entry["id"]
            ):
            entry

            for entry
            in self._base_entries()
        }


    # -----------------------------------------------------
    # 관리자 데이터 정규화
    # -----------------------------------------------------

    def _normalize_entry(
        self,
        entry: dict[str, Any],
        *,
        entry_id: str,
        is_custom: bool,
        is_modified: bool,
        added_at: str | None,
        updated_at: str | None,
    ) -> dict[str, Any]:
        entry_type = str(
            entry.get(
                "entryType",
                "case",
            )
        )

        if entry_type not in {
            "section",
            "case",
        }:
            entry_type = "case"

        group = (
            _clean(
                entry.get(
                    "group"
                )
            )
            or
            "민원유형별 대응"
        )

        title = (
            _clean(
                entry.get(
                    "title"
                )
            )
            or
            "제목 없음"
        )

        return {
            "id": (
                entry_id
            ),

            "entryType": (
                entry_type
            ),

            "group": (
                group
            ),

            "topic": (
                _clean(
                    entry.get(
                        "topic"
                    )
                )
                or title
            ),

            "title": (
                title
            ),

            "breadcrumb": (
                _string_list(
                    entry.get(
                        "breadcrumb"
                    )
                )
            ),

            "sourcePages": (
                _int_list(
                    entry.get(
                        "sourcePages"
                    )
                )
            ),

            "departments": (
                _string_list(
                    entry.get(
                        "departments"
                    )
                )
            ),

            "summary": (
                _clean(
                    entry.get(
                        "summary"
                    )
                )
            ),

            "content": (
                _clean(
                    entry.get(
                        "content"
                    )
                )
            ),

            "intakeQuestions": (
                _string_list(
                    entry.get(
                        "intakeQuestions"
                    )
                )
            ),

            "immediateActions": (
                _string_list(
                    entry.get(
                        "immediateActions"
                    )
                )
            ),

            "decisionBranches": (
                self
                ._decision_branches(
                    entry.get(
                        "decisionBranches"
                    )
                )
            ),

            "responseScripts": (
                _string_list(
                    entry.get(
                        "responseScripts"
                    )
                )
            ),

            "escalationRules": (
                self
                ._escalation_rules(
                    entry.get(
                        "escalationRules"
                    )
                )
            ),

            "cautions": (
                _string_list(
                    entry.get(
                        "cautions"
                    )
                )
            ),

            "isCustom": (
                is_custom
            ),

            "isModified": (
                is_modified
            ),

            "addedAt": (
                added_at
            ),

            "updatedAt": (
                updated_at
            ),
        }


    # DB에는 화면용 메타데이터를 제외하고 저장
    def _payload_for_storage(
        self,
        entry: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "entryType": (
                entry.get(
                    "entryType",
                    "case",
                )
            ),

            "group": (
                entry.get(
                    "group",
                    "민원유형별 대응",
                )
            ),

            "topic": (
                entry.get(
                    "topic",
                    "",
                )
            ),

            "title": (
                entry.get(
                    "title",
                    "",
                )
            ),

            "breadcrumb": list(
                entry.get(
                    "breadcrumb",
                    [],
                )
            ),

            "sourcePages": list(
                entry.get(
                    "sourcePages",
                    [],
                )
            ),

            "departments": list(
                entry.get(
                    "departments",
                    [],
                )
            ),

            "summary": (
                entry.get(
                    "summary",
                    "",
                )
            ),

            "content": (
                entry.get(
                    "content",
                    "",
                )
            ),

            "intakeQuestions": list(
                entry.get(
                    "intakeQuestions",
                    [],
                )
            ),

            "immediateActions": list(
                entry.get(
                    "immediateActions",
                    [],
                )
            ),

            "decisionBranches": list(
                entry.get(
                    "decisionBranches",
                    [],
                )
            ),

            "responseScripts": list(
                entry.get(
                    "responseScripts",
                    [],
                )
            ),

            "escalationRules": list(
                entry.get(
                    "escalationRules",
                    [],
                )
            ),

            "cautions": list(
                entry.get(
                    "cautions",
                    [],
                )
            ),
        }


    # -----------------------------------------------------
    # DB 읽기
    # -----------------------------------------------------

    def _override_rows(
        self,
    ):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    entry_id,
                    payload_json,
                    created_at,
                    updated_at

                FROM manual_overrides

                ORDER BY updated_at DESC
                """
            ).fetchall()


    def _custom_rows(
        self,
    ):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    entry_id,
                    payload_json,
                    created_at,
                    updated_at

                FROM manual_custom_entries

                ORDER BY created_at ASC
                """
            ).fetchall()


    def modified_entry_ids(
        self,
    ) -> set[str]:
        return {
            str(
                row[
                    "entry_id"
                ]
            )

            for row
            in self._override_rows()
        }


    def has_admin_changes(
        self,
    ) -> bool:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    EXISTS(
                        SELECT 1
                        FROM manual_overrides
                    )
                    OR
                    EXISTS(
                        SELECT 1
                        FROM manual_custom_entries
                    )
                    AS has_changes
                """
            ).fetchone()

        return bool(
            row
            and int(
                row[
                    "has_changes"
                ]
            )
        )


    # -----------------------------------------------------
    # 원본 + 관리자 변경본 + 신규 항목
    # -----------------------------------------------------

    def list_entries(
        self,
    ) -> list[
        dict[str, Any]
    ]:
        base_entries = (
            self
            ._base_entry_map()
        )

        overrides = {
            str(
                row[
                    "entry_id"
                ]
            ):
            row

            for row
            in self._override_rows()
        }

        entries: list[
            dict[str, Any]
        ] = []

        for (
            entry_id,
            base_entry,
        ) in base_entries.items():
            row = overrides.get(
                entry_id
            )

            if row is None:
                entries.append(
                    base_entry
                )
                continue

            payload = (
                _json_dict(
                    row[
                        "payload_json"
                    ]
                )
            )

            merged = {
                **base_entry,
                **payload,
            }

            normalized_entry = self._normalize_entry(
                merged,
                entry_id=entry_id,
                is_custom=False,
                is_modified=True,
                added_at=None,
                updated_at=str(
                    row[
                        "updated_at"
                    ]
                )[:10],
            )

            normalized_entry["changedFields"] = [
                field

                for field
                in MANUAL_EDITABLE_FIELDS

                if normalized_entry.get(field)
                != base_entry.get(field)
            ]

            entries.append(
                normalized_entry
            )

        # 관리자가 직접 추가한 민원
        for row in self._custom_rows():
            entry_id = str(
                row[
                    "entry_id"
                ]
            )

            payload = (
                _json_dict(
                    row[
                        "payload_json"
                    ]
                )
            )

            entries.append(
                self._normalize_entry(
                    payload,
                    entry_id=entry_id,
                    is_custom=True,
                    is_modified=False,
                    added_at=str(
                        row[
                            "created_at"
                        ]
                    )[:10],
                    updated_at=str(
                        row[
                            "updated_at"
                        ]
                    )[:10],
                )
            )

        group_index = {
            group: index

            for (
                index,
                group,
            )
            in enumerate(
                GROUP_ORDER
            )
        }

        def sort_key(
            entry: dict[str, Any],
        ):
            pages = entry.get(
                "sourcePages",
                [],
            )

            first_page = (
                pages[0]
                if pages
                else 9999
            )

            return (
                group_index.get(
                    str(
                        entry.get(
                            "group",
                            "부록",
                        )
                    ),
                    999,
                ),

                first_page,

                str(
                    entry.get(
                        "title",
                        "",
                    )
                ),
            )

        entries.sort(
            key=sort_key
        )

        return entries


    def get_entry(
        self,
        entry_id: str,
    ) -> (
        dict[str, Any]
        | None
    ):
        for entry in (
            self.list_entries()
        ):
            if str(
                entry.get(
                    "id"
                )
            ) == entry_id:
                return entry

        return None


    # -----------------------------------------------------
    # 관리자 신규 민원 추가
    # -----------------------------------------------------

    def create_entry(
        self,
        payload: dict[str, Any],
        user_id: int,
    ) -> dict[str, Any]:
        entry_id = (
            "admin_manual_"
            + uuid4().hex
        )

        now = _now_iso()

        normalized = (
            self._normalize_entry(
                payload,
                entry_id=entry_id,
                is_custom=True,
                is_modified=False,
                added_at=now[:10],
                updated_at=now[:10],
            )
        )

        storage_payload = (
            self
            ._payload_for_storage(
                normalized
            )
        )

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO manual_custom_entries (
                    entry_id,
                    payload_json,
                    created_at,
                    updated_at,
                    updated_by
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entry_id,

                    json.dumps(
                        storage_payload,
                        ensure_ascii=False,
                    ),

                    now,

                    now,

                    user_id,
                ),
            )

        created = (
            self
            .get_entry(
                entry_id
            )
        )

        if created is None:
            raise RuntimeError(
                "추가한 매뉴얼을 다시 불러오지 못했습니다."
            )

        return created


    # -----------------------------------------------------
    # 기존/신규 매뉴얼 수정
    # -----------------------------------------------------

    def update_entry(
        self,
        entry_id: str,
        payload: dict[str, Any],
        user_id: int,
    ) -> dict[str, Any]:
        now = _now_iso()

        # 먼저 관리자 신규 항목인지 확인
        with get_connection() as connection:
            custom_row = (
                connection.execute(
                    """
                    SELECT
                        entry_id,
                        payload_json,
                        created_at,
                        updated_at

                    FROM manual_custom_entries

                    WHERE entry_id = ?
                    """,
                    (
                        entry_id,
                    ),
                )
                .fetchone()
            )

        # 신규 항목 수정
        if custom_row is not None:
            current_payload = (
                _json_dict(
                    custom_row[
                        "payload_json"
                    ]
                )
            )

            merged = {
                **current_payload,
                **payload,
            }

            normalized = (
                self
                ._normalize_entry(
                    merged,
                    entry_id=entry_id,
                    is_custom=True,
                    is_modified=False,
                    added_at=str(
                        custom_row[
                            "created_at"
                        ]
                    )[:10],
                    updated_at=now[:10],
                )
            )

            storage_payload = (
                self
                ._payload_for_storage(
                    normalized
                )
            )

            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE manual_custom_entries

                    SET
                        payload_json = ?,
                        updated_at = ?,
                        updated_by = ?

                    WHERE entry_id = ?
                    """,
                    (
                        json.dumps(
                            storage_payload,
                            ensure_ascii=False,
                        ),

                        now,

                        user_id,

                        entry_id,
                    ),
                )

            updated = (
                self
                .get_entry(
                    entry_id
                )
            )

            if updated is None:
                raise RuntimeError(
                    "수정한 매뉴얼을 다시 불러오지 못했습니다."
                )

            return updated


        # 기존 공식 매뉴얼 항목인지 확인
        base_entry = (
            self
            ._base_entry_map()
            .get(
                entry_id
            )
        )

        if base_entry is None:
            raise KeyError(
                entry_id
            )

        current = (
            self
            .get_entry(
                entry_id
            )
            or base_entry
        )

        merged = {
            **current,
            **payload,
        }

        normalized = (
            self
            ._normalize_entry(
                merged,
                entry_id=entry_id,
                is_custom=False,
                is_modified=True,
                added_at=None,
                updated_at=now[:10],
            )
        )

        storage_payload = (
            self
            ._payload_for_storage(
                normalized
            )
        )

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO manual_overrides (
                    entry_id,
                    payload_json,
                    created_at,
                    updated_at,
                    updated_by
                )

                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT(entry_id)

                DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
                """,
                (
                    entry_id,

                    json.dumps(
                        storage_payload,
                        ensure_ascii=False,
                    ),

                    now,

                    now,

                    user_id,
                ),
            )

        updated = (
            self
            .get_entry(
                entry_id
            )
        )

        if updated is None:
            raise RuntimeError(
                "수정한 매뉴얼을 다시 불러오지 못했습니다."
            )

        return updated


    # -----------------------------------------------------
    # 기존 항목 → 원본 복구
    # 관리자 신규 항목 → 삭제
    # -----------------------------------------------------

    def delete_or_restore(
        self,
        entry_id: str,
    ) -> str:
        with get_connection() as connection:
            custom_row = (
                connection.execute(
                    """
                    SELECT entry_id

                    FROM manual_custom_entries

                    WHERE entry_id = ?
                    """,
                    (
                        entry_id,
                    ),
                )
                .fetchone()
            )

            if custom_row is not None:
                connection.execute(
                    """
                    DELETE FROM manual_custom_entries

                    WHERE entry_id = ?
                    """,
                    (
                        entry_id,
                    ),
                )

                return "deleted"

        base_entry = (
            self
            ._base_entry_map()
            .get(
                entry_id
            )
        )

        if base_entry is None:
            raise KeyError(
                entry_id
            )

        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM manual_overrides

                WHERE entry_id = ?
                """,
                (
                    entry_id,
                ),
            )

        return "restored"


    # -----------------------------------------------------
    # 검색용: 관리자 수정/추가 항목만 가져오기
    # -----------------------------------------------------

    def _changed_entries(
        self,
    ) -> list[
        dict[str, Any]
    ]:
        changed_ids = (
            self
            .modified_entry_ids()
        )

        return [
            entry

            for entry
            in self.list_entries()

            if (
                str(
                    entry.get(
                        "id"
                    )
                )
                in changed_ids

                or

                bool(
                    entry.get(
                        "isCustom"
                    )
                )
            )
        ]


    def _searchable_text(
        self,
        entry: dict[str, Any],
    ) -> str:
        branch_text: list[str] = []

        for branch in entry.get(
            "decisionBranches",
            [],
        ):
            if not isinstance(
                branch,
                dict,
            ):
                continue

            branch_text.append(
                _clean(
                    branch.get(
                        "condition"
                    )
                )
            )

            branch_text.extend(
                _string_list(
                    branch.get(
                        "actions"
                    )
                )
            )

            branch_text.append(
                _clean(
                    branch.get(
                        "response"
                    )
                )
            )

        escalation_text: list[str] = []

        for rule in entry.get(
            "escalationRules",
            [],
        ):
            if not isinstance(
                rule,
                dict,
            ):
                continue

            escalation_text.append(
                _clean(
                    rule.get(
                        "condition"
                    )
                )
            )

            escalation_text.append(
                _clean(
                    rule.get(
                        "action"
                    )
                )
            )

        values = [
            _clean(
                entry.get(
                    "title"
                )
            ),

            _clean(
                entry.get(
                    "topic"
                )
            ),

            _clean(
                entry.get(
                    "group"
                )
            ),

            _clean(
                entry.get(
                    "summary"
                )
            ),

            _clean(
                entry.get(
                    "content"
                )
            ),

            " ".join(
                _string_list(
                    entry.get(
                        "departments"
                    )
                )
            ),

            " ".join(
                _string_list(
                    entry.get(
                        "intakeQuestions"
                    )
                )
            ),

            " ".join(
                _string_list(
                    entry.get(
                        "immediateActions"
                    )
                )
            ),

            " ".join(
                _string_list(
                    entry.get(
                        "responseScripts"
                    )
                )
            ),

            " ".join(
                _string_list(
                    entry.get(
                        "cautions"
                    )
                )
            ),

            " ".join(
                branch_text
            ),

            " ".join(
                escalation_text
            ),
        ]

        return " ".join(
            value

            for value
            in values

            if value
        )


    # 관리자 데이터는 별도의 검색 인덱스를
    # 다시 만들 필요 없이 즉시 검색에 반영
    def _search_score(
        self,
        query: str,
        entry: dict[str, Any],
    ) -> float:
        query_clean = re.sub(
            r"\s+",
            "",
            query.lower(),
        )

        if not query_clean:
            return 0.0

        title = re.sub(
            r"\s+",
            "",
            _clean(
                entry.get(
                    "title"
                )
            ).lower(),
        )

        topic = re.sub(
            r"\s+",
            "",
            _clean(
                entry.get(
                    "topic"
                )
            ).lower(),
        )

        text = re.sub(
            r"\s+",
            "",
            self
            ._searchable_text(
                entry
            )
            .lower(),
        )

        score = 0.0

        if query_clean in title:
            score += 30.0

        elif query_clean in topic:
            score += 20.0

        elif query_clean in text:
            score += 12.0

        terms = re.findall(
            r"[가-힣A-Za-z0-9]{2,}",
            query.lower(),
        )

        for term in terms:
            compact = re.sub(
                r"\s+",
                "",
                term,
            )

            if compact in title:
                score += 12.0

            elif compact in topic:
                score += 8.0

            elif compact in text:
                score += 4.0

        # 한국어 조사 때문에
        # "킥보드가" / "킥보드"처럼 달라져도
        # 잡을 수 있도록 문자 바이그램 보조
        query_bigrams = {
            query_clean[
                index:
                index + 2
            ]

            for index
            in range(
                max(
                    0,
                    len(
                        query_clean
                    )
                    - 1,
                )
            )
        }

        text_bigrams = {
            text[
                index:
                index + 2
            ]

            for index
            in range(
                max(
                    0,
                    len(
                        text
                    )
                    - 1,
                )
            )
        }

        if query_bigrams:
            overlap = len(
                query_bigrams
                & text_bigrams
            )

            ratio = (
                overlap
                / len(
                    query_bigrams
                )
            )

            score += (
                overlap * 0.8
                + ratio * 10.0
            )

        return score


    def search_admin_changes(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[
        dict[str, Any]
    ]:
        scored: list[
            tuple[
                float,
                dict[str, Any],
            ]
        ] = []

        for entry in (
            self
            ._changed_entries()
        ):
            score = (
                self
                ._search_score(
                    query,
                    entry,
                )
            )

            if score <= 0:
                continue

            scored.append(
                (
                    score,
                    entry,
                )
            )

        scored.sort(
            key=lambda item: (
                item[0]
            ),
            reverse=True,
        )

        return [
            {
                "score": score,
                "entry": entry,
            }

            for (
                score,
                entry,
            )
            in scored[
                :top_k
            ]
        ]


    # -----------------------------------------------------
    # API 응답
    # -----------------------------------------------------

    def response_data(
        self,
    ) -> dict[str, Any]:
        entries = (
            self
            .list_entries()
        )

        return {
            "source": (
                self.source
            ),

            "totalCount": len(
                entries
            ),

            "entries": (
                entries
            ),
        }


manual_service = (
    ManualService()
)
