from __future__ import annotations

import re

from typing import Any

from backend.services.guide_service import (
    guide_service,
)

from backend.services.search_service import (
    NO_MATCH_MESSAGE,
    SearchServiceUnavailable,
    search_service as base_search_service,
)


class CombinedSearchService:
    """
    기존 데이터팀 검색 결과와
    관리자가 수정/추가한 안내 검색 결과를
    하나로 합쳐주는 서비스
    """

    @property
    def is_ready(
        self,
    ) -> bool:
        """
        기존 검색엔진이 준비되어 있거나
        관리자 수정 데이터가 있으면 검색 가능
        """

        return (
            base_search_service.is_ready
            or
            guide_service.has_overrides()
        )

    @property
    def load_error(
        self,
    ) -> str | None:
        """
        검색 준비 상태 확인용
        """

        if base_search_service.is_ready:
            return None

        if guide_service.has_overrides():
            return (
                "기존 검색엔진은 준비되지 않았지만 "
                "관리자 반영 안내 검색은 사용할 수 있습니다."
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
        """
        최종 검색 함수

        1. 관리자 수정/추가 내용 검색
        2. 기존 데이터팀 검색
        3. 두 결과 합치기
        """

        query = query.strip()

        if not query:

            return self._empty_response(
                query=query,
                message=(
                    "검색어를 입력해 주세요."
                ),
            )

        # -------------------------------------------------
        # 1. 관리자가 추가/수정한 내용 검색
        # -------------------------------------------------

        admin_matches = (
            guide_service
            .search_overrides(
                query=query,
                top_k=top_k,
            )
        )

        admin_results = (
            self
            ._make_admin_results(
                query=query,
                matches=admin_matches,
            )
        )

        # -------------------------------------------------
        # 2. 기존 데이터팀 검색
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

        # 기존 검색엔진도 없고
        # 관리자 검색 결과도 없으면
        # 검색 불가능
        elif not admin_results:

            raise SearchServiceUnavailable(
                base_search_service.load_error
                or
                (
                    "검색 엔진 또는 "
                    "검색 데이터가 준비되지 않았습니다."
                )
            )

        # 기존 검색 결과 배열
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
        # 3. 관리자 결과 + 기존 결과 합치기
        # -------------------------------------------------

        combined_results: list[
            dict[str, Any]
        ] = []

        used_ids: set[str] = set()

        # 관리자가 변경한 내용을 먼저 넣고
        # 그 다음 기존 검색 결과를 넣음
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

            # 같은 결과 중복 방지
            if (
                result_id
                and
                result_id in used_ids
            ):
                continue

            if result_id:

                used_ids.add(
                    result_id
                )

            combined_results.append(
                result
            )

            # 프론트에서 요청한 개수까지만 반환
            if (
                len(
                    combined_results
                )
                >= top_k
            ):
                break

        # -------------------------------------------------
        # 검색 결과가 하나도 없는 경우
        # -------------------------------------------------

        if not combined_results:

            # 기존 검색 서비스가 이미
            # no_match 응답을 만들었다면 그대로 사용
            if base_response:

                return base_response

            return self._empty_response(
                query=query,
                message=NO_MATCH_MESSAGE,
            )

        # -------------------------------------------------
        # 관련 부서 정리
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
                    and
                    department
                    not in
                    recommended_departments
                ):

                    recommended_departments.append(
                        department
                    )

        # 관리자 수정 내용이 검색됐다면
        # 일반 매뉴얼 검색 결과처럼 처리
        if admin_results:

            tier = "manual_exact"

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

            "query": query,

            "tier": tier,

            "message": message,

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

    def _make_admin_results(
        self,
        query: str,
        matches: list[
            dict[str, Any]
        ],
    ) -> list[
        dict[str, Any]
    ]:
        """
        guide_service가 찾은 관리자 수정 내용을
        기존 SearchResult 모양으로 변환
        """

        if not matches:
            return []

        # 상대 관련도를 계산하기 위해
        # 가장 높은 점수를 찾음
        max_score = max(
            float(
                item.get(
                    "score",
                    0,
                )
            )
            for item in matches
        )

        # 검색어 태그 생성
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

            # 처리 단계 내용
            steps = [
                str(step).strip()

                for step
                in section.get(
                    "steps",
                    [],
                )

                if str(
                    step
                ).strip()
            ]

            # 검색 결과에서 보여줄 짧은 요약
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

            # 새로 추가한 단계라면 추가 날짜
            added_at = (
                section.get(
                    "addedAt"
                )
            )

            # 기존 내용 수정이라면
            # guide 전체 수정 날짜 사용
            updated_at = (
                added_at
                or
                guide.get(
                    "updatedAt"
                )
                or
                ""
            )

            # 관련도 0~100
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

            # -------------------------------------------------
            # 기존 검색 결과와 같은 형태로 만들어줌
            # -------------------------------------------------

            result = {

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

                # 현재 업무 안내 데이터에는
                # 별도의 담당 부서 입력칸이 없으므로
                # 기본값 사용
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

                # 새로 추가된 단계라면
                # 예: 2026-10-04 추가
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

                # 사용자 화면에서는
                # 기존 매뉴얼과 같은 안내로 표시
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

                # 최신 프론트에서 사용하는
                # 추가 필드들
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

            results.append(
                result
            )

        return results

    def _empty_response(
        self,
        query: str,
        message: str,
    ) -> dict[str, Any]:
        """
        검색 결과 없음
        """

        return {

            "query": query,

            "tier": "no_match",

            "message": message,

            "resultCount": 0,

            "recommendedDepartments": [],

            "relevanceNotice": (
                "관련도는 현재 검색 결과 안에서의 "
                "상대 점수이며, 정답 확률이나 "
                "신뢰도 확률을 의미하지 않습니다."
            ),

            "results": [],
        }


# 다른 파일에서 사용할 공통 객체
combined_search_service = (
    CombinedSearchService()
)