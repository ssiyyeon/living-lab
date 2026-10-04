from __future__ import annotations

import json
import re

from datetime import (
    date,
    datetime,
    timezone,
)

from pathlib import Path
from typing import Any

from backend.database import (
    get_connection,
)


# ---------------------------------------------------------
# 프로젝트 경로
# ---------------------------------------------------------

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)


# 데이터팀의 기존 매뉴얼 데이터
MANUAL_SECTIONS_PATH = (
    ROOT_DIR
    / "data"
    / "manual"
    / "manual_sections.json"
)

QUICK_GUIDES_PATH = (
    ROOT_DIR
    / "data"
    / "manual"
    / "quick_guides.json"
)


SOURCE_NAME = (
    "당직 근무요령 및 상황별 매뉴얼"
)


# ---------------------------------------------------------
# 관리자 화면에서 보여줄 업무 안내 종류
#
# 프론트에서는 서버에서 받은 guide 목록을 그대로 사용하므로
# 여기의 id를 기준으로 저장/수정하게 됩니다.
# ---------------------------------------------------------

GUIDE_CONFIG = {

    "duty_timeline": {
        "title": "근무 타임라인",

        "description": (
            "시간대별 당직 근무 확인 사항입니다."
        ),

        "matcher": "timeline",
    },

    "duty_log": {
        "title": "당직근무일지 작성",

        "description": (
            "근무 시작 시 당직보고를 만들고, 종료 전 상세현황과 순찰점검을 완성합니다."
        ),

        "matcher": "duty_log",
    },

    "complaint_registration": {
        "title": "당직민원 등록",

        "description": (
            "접수한 민원을 누락 없이 기록하고 처리부서를 지정하는 방법입니다."
        ),

        "matcher": "complaint_registration",
    },

    "duty_basics": {
        "title": "당직 기본업무",

        "description": (
            "당직근무 중 기본적으로 확인할 업무입니다."
        ),

        "matcher": "basics",
    },

    "disaster_response": {
        "title": "재난·비상 대응",

        "description": (
            "재난 및 비상 상황에서 확인할 대응 절차입니다."
        ),

        "matcher": "disaster",
    },

    "emergency_contacts": {
        "title": "긴급 연락망",

        "description": (
            "당직 중 필요한 연락 및 보고 관련 안내입니다."
        ),

        "matcher": "contacts",
    },
}


# ---------------------------------------------------------
# 시간 관련 함수
# ---------------------------------------------------------

def _now_iso() -> str:
    """
    DB에 저장할 현재 시간
    """

    return datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )


def _today() -> str:
    """
    화면에 표시할 추가 날짜
    예: 2026-10-04
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
    여러 줄 공백 등을 한 칸으로 정리
    """

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def _normalize_section(
    section: dict[str, Any],
) -> dict[str, Any]:
    """
    프론트에서 받은 처리 단계 데이터를
    일정한 형식으로 정리
    """

    return {

        "title": _clean(
            section.get(
                "title",
                "",
            )
        ),

        "timeLabel": _clean(
            section.get(
                "timeLabel",
                "",
            )
        ),

        "steps": [
            _clean(step)

            for step
            in section.get(
                "steps",
                [],
            )

            if _clean(step)
        ],
    }


# ---------------------------------------------------------
# GuideService
# ---------------------------------------------------------

class GuideService:

    @property
    def source(
        self,
    ) -> str:

        return SOURCE_NAME


    # -----------------------------------------------------
    # 기존 데이터팀 매뉴얼 읽기
    # -----------------------------------------------------

    def _load_manual_sections(
        self,
    ) -> list[
        dict[str, Any]
    ]:

        # 아직 feature/data가 합쳐지지 않았다면
        # 파일이 없을 수 있으므로 빈 목록 반환
        if not (
            MANUAL_SECTIONS_PATH
            .exists()
        ):
            return []

        try:

            with (
                MANUAL_SECTIONS_PATH
                .open(
                    "r",
                    encoding="utf-8",
                )
            ) as file:

                data = json.load(
                    file
                )

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

            for item
            in data

            if isinstance(
                item,
                dict,
            )
        ]


    # -----------------------------------------------------
    # 기존 프론트에서 사용하던 빠른 업무 안내 읽기
    #
    # 정리된 제목, 시간대, 주의사항을 그대로 기본값으로 사용하고
    # 관리자가 수정한 경우에는 DB의 수정본을 우선합니다.
    # -----------------------------------------------------

    def _load_quick_guides(
        self,
    ) -> dict[str, dict[str, Any]]:

        if not QUICK_GUIDES_PATH.exists():
            return {}

        try:
            with QUICK_GUIDES_PATH.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        if not isinstance(data, dict):
            return {}

        guides = data.get("guides", [])

        if not isinstance(guides, list):
            return {}

        return {
            str(guide["id"]): guide
            for guide in guides
            if isinstance(guide, dict) and guide.get("id")
        }


    # -----------------------------------------------------
    # 매뉴얼 항목 분류
    # -----------------------------------------------------

    def _matches(
        self,
        item: dict[
            str,
            Any,
        ],
        matcher: str,
    ) -> bool:

        breadcrumb = (
            item.get(
                "breadcrumb",
                [],
            )
            or []
        )

        text = " ".join(
            [
                str(
                    item.get(
                        "section",
                        "",
                    )
                ),

                " ".join(
                    str(value)

                    for value
                    in breadcrumb
                ),

                str(
                    item.get(
                        "content",
                        "",
                    )
                )[:700],
            ]
        )


        if matcher == "timeline":

            return (
                "타임라인"
                in text
            )


        if matcher == "basics":

            return (
                "당직근무자 준수사항"
                in text

                or

                "당직근무 시 준수사항"
                in text
            )


        if matcher == "disaster":

            return (
                "재난"
                in text

                or

                "비상"
                in text
            )


        if matcher == "contacts":

            return (
                "연락망"
                in text

                or

                "연락처"
                in text
            )


        return False


    # -----------------------------------------------------
    # 원문을 처리 단계 목록으로 변환
    # -----------------------------------------------------

    def _steps_from_content(
        self,
        item: dict[
            str,
            Any,
        ],
    ) -> list[str]:

        content = str(
            item.get(
                "content",
                "",
            )
        )

        section_title = _clean(
            item.get(
                "section",
                "",
            )
        )

        result: list[str] = []


        for raw_line in (
            content
            .splitlines()
        ):

            line = _clean(
                raw_line
            )


            if not line:
                continue


            if (
                line
                == section_title
            ):
                continue


            # PDF 페이지 번호 같은 값 제외
            if re.fullmatch(
                r"-?\s*\d+\s*-?",
                line,
            ):
                continue


            if line not in result:

                result.append(
                    line
                )


            # 지나치게 길어지지 않도록 제한
            if len(result) >= 15:
                break


        return result


    # -----------------------------------------------------
    # 기존 매뉴얼 → 기본 guide 생성
    # -----------------------------------------------------

    def _base_guides(
        self,
    ) -> dict[
        str,
        dict[str, Any],
    ]:

        manual_sections = (
            self
            ._load_manual_sections()
        )

        quick_guides = (
            self
            ._load_quick_guides()
        )

        result: dict[
            str,
            dict[str, Any],
        ] = {}


        for (
            guide_id,
            config,
        ) in (
            GUIDE_CONFIG
            .items()
        ):

            curated = quick_guides.get(
                guide_id
            )

            if curated is not None:

                sections = []

                for section in curated.get(
                    "sections",
                    [],
                ):

                    if not isinstance(
                        section,
                        dict,
                    ):
                        continue

                    normalized = _normalize_section(
                        section
                    )

                    normalized["addedAt"] = None

                    sections.append(
                        normalized
                    )

                result[guide_id] = {
                    "id": guide_id,
                    "title": _clean(
                        curated.get(
                            "title",
                            config["title"],
                        )
                    ),
                    "description": _clean(
                        curated.get(
                            "description",
                            config["description"],
                        )
                    ),
                    "sourcePages": [
                        page
                        for page in curated.get(
                            "sourcePages",
                            [],
                        )
                        if isinstance(page, int)
                    ],
                    "sections": sections,
                    "cautions": [
                        _clean(value)
                        for value in curated.get(
                            "cautions",
                            [],
                        )
                        if _clean(value)
                    ],
                    "contacts": [
                        contact
                        for contact in curated.get(
                            "contacts",
                            [],
                        )
                        if isinstance(contact, dict)
                    ],
                    "restrictedNotice": (
                        _clean(
                            curated.get(
                                "restrictedNotice",
                                "",
                            )
                        )
                        or None
                    ),
                    "updatedAt": None,
                }

                continue

            selected = [

                item

                for item
                in manual_sections

                if self._matches(
                    item,
                    str(
                        config[
                            "matcher"
                        ]
                    ),
                )

            ][:6]


            sections = []

            source_pages: list[int] = []


            for item in selected:

                page = item.get(
                    "page"
                )


                if isinstance(
                    page,
                    int,
                ):

                    source_pages.append(
                        page
                    )


                title = (
                    _clean(
                        item.get(
                            "section",
                            "",
                        )
                    )

                    or

                    str(
                        config[
                            "title"
                        ]
                    )
                )


                sections.append(
                    {

                        "title": title,

                        "timeLabel": (
                            f"{page}쪽"

                            if isinstance(
                                page,
                                int,
                            )

                            else ""
                        ),

                        "steps": (
                            self
                            ._steps_from_content(
                                item
                            )
                        ),

                        # 기존 매뉴얼은
                        # 새로 추가된 내용이 아니므로 날짜 없음
                        "addedAt": None,
                    }
                )


            result[
                guide_id
            ] = {

                "id": guide_id,

                "title": str(
                    config[
                        "title"
                    ]
                ),

                "description": str(
                    config[
                        "description"
                    ]
                ),

                "sourcePages": (
                    sorted(
                        set(
                            source_pages
                        )
                    )
                ),

                "sections": sections,

                "cautions": [],

                "contacts": [],

                "restrictedNotice": None,

                "updatedAt": None,
            }


        return result


    # -----------------------------------------------------
    # DB에 저장된 관리자 수정 내용 조회
    # -----------------------------------------------------

    def _override_row(
        self,
        guide_id: str,
    ):

        with get_connection() as connection:

            return connection.execute(
                """
                SELECT
                    guide_id,
                    title,
                    description,
                    sections_json,
                    cautions_json,
                    created_at,
                    updated_at

                FROM guide_overrides

                WHERE guide_id = ?
                """,
                (
                    guide_id,
                ),
            ).fetchone()


    # -----------------------------------------------------
    # 관리자가 추가한 단계의 날짜 조회
    # -----------------------------------------------------

    def _section_dates(
        self,
        guide_id: str,
    ) -> dict[int, str]:

        with get_connection() as connection:

            rows = connection.execute(
                """
                SELECT
                    section_index,
                    added_at

                FROM guide_section_metadata

                WHERE guide_id = ?
                """,
                (
                    guide_id,
                ),
            ).fetchall()


        return {

            int(
                row[
                    "section_index"
                ]
            ):
            str(
                row[
                    "added_at"
                ]
            )

            for row
            in rows
        }


    # -----------------------------------------------------
    # 실제 화면에 보여줄 하나의 guide 반환
    #
    # 관리자 수정본이 있으면 수정본 사용
    # 없으면 원래 매뉴얼 사용
    # -----------------------------------------------------

    def get_guide(
        self,
        guide_id: str,
    ) -> (
        dict[str, Any]
        | None
    ):

        base = (
            self
            ._base_guides()
            .get(
                guide_id
            )
        )


        if base is None:
            return None


        row = self._override_row(
            guide_id
        )


        # 관리자가 아직 수정하지 않았다면
        # 기존 매뉴얼 그대로 반환
        if row is None:

            return base


        try:

            sections = json.loads(
                str(
                    row[
                        "sections_json"
                    ]
                )
            )

            cautions = json.loads(
                str(
                    row[
                        "cautions_json"
                    ]
                )
            )

        except json.JSONDecodeError:

            sections = []

            cautions = []


        if not isinstance(
            sections,
            list,
        ):
            sections = []


        if not isinstance(
            cautions,
            list,
        ):
            cautions = []


        added_dates = (
            self
            ._section_dates(
                guide_id
            )
        )


        normalized_sections = []


        for (
            index,
            section,
        ) in enumerate(
            sections
        ):

            if not isinstance(
                section,
                dict,
            ):
                continue


            normalized = (
                _normalize_section(
                    section
                )
            )


            # 새로 추가한 단계이면
            # 추가 날짜 붙이기
            normalized[
                "addedAt"
            ] = (
                added_dates
                .get(
                    index
                )
            )


            normalized_sections.append(
                normalized
            )


        return {

            **base,

            "title": str(
                row[
                    "title"
                ]
            ),

            "description": str(
                row[
                    "description"
                ]
            ),

            "sections": (
                normalized_sections
            ),

            "cautions": [

                _clean(value)

                for value
                in cautions

                if _clean(value)
            ],

            "updatedAt": str(
                row[
                    "updated_at"
                ]
            )[:10],
        }


    # -----------------------------------------------------
    # 모든 guide 조회
    # -----------------------------------------------------

    def list_guides(
        self,
    ) -> list[
        dict[str, Any]
    ]:

        result = []


        for guide_id in (
            GUIDE_CONFIG
        ):

            guide = (
                self
                .get_guide(
                    guide_id
                )
            )


            if guide is not None:

                result.append(
                    guide
                )


        return result


    # -----------------------------------------------------
    # 관리자가 수정한 내용 저장
    # -----------------------------------------------------

    def save_guide(
        self,
        guide_id: str,
        payload: dict[
            str,
            Any,
        ],
        user_id: int,
    ) -> dict[str, Any]:

        base = (
            self
            ._base_guides()
            .get(
                guide_id
            )
        )


        if base is None:

            raise KeyError(
                guide_id
            )


        # 프론트에서 받은 처리 단계 정리
        sections = [

            _normalize_section(
                section
            )

            for section
            in payload.get(
                "sections",
                [],
            )

            if isinstance(
                section,
                dict,
            )
        ]


        cautions = [

            _clean(value)

            for value
            in payload.get(
                "cautions",
                [],
            )

            if _clean(value)
        ]


        title = _clean(
            payload.get(
                "title",
                "",
            )
        )


        description = _clean(
            payload.get(
                "description",
                "",
            )
        )


        now = _now_iso()


        # 기존 원본 단계 개수
        base_section_count = len(
            base.get(
                "sections",
                [],
            )
        )


        with get_connection() as connection:

            existing = connection.execute(
                """
                SELECT created_at

                FROM guide_overrides

                WHERE guide_id = ?
                """,
                (
                    guide_id,
                ),
            ).fetchone()


            created_at = (

                str(
                    existing[
                        "created_at"
                    ]
                )

                if existing is not None

                else now
            )


            # 수정된 안내 내용 저장
            connection.execute(
                """
                INSERT INTO guide_overrides (
                    guide_id,
                    title,
                    description,
                    sections_json,
                    cautions_json,
                    created_at,
                    updated_at,
                    updated_by
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(guide_id)

                DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    sections_json = excluded.sections_json,
                    cautions_json = excluded.cautions_json,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
                """,
                (
                    guide_id,

                    title,

                    description,

                    json.dumps(
                        sections,
                        ensure_ascii=False,
                    ),

                    json.dumps(
                        cautions,
                        ensure_ascii=False,
                    ),

                    created_at,

                    now,

                    user_id,
                ),
            )


            # 기존에 저장되어 있던
            # 새 단계 날짜 불러오기
            previous_dates = {

                int(
                    row[
                        "section_index"
                    ]
                ):
                str(
                    row[
                        "added_at"
                    ]
                )

                for row
                in connection.execute(
                    """
                    SELECT
                        section_index,
                        added_at

                    FROM guide_section_metadata

                    WHERE guide_id = ?
                    """,
                    (
                        guide_id,
                    ),
                ).fetchall()
            }


            # 메타데이터를 다시 정리
            connection.execute(
                """
                DELETE FROM guide_section_metadata

                WHERE guide_id = ?
                """,
                (
                    guide_id,
                ),
            )


            # 기존 원본 단계 개수를 넘는 부분은
            # 관리자가 새로 추가한 단계로 판단
            for index in range(
                len(
                    sections
                )
            ):

                if (
                    index
                    < base_section_count
                ):
                    continue


                # 이미 존재했던 추가 단계라면
                # 원래 추가 날짜 유지
                added_at = (
                    previous_dates
                    .get(
                        index,
                        _today(),
                    )
                )


                connection.execute(
                    """
                    INSERT INTO guide_section_metadata (
                        guide_id,
                        section_index,
                        added_at
                    )

                    VALUES (?, ?, ?)
                    """,
                    (
                        guide_id,
                        index,
                        added_at,
                    ),
                )


        saved = (
            self
            .get_guide(
                guide_id
            )
        )


        if saved is None:

            raise KeyError(
                guide_id
            )


        return saved


    # -----------------------------------------------------
    # "원본으로 되돌리기"
    #
    # 관리자 수정 내용을 삭제하고
    # 기존 데이터팀 매뉴얼로 복구
    # -----------------------------------------------------

    def reset_guide(
        self,
        guide_id: str,
    ) -> None:

        if guide_id not in (
            GUIDE_CONFIG
        ):

            raise KeyError(
                guide_id
            )


        with get_connection() as connection:

            connection.execute(
                """
                DELETE FROM guide_section_metadata

                WHERE guide_id = ?
                """,
                (
                    guide_id,
                ),
            )


            connection.execute(
                """
                DELETE FROM guide_overrides

                WHERE guide_id = ?
                """,
                (
                    guide_id,
                ),
            )


    # -----------------------------------------------------
    # 관리자 수정 데이터가 하나라도 있는지 확인
    # -----------------------------------------------------

    def has_overrides(
        self,
    ) -> bool:

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count

                FROM guide_overrides
                """
            ).fetchone()


        return (
            int(
                row[
                    "count"
                ]
            )
            > 0
        )


    # -----------------------------------------------------
    # 검색용 2글자 단위 문자열 생성
    #
    # 예:
    # 킥보드
    # → 킥, 킥보, 보드
    #
    # 문장 검색에서도 핵심 단어를 조금 더 잘 찾기 위함
    # -----------------------------------------------------

    def _bigrams(
        self,
        text: str,
    ) -> set[str]:

        chunks = re.findall(
            r"[가-힣A-Za-z0-9]{2,}",
            text.lower(),
        )


        result: set[str] = set()


        for chunk in chunks:

            if len(chunk) == 2:

                result.add(
                    chunk
                )

                continue


            for index in range(
                len(chunk) - 1
            ):

                result.add(
                    chunk[
                        index:
                        index + 2
                    ]
                )


        return result


    # -----------------------------------------------------
    # 간단한 조사 제거
    #
    # "킥보드가" → "킥보드"
    # -----------------------------------------------------

    def _keyword_variants(
        self,
        value: str,
    ) -> set[str]:

        value = (
            value
            .lower()
        )


        result = {
            value
        }


        suffixes = [
            "에서",
            "으로",
            "에게",
            "한테",
            "까지",
            "부터",
            "라고",
            "이고",
            "이면",
            "가",
            "이",
            "은",
            "는",
            "을",
            "를",
            "에",
            "도",
            "와",
            "과",
        ]


        for suffix in suffixes:

            if (
                value.endswith(
                    suffix
                )

                and

                len(value)
                - len(suffix)
                >= 2
            ):

                result.add(
                    value[
                        :-len(
                            suffix
                        )
                    ]
                )


        return result


    # -----------------------------------------------------
    # 관리자 수정 내용을 검색할 때 사용하는 점수
    # -----------------------------------------------------

    def _score(
        self,
        query: str,
        text: str,
    ) -> float:

        query_clean = (
            _clean(
                query
            )
            .lower()
        )


        text_clean = (
            _clean(
                text
            )
            .lower()
        )


        if (
            not query_clean
            or
            not text_clean
        ):
            return 0.0


        score = 0.0


        compact_query = (
            query_clean
            .replace(
                " ",
                "",
            )
        )


        compact_text = (
            text_clean
            .replace(
                " ",
                "",
            )
        )


        # 검색 문장이 그대로 포함되어 있으면 높은 점수
        if (
            len(
                compact_query
            )
            >= 2

            and

            compact_query
            in compact_text
        ):

            score += 120.0


        # 검색어 안의 핵심 단어 확인
        query_terms = re.findall(
            r"[가-힣A-Za-z0-9]{2,}",
            query_clean,
        )


        for term in query_terms:

            for variant in (
                self
                ._keyword_variants(
                    term
                )
            ):

                if (
                    variant
                    in text_clean
                ):

                    score += 45.0

                    break


        # 문장 전체가 정확히 같지 않아도
        # 비슷한 글자 조합이 있으면 일부 점수 부여
        query_grams = (
            self
            ._bigrams(
                query_clean
            )
        )


        text_grams = (
            self
            ._bigrams(
                text_clean
            )
        )


        overlap = (
            query_grams
            & text_grams
        )


        if len(overlap) >= 2:

            ratio = (
                len(
                    overlap
                )
                /
                max(
                    1,
                    len(
                        query_grams
                    ),
                )
            )


            score += (
                ratio
                * 80.0
            )


        return score


    # -----------------------------------------------------
    # 관리자 수정/추가 내용 검색
    # -----------------------------------------------------

    def search_overrides(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[
        dict[str, Any]
    ]:

        # 관리자가 아직 한 번도 수정하지 않았다면
        # 검색할 DB 데이터가 없음
        if not (
            self
            .has_overrides()
        ):

            return []


        base_guides = (
            self
            ._base_guides()
        )


        matches = []


        for guide in (
            self
            .list_guides()
        ):

            # DB 수정본이 없는 가이드는 건너뜀
            if not guide.get(
                "updatedAt"
            ):
                continue


            base = (
                base_guides
                .get(
                    guide[
                        "id"
                    ],
                    {},
                )
            )


            base_sections = (
                base.get(
                    "sections",
                    []
                )
            )


            # 제목 / 설명 / 주의사항 자체가
            # 변경됐는지 확인
            general_changed = (

                guide.get(
                    "title"
                )
                !=
                base.get(
                    "title"
                )

                or

                guide.get(
                    "description"
                )
                !=
                base.get(
                    "description"
                )

                or

                guide.get(
                    "cautions"
                )
                !=
                base.get(
                    "cautions"
                )
            )


            for (
                index,
                section,
            ) in enumerate(
                guide.get(
                    "sections",
                    [],
                )
            ):

                if not isinstance(
                    section,
                    dict,
                ):
                    continue


                normalized = (
                    _normalize_section(
                        section
                    )
                )


                # 원래 없던 단계이면 새 단계
                changed = (
                    index
                    >= len(
                        base_sections
                    )
                )


                # 기존 단계지만 내용이 달라진 경우
                if (
                    not changed

                    and

                    index
                    < len(
                        base_sections
                    )
                ):

                    changed = (
                        normalized
                        !=
                        _normalize_section(
                            base_sections[
                                index
                            ]
                        )
                    )


                # 변경된 내용이 아니면
                # 기존 search.engine이 검색하므로
                # 여기서는 중복 검색하지 않음
                if (
                    not changed

                    and

                    not general_changed
                ):
                    continue


                # -----------------------------------------
                # 검색할 때만 여러 필드를 합쳐봄
                #
                # DB에 이렇게 저장하는 것은 아님
                # -----------------------------------------

                searchable_text = (
                    " ".join(
                        [

                            str(
                                guide.get(
                                    "title",
                                    "",
                                )
                            ),

                            str(
                                guide.get(
                                    "description",
                                    "",
                                )
                            ),

                            str(
                                section.get(
                                    "title",
                                    "",
                                )
                            ),

                            str(
                                section.get(
                                    "timeLabel",
                                    "",
                                )
                            ),

                            " ".join(
                                str(step)

                                for step
                                in section.get(
                                    "steps",
                                    [],
                                )
                            ),

                            " ".join(
                                str(caution)

                                for caution
                                in guide.get(
                                    "cautions",
                                    [],
                                )
                            ),
                        ]
                    )
                )


                score = (
                    self
                    ._score(
                        query,
                        searchable_text,
                    )
                )


                if score < 35:
                    continue


                matches.append(
                    {

                        "guide": guide,

                        "section": section,

                        "sectionIndex": (
                            index
                        ),

                        "score": score,
                    }
                )


        # 관련도 높은 순
        matches.sort(
            key=lambda item: (
                float(
                    item[
                        "score"
                    ]
                )
            ),
            reverse=True,
        )


        return (
            matches[
                :top_k
            ]
        )


# 다른 파일에서 공통으로 사용할 객체
guide_service = (
    GuideService()
)
