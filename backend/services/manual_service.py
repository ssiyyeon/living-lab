from __future__ import annotations

import json
import re

from pathlib import Path
from typing import Any


# ---------------------------------------------------------
# 경로
# ---------------------------------------------------------

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


# 프론트 ManualCatalogView의 분류와 맞춤
GROUP_ORDER = [
    "당직근무자 준수사항",
    "청사 보안·시건",
    "비상 발령·소집",
    "재난유형별 대응",
    "민원유형별 대응",
    "부록",
]


# ---------------------------------------------------------
# 공통 함수
# ---------------------------------------------------------

def _clean(
    value: Any,
) -> str:
    """
    문자열 앞뒤 공백과 불필요한 연속 공백 정리
    """

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
    """
    JSON 값이 문자열 리스트일 경우 안전하게 정리
    """

    if not isinstance(
        value,
        list,
    ):
        return []

    result: list[str] = []

    for item in value:

        text = _clean(
            item
        )

        if (
            text
            and
            text not in result
        ):

            result.append(
                text
            )

    return result


def _load_json(
    path: Path,
) -> list[dict[str, Any]]:
    """
    JSON 파일을 읽습니다.
    """

    if not path.exists():
        return []

    try:

        with path.open(
            "r",
            encoding="utf-8",
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
        for item in data
        if isinstance(
            item,
            dict,
        )
    ]


# ---------------------------------------------------------
# 전체 매뉴얼 서비스
# ---------------------------------------------------------

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
    # 데이터 로드
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


        # 데이터에 기록된 실제 출처가 있으면 사용
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


        if errors:

            self.load_error = (
                " | ".join(
                    errors
                )
            )

        else:

            self.load_error = None


    # -----------------------------------------------------
    # 준비 상태
    # -----------------------------------------------------

    @property
    def is_ready(
        self,
    ) -> bool:

        return bool(
            self.sections
            or
            self.cases
        )


    # -----------------------------------------------------
    # 매뉴얼 분류
    #
    # 프론트의 GROUP_ORDER와 맞춤
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


        # 재난 관련
        if (
            "재난" in classification_text
            or
            "태풍" in classification_text
            or
            "호우" in classification_text
            or
            "대설" in classification_text
            or
            "지진" in classification_text
            or
            "화재" in classification_text
        ):

            return (
                "재난유형별 대응"
            )


        # 민원 관련
        if (
            "민원" in classification_text
            or
            "주정차" in classification_text
            or
            "유기동물" in classification_text
            or
            "소음" in classification_text
        ):

            return (
                "민원유형별 대응"
            )


        # 청사 보안
        if (
            "시건" in classification_text
            or
            "보안" in classification_text
            or
            "청사" in classification_text
            or
            "순찰" in classification_text
        ):

            return (
                "청사 보안·시건"
            )


        # 비상 발령 / 소집
        if (
            "비상발령"
            in classification_text

            or

            "비상 발령"
            in classification_text

            or

            "비상소집"
            in classification_text

            or

            "비상 소집"
            in classification_text

            or

            "비상근무"
            in classification_text
        ):

            return (
                "비상 발령·소집"
            )


        # 일반 당직 업무
        if (
            "당직" in classification_text
            or
            "준수사항"
            in classification_text
            or
            "타임라인"
            in classification_text
        ):

            return (
                "당직근무자 준수사항"
            )


        return "부록"


    # -----------------------------------------------------
    # section 데이터 → 전체 매뉴얼 항목
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
            or
            "제목 없음"
        )

        breadcrumb = (
            _string_list(
                item.get(
                    "breadcrumb"
                )
            )
        )

        page = (
            item.get(
                "page"
            )
        )

        source_pages: list[int] = []

        if isinstance(
            page,
            int,
        ):

            source_pages.append(
                page
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

            # 일반 문서의 원문 그대로 제공
            "content": _clean(
                item.get(
                    "content"
                )
            ),

            "intakeQuestions": [],

            "immediateActions": [],

            "decisionBranches": [],

            "responseScripts": [],

            "escalationRules": [],

            "cautions": [],
        }


    # -----------------------------------------------------
    # case 페이지 내용 합치기
    # -----------------------------------------------------

    def _case_content(
        self,
        item: dict[str, Any],
    ) -> str:

        page_items = (
            item.get(
                "content_by_page",
                [],
            )
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


    # -----------------------------------------------------
    # case 페이지 번호
    # -----------------------------------------------------

    def _case_pages(
        self,
        item: dict[str, Any],
    ) -> list[int]:

        page_start = (
            item.get(
                "page_start"
            )
        )

        page_end = (
            item.get(
                "page_end"
            )
        )


        if (
            isinstance(
                page_start,
                int,
            )

            and

            isinstance(
                page_end,
                int,
            )

            and

            page_end
            >=
            page_start
        ):

            return list(
                range(
                    page_start,
                    page_end + 1,
                )
            )


        result: list[int] = []


        page_items = (
            item.get(
                "content_by_page",
                [],
            )
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


                page = (
                    page_item.get(
                        "page"
                    )
                )


                if (
                    isinstance(
                        page,
                        int,
                    )

                    and

                    page not in result
                ):

                    result.append(
                        page
                    )


        return sorted(
            result
        )


    # -----------------------------------------------------
    # 상황별 분기 정리
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
                or
                actions
                or
                response
            ):

                result.append(
                    {
                        "condition": (
                            condition
                        ),

                        "actions": (
                            actions
                        ),

                        "response": (
                            response
                        ),
                    }
                )


        return result


    # -----------------------------------------------------
    # 상향/보고 규칙 정리
    # -----------------------------------------------------

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
                or
                action
            ):

                result.append(
                    {
                        "condition": (
                            condition
                        ),

                        "action": (
                            action
                        ),
                    }
                )


        return result


    # -----------------------------------------------------
    # case 데이터 → 전체 매뉴얼 항목
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
            or
            "제목 없음"
        )

        category = (
            _clean(
                item.get(
                    "category"
                )
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


        # 데이터팀이 별도의 summary를 만들어둔 경우
        # 그것을 우선 사용.
        #
        # 없다면 정보 손실을 막기 위해
        # 기존 매뉴얼 원문을 그대로 보여줌.
        summary = (
            _clean(
                item.get(
                    "summary"
                )
            )
            or
            full_content
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
                or
                (
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

            "summary": summary,

            "content": (
                full_content
            ),

            # 데이터에 구조화 항목이 존재하는 경우
            # 그대로 사용하고,
            # 존재하지 않으면 빈 배열 사용
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
        }


    # -----------------------------------------------------
    # 전체 매뉴얼 목록
    # -----------------------------------------------------

    def list_entries(
        self,
    ) -> list[
        dict[str, Any]
    ]:

        entries: list[
            dict[str, Any]
        ] = []


        # 일반 문서
        for item in self.sections:

            entries.append(
                self._section_entry(
                    item
                )
            )


        # 상황별 대응 문서
        for item in self.cases:

            entries.append(
                self._case_entry(
                    item
                )
            )


        # 프론트 메뉴의 분류 순서에 맞춰 정렬
        group_index = {

            group: index

            for (
                index,
                group,
            ) in enumerate(
                GROUP_ORDER
            )
        }


        def sort_key(
            entry: dict[str, Any],
        ):

            pages = (
                entry.get(
                    "sourcePages",
                    [],
                )
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


    # -----------------------------------------------------
    # GET /api/manual 응답
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