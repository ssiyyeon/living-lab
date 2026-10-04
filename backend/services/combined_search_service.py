from __future__ import annotations

import re

from typing import Any

from backend.services.guide_service import (
    guide_service,
)

from backend.services.manual_service import (
    manual_service,
)

from backend.services.search_service import (
    NO_MATCH_MESSAGE,
    SearchServiceUnavailable,
    search_service as base_search_service,
)


class CombinedSearchService:

    @property
    def is_ready(
        self,
    ) -> bool:
        return (
            base_search_service.is_ready
            or guide_service.has_overrides()
            or manual_service.has_admin_changes()
        )


    @property
    def load_error(
        self,
    ) -> str | None:
        if base_search_service.is_ready:
            return None

        if (
            guide_service.has_overrides()
            or manual_service.has_admin_changes()
        ):
            return (
                "기존 검색엔진은 준비되지 않았지만 "
                "관리자 반영 내용 검색은 사용할 수 있습니다."
            )

        return (
            base_search_service
            .load_error
        )


    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> dict[str, Any]:
        query = query.strip()

        if not query:
            return self._empty_response(
                query=query,
                message=(
                    "검색어를 입력해 주세요."
                ),
            )


        # -------------------------------------------------
        # 기존 업무안내 관리자 수정본 검색
        # -------------------------------------------------

        guide_matches = (
            guide_service
            .search_overrides(
                query=query,
                top_k=top_k,
            )
        )

        guide_admin_results = (
            self
            ._make_guide_admin_results(
                query=query,
                matches=guide_matches,
            )
        )


        # -------------------------------------------------
        # 전체 매뉴얼 관리자 수정/추가본 검색
        # -------------------------------------------------

        manual_matches = (
            manual_service
            .search_admin_changes(
                query=query,
                top_k=top_k,
            )
        )

        manual_admin_results = (
            self
            ._make_manual_admin_results(
                query=query,
                matches=manual_matches,
            )
        )


        # 관리자 결과 합치기
        admin_results = (
            manual_admin_results
            + guide_admin_results
        )

        admin_results.sort(
            key=lambda item: int(
                item.get(
                    "relevance",
                    0,
                )
            ),
            reverse=True,
        )


        # -------------------------------------------------
        # 기존 데이터팀 검색
        # -------------------------------------------------

        base_response = None

        if base_search_service.is_ready:
            base_response = (
                base_search_service
                .search(
                    query=query,
                    top_k=top_k,
                )
            )

        elif not admin_results:
            raise SearchServiceUnavailable(
                base_search_service.load_error
                or
                (
                    "검색 엔진 또는 "
                    "검색 데이터가 준비되지 않았습니다."
                )
            )


        base_results: list[
            dict[str, Any]
        ] = []

        if base_response:
            base_results = list(
                base_response.get(
                    "results",
                    [],
                )
            )


        # -------------------------------------------------
        # 관리자가 수정한 기존 매뉴얼 항목은
        # 원래 JSON 검색 결과가 다시 나오지 않게 제외
        # -------------------------------------------------

        overridden_manual_ids = (
            manual_service
            .modified_entry_ids()
        )

        if overridden_manual_ids:
            base_results = [
                result

                for result
                in base_results

                if str(
                    result.get(
                        "id",
                        "",
                    )
                )
                not in overridden_manual_ids
            ]


        # -------------------------------------------------
        # 관리자 결과 + 기존 결과 합치기
        # -------------------------------------------------

        combined_results: list[
            dict[str, Any]
        ] = []

        used_ids: set[str] = set()

        for result in (
            admin_results
            + base_results
        ):
            result_id = str(
                result.get(
                    "id",
                    "",
                )
            )

            if (
                result_id
                and result_id in used_ids
            ):
                continue

            if result_id:
                used_ids.add(
                    result_id
                )

            combined_results.append(
                result
            )

            if (
                len(
                    combined_results
                )
                >= top_k
            ):
                break


        # -------------------------------------------------
        # 결과 없음
        # -------------------------------------------------

        if not combined_results:
            if base_response:
                return base_response

            return self._empty_response(
                query=query,
                message=(
                    NO_MATCH_MESSAGE
                ),
            )


        # -------------------------------------------------
        # 추천 부서
        # -------------------------------------------------

        recommended_departments: list[
            str
        ] = []

        for result in combined_results:
            for department in (
                result.get(
                    "departments",
                    [],
                )
            ):
                if (
                    department
                    and department
                    not in recommended_departments
                ):
                    recommended_departments.append(
                        department
                    )


        admin_ids = {
            str(
                result.get(
                    "id",
                    "",
                )
            )

            for result
            in admin_results
        }

        has_admin_result = any(
            str(
                result.get(
                    "id",
                    "",
                )
            )
            in admin_ids

            for result
            in combined_results
        )


        if has_admin_result:
            tier = (
                "manual_exact"
            )

            message = (
                "당직 매뉴얼에서 "
                "관련 내용을 찾았습니다."
            )

        else:
            tier = str(
                (
                    base_response
                    or {}
                ).get(
                    "tier",
                    "manual_exact",
                )
            )

            message = str(
                (
                    base_response
                    or {}
                ).get(
                    "message",
                    "관련 검색 결과를 찾았습니다.",
                )
            )


        return {
            "query": (
                query
            ),

            "tier": (
                tier
            ),

            "message": (
                message
            ),

            "resultCount": len(
                combined_results
            ),

            "recommendedDepartments": (
                recommended_departments
            ),

            "relevanceNotice": (
                "관련도는 현재 검색 결과 안에서의 "
                "상대 점수이며, 정답 확률이나 "
                "신뢰도 확률을 의미하지 않습니다."
            ),

            "results": (
                combined_results
            ),
        }


    # -----------------------------------------------------
    # 기존 업무안내 관리자 수정본 → SearchResult
    # -----------------------------------------------------

    def _make_guide_admin_results(
        self,
        query: str,
        matches: list[
            dict[str, Any]
        ],
    ) -> list[
        dict[str, Any]
    ]:
        if not matches:
            return []

        max_score = max(
            float(
                item.get(
                    "score",
                    0,
                )
            )

            for item
            in matches
        )

        query_terms = re.findall(
            r"[가-힣A-Za-z0-9]{2,}",
            query,
        )

        results: list[
            dict[str, Any]
        ] = []

        for match in matches:
            guide = (
                match[
                    "guide"
                ]
            )

            section = (
                match[
                    "section"
                ]
            )

            section_index = int(
                match[
                    "sectionIndex"
                ]
            )

            score = float(
                match[
                    "score"
                ]
            )

            steps = [
                str(
                    step
                ).strip()

                for step
                in section.get(
                    "steps",
                    [],
                )

                if str(
                    step
                ).strip()
            ]

            summary = (
                " ".join(
                    steps[:3]
                )
            )

            if not summary:
                summary = str(
                    guide.get(
                        "description",
                        "",
                    )
                )

            added_at = (
                section.get(
                    "addedAt"
                )
            )

            updated_at = (
                added_at
                or guide.get(
                    "updatedAt"
                )
                or ""
            )

            if max_score > 0:
                relevance = round(
                    (
                        score
                        / max_score
                    )
                    * 100
                )

            else:
                relevance = 0


            results.append(
                {
                    "id": (
                        f"guide_"
                        f"{guide['id']}_"
                        f"{section_index}"
                    ),

                    "kind": (
                        "manual_section"
                    ),

                    "category": (
                        "당직 매뉴얼"
                    ),

                    "documentName": str(
                        guide.get(
                            "title",
                            "",
                        )
                    ),

                    "civilType": (
                        str(
                            section.get(
                                "title",
                                "",
                            )
                        )
                        or
                        str(
                            guide.get(
                                "title",
                                "",
                            )
                        )
                    ),

                    "department": (
                        "담당 부서 확인 필요"
                    ),

                    "departments": [],

                    "departmentContacts": [],

                    "paragraphSummary": (
                        summary
                    ),

                    "guidance": (
                        " ".join(
                            steps
                        )
                        if steps
                        else
                        str(
                            guide.get(
                                "description",
                                "",
                            )
                        )
                    ),

                    "note": (
                        f"{added_at} 추가"
                        if added_at
                        else ""
                    ),

                    "updatedAt": str(
                        updated_at
                    ),

                    "relevance": max(
                        1,
                        min(
                            100,
                            relevance,
                        ),
                    ),

                    "tags": (
                        query_terms[:6]
                    ),

                    "evidenceLevel": (
                        "official_manual"
                    ),

                    "sourceReference": str(
                        guide.get(
                            "title",
                            "",
                        )
                    ),

                    "sourcePages": list(
                        guide.get(
                            "sourcePages",
                            [],
                        )
                    ),

                    "matchedPage": None,

                    "originalUrl": None,

                    "candidateCount": None,

                    "departmentRouting": [],

                    "caseKind": None,

                    "intakeQuestions": [],

                    "immediateActions": (
                        steps
                    ),

                    "decisionBranches": [],

                    "responseScripts": [],

                    "escalationRules": [],

                    "cautions": list(
                        guide.get(
                            "cautions",
                            [],
                        )
                    ),
                }
            )

        return results


    # -----------------------------------------------------
    # 전체 매뉴얼 관리자 수정/추가본 → SearchResult
    # -----------------------------------------------------

    def _make_manual_admin_results(
        self,
        query: str,
        matches: list[
            dict[str, Any]
        ],
    ) -> list[
        dict[str, Any]
    ]:
        if not matches:
            return []

        max_score = max(
            float(
                item.get(
                    "score",
                    0,
                )
            )

            for item
            in matches
        )

        query_terms = re.findall(
            r"[가-힣A-Za-z0-9]{2,}",
            query,
        )

        results: list[
            dict[str, Any]
        ] = []

        for match in matches:
            entry = (
                match[
                    "entry"
                ]
            )

            score = float(
                match.get(
                    "score",
                    0,
                )
            )

            if max_score > 0:
                relevance = round(
                    (
                        score
                        / max_score
                    )
                    * 100
                )

            else:
                relevance = 0


            departments = [
                str(
                    value
                )

                for value
                in entry.get(
                    "departments",
                    [],
                )

                if str(
                    value
                ).strip()
            ]


            summary = str(
                entry.get(
                    "summary",
                    "",
                )
            ).strip()

            if not summary:
                summary = str(
                    entry.get(
                        "content",
                        "",
                    )
                ).strip()

            if len(
                summary
            ) > 500:
                summary = (
                    summary[:497]
                    + "..."
                )


            immediate_actions = list(
                entry.get(
                    "immediateActions",
                    [],
                )
            )

            content = str(
                entry.get(
                    "content",
                    "",
                )
            ).strip()

            guidance = (
                " ".join(
                    str(
                        value
                    )

                    for value
                    in immediate_actions

                    if str(
                        value
                    ).strip()
                )
                or content
                or summary
            )


            source_pages = [
                int(
                    page
                )

                for page
                in entry.get(
                    "sourcePages",
                    [],
                )

                if isinstance(
                    page,
                    int,
                )
            ]


            added_at = (
                entry.get(
                    "addedAt"
                )
            )

            note = (
                f"{added_at} 추가"

                if (
                    entry.get(
                        "isCustom"
                    )
                    and added_at
                )

                else ""
            )


            results.append(
                {
                    "id": str(
                        entry.get(
                            "id",
                            "",
                        )
                    ),

                    "kind": (
                        "manual_case"

                        if entry.get(
                            "entryType"
                        )
                        == "case"

                        else "manual_section"
                    ),

                    "category": str(
                        entry.get(
                            "group",
                            "당직 매뉴얼",
                        )
                    ),

                    "documentName": (
                        "당직 근무요령 및 상황별 매뉴얼"
                    ),

                    "civilType": str(
                        entry.get(
                            "title",
                            "",
                        )
                    ),

                    "department": (
                        " · ".join(
                            departments
                        )

                        if departments

                        else
                        "담당 부서 확인 필요"
                    ),

                    "departments": (
                        departments
                    ),

                    "departmentContacts": [],

                    "paragraphSummary": (
                        summary
                        or
                        "관련 매뉴얼 내용을 확인해 주세요."
                    ),

                    "guidance": (
                        guidance
                        or
                        "관련 매뉴얼 내용을 확인해 주세요."
                    ),

                    "note": (
                        note
                    ),

                    "updatedAt": str(
                        entry.get(
                            "updatedAt",
                            "",
                        )
                        or ""
                    ),

                    "relevance": max(
                        1,
                        min(
                            100,
                            relevance,
                        ),
                    ),

                    "tags": (
                        query_terms[:6]
                    ),

                    "evidenceLevel": (
                        "official_manual"
                    ),

                    "sourceReference": (
                        manual_service
                        .source
                    ),

                    "sourcePages": (
                        source_pages
                    ),

                    "matchedPage": (
                        source_pages[0]
                        if source_pages
                        else None
                    ),

                    "originalUrl": None,

                    "candidateCount": None,

                    "departmentRouting": [],

                    "caseKind": str(
                        entry.get(
                            "topic",
                            "",
                        )
                        or ""
                    ),

                    "intakeQuestions": list(
                        entry.get(
                            "intakeQuestions",
                            [],
                        )
                    ),

                    "immediateActions": (
                        immediate_actions
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
            )

        return results


    def _empty_response(
        self,
        query: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "query": (
                query
            ),

            "tier": (
                "no_match"
            ),

            "message": (
                message
            ),

            "resultCount": 0,

            "recommendedDepartments": [],

            "relevanceNotice": (
                "관련도는 현재 검색 결과 안에서의 "
                "상대 점수이며, 정답 확률이나 "
                "신뢰도 확률을 의미하지 않습니다."
            ),

            "results": [],
        }


combined_search_service = (
    CombinedSearchService()
)