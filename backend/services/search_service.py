from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


NO_MATCH_MESSAGE = (
    "관련 문서에서 해당 민원에 대한 명확한 내용을 찾지 못했습니다. "
    "검색어를 변경하거나 관련 담당 부서에 확인해 주세요."
)


class SearchServiceUnavailable(RuntimeError):
    pass


class SearchService:
    def __init__(self) -> None:
        self.engine = None

        self.manual_cases: dict[str, dict[str, Any]] = {}
        self.manual_sections: dict[str, dict[str, Any]] = {}
        self.recurring_cases: dict[str, dict[str, Any]] = {}

        self.manual_source = "당직 근무요령 및 상황별 매뉴얼"

        self._errors: list[str] = []

        self._load_source_data()
        self._load_engine()

    @property
    def is_ready(self) -> bool:
        has_data = bool(
            self.manual_cases
            or self.manual_sections
            or self.recurring_cases
        )

        return self.engine is not None and has_data

    @property
    def load_error(self) -> str | None:
        if not self._errors:
            return None

        return " | ".join(self._errors)

    def _load_json(self, path: Path) -> Any:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _load_source_data(self) -> None:
        try:
            cases = self._load_json(
                DATA_DIR
                / "manual"
                / "manual_cases.json"
            )

            sections = self._load_json(
                DATA_DIR
                / "manual"
                / "manual_sections.json"
            )

            recurring = self._load_json(
                DATA_DIR
                / "complaints"
                / "recurring_cases.json"
            )

            self.manual_cases = {
                item["id"]: item
                for item in cases
                if item.get("id")
            }

            self.manual_sections = {
                item["id"]: item
                for item in sections
                if item.get("id")
            }

            self.recurring_cases = {
                f"recurring_{index:03d}": item
                for index, item in enumerate(recurring)
            }

            for section in sections:
                if section.get("source"):
                    self.manual_source = section["source"]
                    break

        except Exception as exc:
            self._errors.append(
                "source data load failed: "
                f"{type(exc).__name__}: {exc}"
            )

    def _load_engine(self) -> None:
        try:
            root = str(ROOT_DIR)

            if root not in sys.path:
                sys.path.insert(0, root)

            from search.engine import SearchEngine

            self.engine = SearchEngine()

        except Exception as exc:
            self.engine = None

            self._errors.append(
                "search engine load failed: "
                f"{type(exc).__name__}: {exc}"
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
                tier="no_match",
                message="검색어를 입력해 주세요.",
            )

        if not self.is_ready:
            raise SearchServiceUnavailable(
                self.load_error
                or "검색 엔진 또는 검색 데이터가 준비되지 않았습니다."
            )

        raw = self.engine.search(
            query,
            top_k=top_k,
        )

        tier = raw.get(
            "tier",
            "no_match",
        )

        if tier == "no_match":
            return self._empty_response(
                query=query,
                tier="no_match",
                message=NO_MATCH_MESSAGE,
            )

        raw_results = self._remove_zero_score_results(
            raw.get(
                "results",
                [],
            ),
            tier=tier,
        )

        if not raw_results:
            return self._empty_response(
                query=query,
                tier="no_match",
                message=NO_MATCH_MESSAGE,
            )

        max_score = max(
            self._selected_score(
                item,
                tier,
            )
            for item in raw_results
        )

        results = [
            self._enrich_result(
                raw_result=item,
                query=query,
                tier=tier,
                max_score=max_score,
            )
            for item in raw_results
        ]

        recommended_departments: list[str] = []

        for result in results:
            for department in result.get(
                "departments",
                [],
            ):
                if department not in recommended_departments:
                    recommended_departments.append(
                        department
                    )

        return {
            "query": query,
            "tier": tier,
            "message": self._tier_message(tier),
            "resultCount": len(results),
            "recommendedDepartments": recommended_departments,
            "relevanceNotice": (
                "관련도는 현재 검색 결과 안에서의 상대 점수이며, "
                "정답 확률이나 신뢰도 확률을 의미하지 않습니다."
            ),
            "results": results,
        }

    def _empty_response(
        self,
        query: str,
        tier: str,
        message: str,
    ) -> dict[str, Any]:

        return {
            "query": query,
            "tier": tier,
            "message": message,
            "resultCount": 0,
            "recommendedDepartments": [],
            "relevanceNotice": (
                "관련도는 현재 검색 결과 안에서의 상대 점수이며, "
                "정답 확률이나 신뢰도 확률을 의미하지 않습니다."
            ),
            "results": [],
        }

    def _remove_zero_score_results(
        self,
        results: list[dict[str, Any]],
        tier: str,
    ) -> list[dict[str, Any]]:

        return [
            item
            for item in results
            if self._selected_score(
                item,
                tier,
            ) > 0
        ]

    def _selected_score(
        self,
        item: dict[str, Any],
        tier: str,
    ) -> float:

        if tier == "manual_semantic":
            value = item.get(
                "embedding_score",
                item.get(
                    "score",
                    0,
                ),
            )

        else:
            value = item.get(
                "bm25_score",
                item.get(
                    "score",
                    0,
                ),
            )

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _relative_relevance(
        self,
        score: float,
        max_score: float,
    ) -> int:

        if max_score <= 0:
            return 0

        value = round(
            (score / max_score) * 100
        )

        return max(
            1,
            min(
                100,
                value,
            ),
        )

    def _enrich_result(
        self,
        raw_result: dict[str, Any],
        query: str,
        tier: str,
        max_score: float,
    ) -> dict[str, Any]:

        kind = raw_result.get(
            "kind",
            "",
        )

        doc_id = raw_result.get(
            "doc_id",
            "",
        )

        score = self._selected_score(
            raw_result,
            tier,
        )

        relevance = self._relative_relevance(
            score,
            max_score,
        )

        if kind == "manual_case":
            return self._manual_case_result(
                doc_id=doc_id,
                raw_result=raw_result,
                query=query,
                relevance=relevance,
            )

        if kind == "manual_section":
            return self._manual_section_result(
                doc_id=doc_id,
                raw_result=raw_result,
                query=query,
                relevance=relevance,
            )

        if kind == "recurring_case":
            return self._recurring_case_result(
                doc_id=doc_id,
                raw_result=raw_result,
                relevance=relevance,
            )

        return self._fallback_result(
            raw_result=raw_result,
            relevance=relevance,
        )

    def _manual_case_result(
        self,
        doc_id: str,
        raw_result: dict[str, Any],
        query: str,
        relevance: int,
    ) -> dict[str, Any]:

        item = self.manual_cases.get(
            doc_id,
            {},
        )

        content_by_page = item.get(
            "content_by_page",
            [],
        )

        excerpt, matched_page = self._best_excerpt(
            query=query,
            page_items=content_by_page,
        )

        departments = self._string_list(
            item.get(
                "departments"
            )
        )

        breadcrumb = self._string_list(
            item.get(
                "breadcrumb"
            )
        )

        keywords = self._string_list(
            item.get(
                "keywords"
            )
        )[:6]

        page_start = item.get(
            "page_start"
        )

        page_end = item.get(
            "page_end"
        )

        source_pages = self._page_range(
            page_start=page_start,
            page_end=page_end,
            fallback_pages=[
                page.get("page")
                for page in content_by_page
                if page.get("page") is not None
            ],
        )

        civil_type = (
            item.get("title")
            or raw_result.get(
                "title",
                "",
            )
        )

        if breadcrumb:
            document_name = breadcrumb[0]

        else:
            document_name = (
                "당직 근무요령 및 상황별 매뉴얼"
            )

        note_parts = [
            "공식 매뉴얼 근거"
        ]

        if len(breadcrumb) > 1:
            note_parts.append(
                " > ".join(
                    breadcrumb[1:]
                )
            )

        return {
            "id": doc_id,
            "kind": "manual_case",
            "category": (
                item.get("category")
                or "당직 매뉴얼"
            ),
            "documentName": document_name,
            "civilType": civil_type,
            "department": self._department_text(
                departments
            ),
            "departments": departments,
            "paragraphSummary": (
                excerpt
                or "관련 원문 내용을 확인해 주세요."
            ),
            "guidance": (
                "공식 당직 매뉴얼에서 관련 근거가 확인되었습니다. "
                "아래 관련 문단과 원문 페이지를 기준으로 대응해 주세요."
            ),
            "note": " · ".join(
                note_parts
            ),
            "updatedAt": self._manual_date(),
            "relevance": relevance,
            "tags": keywords,
            "evidenceLevel": "official_manual",
            "sourceReference": self._source_reference(
                self.manual_source,
                source_pages,
            ),
            "sourcePages": source_pages,
            "matchedPage": matched_page,
            "originalUrl": None,
            "candidateCount": None,
            "departmentRouting": [],
        }

    def _manual_section_result(
        self,
        doc_id: str,
        raw_result: dict[str, Any],
        query: str,
        relevance: int,
    ) -> dict[str, Any]:

        item = self.manual_sections.get(
            doc_id,
            {},
        )

        page = item.get(
            "page"
        )

        content = item.get(
            "content",
            "",
        )

        excerpt, matched_page = self._best_excerpt(
            query=query,
            page_items=[
                {
                    "page": page,
                    "text": content,
                }
            ],
        )

        keywords = self._string_list(
            item.get(
                "keywords"
            )
        )[:6]

        breadcrumb = self._string_list(
            item.get(
                "breadcrumb"
            )
        )

        source = (
            item.get("source")
            or self.manual_source
        )

        return {
            "id": doc_id,
            "kind": "manual_section",
            "category": "당직 매뉴얼",
            "documentName": (
                item.get(
                    "document_title"
                )
                or "당직 근무요령 및 상황별 매뉴얼"
            ),
            "civilType": (
                item.get("section")
                or raw_result.get(
                    "title",
                    "",
                )
            ),
            "department": "담당 부서 확인 필요",
            "departments": [],
            "paragraphSummary": (
                excerpt
                or "관련 원문 내용을 확인해 주세요."
            ),
            "guidance": (
                "공식 당직 매뉴얼의 관련 문단입니다. "
                "원문 페이지를 확인한 뒤 문서에 적힌 절차를 따라 주세요."
            ),
            "note": (
                "공식 매뉴얼 근거"
                + (
                    f" · {' > '.join(breadcrumb)}"
                    if breadcrumb
                    else ""
                )
            ),
            "updatedAt": self._extract_date(
                source
            ),
            "relevance": relevance,
            "tags": keywords,
            "evidenceLevel": "official_manual",
            "sourceReference": self._source_reference(
                source,
                [page]
                if isinstance(
                    page,
                    int,
                )
                else [],
            ),
            "sourcePages": (
                [page]
                if isinstance(
                    page,
                    int,
                )
                else []
            ),
            "matchedPage": matched_page,
            "originalUrl": None,
            "candidateCount": None,
            "departmentRouting": [],
        }

    def _recurring_case_result(
        self,
        doc_id: str,
        raw_result: dict[str, Any],
        relevance: int,
    ) -> dict[str, Any]:

        item = self.recurring_cases.get(
            doc_id,
            {},
        )

        departments = self._string_list(
            item.get(
                "main_departments"
            )
        )

        source_years = [
            year
            for year in item.get(
                "source_years",
                [],
            )
            if isinstance(
                year,
                int,
            )
        ]

        civil_type = (
            item.get("type")
            or raw_result.get(
                "title",
                "",
            )
        )

        candidate_count = item.get(
            "candidate_count"
        )

        if source_years:
            if len(source_years) == 1:
                year_label = str(
                    source_years[0]
                )

            else:
                year_label = (
                    f"{min(source_years)}"
                    f"–{max(source_years)}"
                )

        else:
            year_label = "3개년"

        paragraph = (
            f"{year_label} 당직 민원 목록에서 "
            f"반복적으로 확인된 '{civil_type}' 유형입니다."
        )

        if isinstance(
            candidate_count,
            int,
        ):
            paragraph += (
                f" 반복 사례 후보 수는 "
                f"{candidate_count}건입니다."
            )

        note = item.get(
            "manual_gap_note"
        )

        if not note:
            note = (
                "과거 민원 목록을 바탕으로 한 참고 사례입니다. "
                "매뉴얼에 없는 내용은 공식 대응으로 단정하지 않습니다."
            )

        routing = []

        for route in (
            item.get(
                "department_routing",
                [],
            )
            or []
        ):
            if not isinstance(
                route,
                dict,
            ):
                continue

            routing.append(
                {
                    "department": str(
                        route.get(
                            "department",
                            "",
                        )
                    ),
                    "condition": str(
                        route.get(
                            "condition",
                            "",
                        )
                    ),
                    "confidence": str(
                        route.get(
                            "confidence",
                            "",
                        )
                    ),
                }
            )

        return {
            "id": doc_id,
            "kind": "recurring_case",
            "category": "반복 민원 사례",
            "documentName": "3개년 당직 민원 목록",
            "civilType": civil_type,
            "department": self._department_text(
                departments
            ),
            "departments": departments,
            "paragraphSummary": paragraph,
            "guidance": (
                "과거 처리 사례를 참고용으로 제공합니다. "
                "공식 매뉴얼 근거가 아니므로 실제 대응 전 담당 부서를 확인해 주세요."
            ),
            "note": self._truncate(
                str(note),
                500,
            ),
            "updatedAt": (
                str(
                    max(source_years)
                )
                if source_years
                else ""
            ),
            "relevance": relevance,
            "tags": (
                [
                    "반복민원",
                    "참고사례",
                ]
                + departments[:4]
            ),
            "evidenceLevel": "historical_case",
            "sourceReference": (
                f"3개년 당직 민원 목록 "
                f"({year_label})"
            ),
            "sourcePages": [],
            "matchedPage": None,
            "originalUrl": None,
            "candidateCount": (
                candidate_count
                if isinstance(
                    candidate_count,
                    int,
                )
                else None
            ),
            "departmentRouting": routing,
        }

    def _fallback_result(
        self,
        raw_result: dict[str, Any],
        relevance: int,
    ) -> dict[str, Any]:

        title = str(
            raw_result.get(
                "title",
                "",
            )
        )

        return {
            "id": str(
                raw_result.get(
                    "doc_id",
                    "",
                )
            ),
            "kind": str(
                raw_result.get(
                    "kind",
                    "",
                )
            ),
            "category": "검색 결과",
            "documentName": title,
            "civilType": title,
            "department": "담당 부서 확인 필요",
            "departments": [],
            "paragraphSummary": (
                "상세 원문 데이터 확인이 필요합니다."
            ),
            "guidance": (
                "원문 근거를 확인해 주세요."
            ),
            "note": (
                "검색 인덱스와 상세 데이터 연결 정보를 확인해 주세요."
            ),
            "updatedAt": "",
            "relevance": relevance,
            "tags": [],
            "evidenceLevel": str(
                raw_result.get(
                    "evidence_level",
                    "",
                )
            ),
            "sourceReference": "",
            "sourcePages": [],
            "matchedPage": None,
            "originalUrl": None,
            "candidateCount": None,
            "departmentRouting": [],
        }

    def _best_excerpt(
        self,
        query: str,
        page_items: list[dict[str, Any]],
        limit: int = 480,
    ) -> tuple[str, int | None]:

        if not page_items:
            return "", None

        terms = re.findall(
            r"[가-힣A-Za-z0-9]{2,}",
            query,
        )

        candidates: list[
            tuple[
                int,
                int,
                str,
                int | None,
            ]
        ] = []

        for order, page_item in enumerate(
            page_items
        ):
            text = self._clean_text(
                str(
                    page_item.get(
                        "text",
                        "",
                    )
                )
            )

            score = sum(
                text.count(term)
                for term in terms
            )

            page = page_item.get(
                "page"
            )

            page_number = (
                page
                if isinstance(
                    page,
                    int,
                )
                else None
            )

            candidates.append(
                (
                    score,
                    -order,
                    text,
                    page_number,
                )
            )

        _, _, best_text, best_page = max(
            candidates,
            key=lambda item: (
                item[0],
                item[1],
            ),
        )

        if not best_text:
            return "", best_page

        positions = [
            best_text.find(term)
            for term in terms
            if best_text.find(term) >= 0
        ]

        first_match = (
            min(positions)
            if positions
            else 0
        )

        start = max(
            0,
            first_match - 100,
        )

        end = min(
            len(best_text),
            start + limit,
        )

        excerpt = best_text[
            start:end
        ].strip()

        if start > 0:
            excerpt = (
                "…" + excerpt
            )

        if end < len(best_text):
            excerpt += "…"

        return (
            excerpt,
            best_page,
        )

    def _clean_text(
        self,
        text: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def _truncate(
        self,
        text: str,
        limit: int,
    ) -> str:

        cleaned = self._clean_text(
            text
        )

        if len(cleaned) <= limit:
            return cleaned

        return (
            cleaned[
                : limit - 1
            ].rstrip()
            + "…"
        )

    def _department_text(
        self,
        departments: list[str],
    ) -> str:

        if not departments:
            return "담당 부서 확인 필요"

        return " · ".join(
            departments
        )

    def _string_list(
        self,
        value: Any,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            return []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    def _page_range(
        self,
        page_start: Any,
        page_end: Any,
        fallback_pages: list[Any],
    ) -> list[int]:

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

        return [
            page
            for page in fallback_pages
            if isinstance(
                page,
                int,
            )
        ]

    def _source_reference(
        self,
        source: str,
        pages: list[int],
    ) -> str:

        if not pages:
            return source

        if len(pages) == 1:
            page_text = (
                f"{pages[0]}쪽"
            )

        else:
            page_text = (
                f"{min(pages)}"
                f"–{max(pages)}쪽"
            )

        return (
            f"{source} · "
            f"{page_text}"
        )

    def _manual_date(self) -> str:
        return self._extract_date(
            self.manual_source
        )

    def _extract_date(
        self,
        text: str,
    ) -> str:

        match = re.search(
            r"(\d{4})\.(\d{1,2})",
            text,
        )

        if not match:
            return ""

        year, month = (
            match.groups()
        )

        return (
            f"{year}-"
            f"{int(month):02d}"
        )

    def _tier_message(
        self,
        tier: str,
    ) -> str:

        messages = {
            "manual_exact": (
                "공식 당직 매뉴얼에서 관련 내용을 찾았습니다."
            ),
            "manual_semantic": (
                "공식 당직 매뉴얼에서 의미가 유사한 내용을 찾았습니다. "
                "자동 의미 매칭 결과이므로 원문을 확인해 주세요."
            ),
            "historical_case": (
                "공식 매뉴얼의 명확한 근거 대신 과거 민원 사례를 "
                "참고용으로 제공합니다."
            ),
        }

        return messages.get(
            tier,
            "관련 검색 결과를 찾았습니다.",
        )


search_service = SearchService()