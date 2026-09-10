from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


NO_MATCH_MESSAGE = (
    "입력한 내용만으로는 대응 절차를 정하기 어렵습니다. "
    "발생 위치, 현재 상황, 원하는 조치를 조금 더 구체적으로 입력해 주세요."
)


class SearchServiceUnavailable(RuntimeError):
    pass


class SearchService:
    def __init__(self) -> None:
        self.engine = None

        self.manual_cases: dict[str, dict[str, Any]] = {}
        self.manual_sections: dict[str, dict[str, Any]] = {}
        self.manual_actions: dict[str, dict[str, Any]] = {}
        self.recurring_cases: dict[str, dict[str, Any]] = {}
        self.response_guides: dict[str, dict[str, Any]] = {}
        self.quick_guides: dict[str, dict[str, Any]] = {}
        self.department_contacts: list[dict[str, Any]] = []
        self.default_department_contact: dict[str, Any] = {}
        self.department_contact_notice = "공개된 업무용 연락처입니다."
        self.department_contacts_verified_at = ""
        self.quick_guide_source = "당직 근무요령 및 상황별 매뉴얼"

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

            action_data = self._load_json(
                DATA_DIR
                / "manual"
                / "manual_action_cases.json"
            )

            response_guide_data = self._load_json(
                DATA_DIR
                / "complaints"
                / "response_guides.json"
            )

            quick_guide_data = self._load_json(
                DATA_DIR
                / "manual"
                / "quick_guides.json"
            )

            department_contact_data = self._load_json(
                DATA_DIR
                / "contacts"
                / "department_contacts.json"
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

            self.manual_actions = {
                item["id"]: item
                for item in action_data.get("cases", [])
                if item.get("id")
            }

            self.recurring_cases = {
                f"recurring_{index:03d}": item
                for index, item in enumerate(recurring)
            }

            self.response_guides = {
                item["id"]: item
                for item in response_guide_data.get("guides", [])
                if item.get("id")
            }

            self.quick_guides = {
                item["id"]: item
                for item in quick_guide_data.get("guides", [])
                if item.get("id")
            }
            self.quick_guide_source = str(
                quick_guide_data.get("source")
                or self.manual_source
            )

            self.department_contacts = [
                item
                for item in department_contact_data.get("contacts", [])
                if isinstance(item, dict) and item.get("phone")
            ]
            self.default_department_contact = dict(
                department_contact_data.get("defaultContact") or {}
            )
            self.department_contact_notice = str(
                department_contact_data.get("notice")
                or self.department_contact_notice
            )
            self.department_contacts_verified_at = str(
                department_contact_data.get("verifiedAt") or ""
            )

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

        response_guide = self._match_response_guide(
            query
        )

        if response_guide:
            return self._response_guide_response(
                query=query,
                guide=response_guide,
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

        raw_results = self._prefer_action_result(
            raw_results
        )

        # 기본 화면에는 가장 적합한 대응 절차 하나만 제공한다. 다만 공식 매뉴얼과
        # 동일 주제의 과거 처리사례가 명시적으로 연결된 경우에는 참고 근거 한 건을
        # 함께 내려 보내 두 근거의 성격을 구분해 볼 수 있게 한다.
        has_related_reference = any(
            item.get("related_reference")
            for item in raw_results[1:]
        )
        raw_results = raw_results[
            : 2 if has_related_reference else 1
        ]

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

    def get_quick_guides(
        self,
    ) -> dict[str, Any]:

        return {
            "source": self.quick_guide_source,
            "guides": list(self.quick_guides.values()),
        }

    def get_contact_directory(
        self,
    ) -> dict[str, Any]:

        contacts: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()

        def add_contact(
            *,
            group: str,
            organization: str,
            label: str,
            phone: str,
            note: str = "",
            source: str,
            source_url: str = "",
        ) -> None:
            normalized_phone = str(phone).strip()
            normalized_organization = str(organization).strip()
            normalized_label = str(label).strip()
            key = (
                normalized_organization,
                normalized_label,
                normalized_phone,
            )

            if not normalized_phone or key in seen:
                return

            seen.add(key)
            stable_key = "|".join(key).encode("utf-8")
            contact_id = hashlib.sha1(stable_key).hexdigest()[:12]
            contacts.append(
                {
                    "id": f"contact_{contact_id}",
                    "group": group,
                    "organization": normalized_organization,
                    "label": normalized_label,
                    "phone": normalized_phone,
                    "note": str(note).strip(),
                    "source": source,
                    "sourceUrl": str(source_url).strip(),
                }
            )

        default_contact = self.default_department_contact
        if default_contact:
            add_contact(
                group="대표·당직",
                organization=str(default_contact.get("department", "유성구청")),
                label=str(default_contact.get("label", "대표전화")),
                phone=str(default_contact.get("phone", "")),
                note=str(default_contact.get("note", "")),
                source="유성구 공개 부서 연락처",
                source_url=str(default_contact.get("sourceUrl", "")),
            )

        emergency_guide = self.quick_guides.get("emergency_contacts", {})
        for contact in emergency_guide.get("contacts", []):
            if not isinstance(contact, dict):
                continue

            add_contact(
                group=str(contact.get("group", "대표·당직")),
                organization=str(contact.get("organization", "")),
                label=str(contact.get("label", "")),
                phone=str(contact.get("phone", "")),
                source=self.quick_guide_source,
            )

        for contact in self.department_contacts:
            add_contact(
                group="담당 부서",
                organization=str(contact.get("department", "")),
                label=str(contact.get("label", "")),
                phone=str(contact.get("phone", "")),
                note=str(contact.get("note", "")),
                source="유성구 공개 부서 연락처",
                source_url=str(contact.get("sourceUrl", "")),
            )

        return {
            "source": self.quick_guide_source,
            "verifiedAt": self.department_contacts_verified_at,
            "notice": (
                f"{self.department_contact_notice} "
                "직원 개인 연락처와 비공개 비상연락망은 포함하지 않습니다."
            ),
            "contacts": contacts,
        }

    def get_manual_catalog(
        self,
    ) -> dict[str, Any]:

        entries: list[dict[str, Any]] = []

        for item in self.manual_sections.values():
            page = item.get("page")
            source_pages = [page] if isinstance(page, int) else []
            content = str(item.get("content", ""))

            entries.append(
                {
                    "id": str(item.get("id", "")),
                    "entryType": "section",
                    "group": self._manual_catalog_group(source_pages),
                    "topic": str(item.get("section", "일반 참고")),
                    "title": str(item.get("section", "매뉴얼 참고사항")),
                    "breadcrumb": self._string_list(item.get("breadcrumb")),
                    "sourcePages": source_pages,
                    "departments": [],
                    "summary": self._readable_section_summary(content, 280),
                    "content": self._public_manual_content(content),
                    "intakeQuestions": [],
                    "immediateActions": [],
                    "decisionBranches": [],
                    "responseScripts": [],
                    "escalationRules": [],
                    "cautions": [],
                }
            )

        for item in self.manual_cases.values():
            item_id = str(item.get("id", ""))
            action = self.manual_actions.get(item_id, {})
            source_pages = self._page_range(
                item.get("page_start"),
                item.get("page_end"),
                [page_item.get("page") for page_item in item.get("content_by_page", [])],
            )
            content = "\n\n".join(
                str(page_item.get("text", ""))
                for page_item in item.get("content_by_page", [])
                if isinstance(page_item, dict)
            )

            entries.append(
                {
                    "id": item_id,
                    "entryType": "case",
                    "group": self._manual_catalog_group(source_pages),
                    "topic": str(item.get("category", "상황별 대응")),
                    "title": str(item.get("title", "상황별 대응")),
                    "breadcrumb": self._string_list(item.get("breadcrumb")),
                    "sourcePages": source_pages,
                    "departments": self._string_list(
                        action.get("departments") or item.get("departments")
                    ),
                    "summary": str(action.get("summary") or self._readable_section_summary(content, 280)),
                    "content": self._public_manual_content(content),
                    "intakeQuestions": self._string_list(action.get("intakeQuestions")),
                    "immediateActions": self._string_list(action.get("immediateActions")),
                    "decisionBranches": action.get("decisionBranches", []),
                    "responseScripts": self._string_list(action.get("responseScripts")),
                    "escalationRules": action.get("escalationRules", []),
                    "cautions": self._string_list(action.get("cautions")),
                }
            )

        entries.sort(
            key=lambda entry: (
                min(entry["sourcePages"]) if entry["sourcePages"] else 999,
                entry["id"],
            )
        )

        return {
            "source": self.manual_source,
            "totalCount": len(entries),
            "entries": entries,
        }

    @staticmethod
    def _manual_catalog_group(
        pages: list[int],
    ) -> str:

        page = min(pages) if pages else 999

        if page <= 15:
            return "당직근무자 준수사항"
        if page <= 20:
            return "청사 보안·시건"
        if page <= 25:
            return "비상 발령·소집"
        if page <= 47:
            return "재난유형별 대응"
        if page <= 84:
            return "민원유형별 대응"
        return "부록"

    def _public_manual_content(
        self,
        content: str,
    ) -> str:

        lines: list[str] = []

        for raw_line in str(content).replace("\x00", " ").splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()

            if not line or re.fullmatch(r"-\s*\d+\s*-", line):
                continue

            line = re.sub(r"[▫▪◦⦁●■ü]+", "• ", line)
            line = re.sub(r"(?:⇨|⇒)+", "→", line)
            lines.append(line)

        return "\n".join(lines)

    def _contacts_for_departments(
        self,
        departments: list[str],
        case_id: str = "",
    ) -> list[dict[str, str]]:

        resolved: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        case_contacts = [
            contact
            for contact in self.department_contacts
            if case_id
            and case_id in self._string_list(contact.get("matchCaseIds"))
        ]

        contacts_to_check = case_contacts or self.department_contacts

        for department in departments:
            for contact in contacts_to_check:
                matches = self._string_list(
                    contact.get("matchDepartments")
                )

                if not case_contacts and department not in matches:
                    continue

                item = {
                    "department": str(contact.get("department", department)),
                    "label": str(contact.get("label", "업무 연락처")),
                    "phone": str(contact.get("phone", "")),
                    "note": str(contact.get("note", "")),
                    "sourceUrl": str(contact.get("sourceUrl", "")),
                }
                key = (item["department"], item["phone"])

                if item["phone"] and key not in seen:
                    resolved.append(item)
                    seen.add(key)

        if not resolved and departments and self.default_department_contact:
            contact = self.default_department_contact
            resolved.append(
                {
                    "department": str(contact.get("department", "유성구청")),
                    "label": str(contact.get("label", "담당 부서 연결")),
                    "phone": str(contact.get("phone", "")),
                    "note": str(contact.get("note", "")),
                    "sourceUrl": str(contact.get("sourceUrl", "")),
                }
            )

        return resolved

    @staticmethod
    def _normalize_match_text(
        text: str,
    ) -> str:

        return re.sub(
            r"[^가-힣A-Za-z0-9]+",
            "",
            text,
        ).lower()

    def _match_response_guide(
        self,
        query: str,
    ) -> dict[str, Any] | None:

        normalized_query = self._normalize_match_text(
            query
        )
        matches: list[tuple[int, dict[str, Any]]] = []

        for guide in self.response_guides.values():
            terms = [
                guide.get("title", ""),
                *guide.get("searchTerms", []),
            ]

            for term in terms:
                normalized_term = self._normalize_match_text(
                    str(term)
                )

                if len(normalized_term) < 2:
                    continue

                if normalized_term == normalized_query:
                    score = 200 + len(normalized_term)
                elif normalized_term in normalized_query:
                    score = 150 + len(normalized_term)
                elif normalized_query in normalized_term:
                    score = 100 + len(normalized_query)
                else:
                    continue

                matches.append(
                    (score, guide)
                )

        if not matches:
            return None

        return max(
            matches,
            key=lambda item: item[0],
        )[1]

    def _response_guide_response(
        self,
        query: str,
        guide: dict[str, Any],
    ) -> dict[str, Any]:

        departments = self._string_list(
            guide.get("departments")
        )
        immediate_actions = self._string_list(
            guide.get("immediateActions")
        )

        result = {
            "id": str(guide.get("id", "")),
            "kind": "department_guide",
            "category": "담당부서 안내",
            "documentName": "당직 대응 가이드",
            "civilType": str(guide.get("title", "민원 처리 안내")),
            "department": self._department_text(departments),
            "departments": departments,
            "paragraphSummary": str(guide.get("summary", "")),
            "guidance": " ".join(immediate_actions),
            "note": (
                "과거 당직 민원의 실제 이첩 사례를 기준으로 정리한 안내입니다. "
                "허가 여부와 최종 처분은 담당 부서 확인이 필요합니다."
            ),
            "updatedAt": "2026",
            "relevance": 100,
            "tags": [],
            "evidenceLevel": str(guide.get("evidenceLevel", "historical_case")),
            "sourceReference": str(guide.get("sourceReference", "3개년 당직 민원 목록")),
            "sourcePages": [],
            "matchedPage": None,
            "originalUrl": None,
            "candidateCount": guide.get("candidateCount"),
            "departmentRouting": [],
            "departmentContacts": self._contacts_for_departments(
                departments,
                str(guide.get("id", "")),
            ),
            "caseKind": guide.get("caseKind", "routing"),
            "intakeQuestions": self._string_list(guide.get("intakeQuestions")),
            "immediateActions": immediate_actions,
            "decisionBranches": guide.get("decisionBranches", []),
            "responseScripts": self._string_list(guide.get("responseScripts")),
            "escalationRules": guide.get("escalationRules", []),
            "cautions": self._string_list(guide.get("cautions")),
        }

        return {
            "query": query,
            "tier": "department_guide",
            "message": "과거 처리 사례를 바탕으로 담당 부서와 대응 순서를 안내합니다.",
            "resultCount": 1,
            "recommendedDepartments": departments,
            "relevanceNotice": "담당부서 안내는 과거 처리 사례를 근거로 하며 최종 판단은 담당 부서에서 합니다.",
            "results": [result],
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

    def _prefer_action_result(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if not results:
            return results

        first_result = results[0]
        first_id = str(
            first_result.get(
                "doc_id",
                "",
            )
        )

        # 행동 데이터가 붙은 공식 사례가 1순위라면, OCR 원문 조각과
        # 낮은 점수의 참고 문서는 숨긴다. 단, 검색 의도 데이터에서 같은
        # 주제로 직접 연결한 과거 처리사례 한 건은 근거 비교용으로 유지한다.
        if first_id in self.manual_actions:
            related_references = [
                item
                for item in results[1:]
                if item.get("related_reference")
            ]
            return [
                first_result,
                *related_references[:1],
            ]

        return results

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

        action_case = self.manual_actions.get(
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
                action_case.get("summary")
                or excerpt
                or "관련 원문 내용을 확인해 주세요."
            ),
            "guidance": (
                " ".join(
                    action_case.get(
                        "immediateActions",
                        [],
                    )
                )
                or (
                    "공식 당직 매뉴얼에서 관련 근거가 확인되었습니다. "
                    "아래 관련 문단과 원문 페이지를 기준으로 대응해 주세요."
                )
            ),
            "note": " · ".join(
                (
                    action_case.get(
                        "cautions",
                        [],
                    )[:1]
                    + note_parts
                )
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
            "departmentContacts": self._contacts_for_departments(
                departments,
                doc_id,
            ),
            "caseKind": action_case.get("caseKind"),
            "intakeQuestions": action_case.get(
                "intakeQuestions",
                [],
            ),
            "immediateActions": action_case.get(
                "immediateActions",
                [],
            ),
            "decisionBranches": action_case.get(
                "decisionBranches",
                [],
            ),
            "responseScripts": action_case.get(
                "responseScripts",
                [],
            ),
            "escalationRules": action_case.get(
                "escalationRules",
                [],
            ),
            "cautions": action_case.get(
                "cautions",
                [],
            ),
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
                self._readable_section_summary(
                    content
                    or excerpt
                )
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
            "departmentContacts": [],
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

            raw_condition = str(
                route.get(
                    "condition",
                    "",
                )
            )
            raw_confidence = str(
                route.get(
                    "confidence",
                    "",
                )
            )

            routing.append(
                {
                    "department": str(
                        route.get(
                            "department",
                            "",
                        )
                    ),
                    "condition": self._routing_condition_label(
                        raw_condition
                    ),
                    "confidence": self._routing_confidence_label(
                        raw_confidence
                    ),
                }
            )

        routing_branches = [
            {
                "condition": route["condition"],
                "actions": [
                    f"{route['department']} 소관으로 분류해 민원 내용을 이첩한다."
                ],
                "response": (
                    f"말씀하신 상황은 {route['department']} 확인이 필요합니다. "
                    "내용을 기록해 담당 부서로 전달하겠습니다."
                ),
            }
            for route in routing
            if route["department"] and route["condition"]
        ]

        department_text = self._department_text(
            departments
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
                "민원 발생 위치와 현재 상황을 기록한 뒤 "
                f"{department_text}에 이첩합니다."
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
            "departmentContacts": self._contacts_for_departments(
                departments,
                doc_id,
            ),
            "caseKind": "routing",
            "intakeQuestions": [
                "민원이 발생한 정확한 위치는 어디인가요?",
                "현재도 문제가 계속되고 있나요?",
                "민원인이 원하는 조치는 무엇인가요?",
                "담당 부서에서 회신할 연락처를 남기셨나요?",
            ],
            "immediateActions": [
                "위치, 발생 시각, 현재 상태와 요청사항을 당직민원에 기록한다.",
                f"과거 처리 사례의 담당 부서인 {department_text}에 이첩한다.",
                "야간에 처리 결과나 출동 여부를 확정해서 약속하지 않는다.",
            ],
            "decisionBranches": routing_branches,
            "responseScripts": [
                f"민원 내용을 정확히 기록한 뒤 {department_text}에 전달하겠습니다. "
                "담당 부서 확인 후 처리 가능한 사항을 안내드리겠습니다."
            ],
            "escalationRules": [],
            "cautions": [
                "과거 이첩 사례에 따른 안내이므로 최종 소관과 조치는 담당 부서가 판단한다."
            ],
        }

    def _routing_condition_label(
        self,
        condition: str,
    ) -> str:

        # department_routing.condition은 표본 번호와 판단 근거까지 담은
        # 데이터 검수용 필드다. 화면 버튼에는 첫 업무 조건만 짧게 노출한다.
        label = re.split(
            r"\s*[\(\[]",
            condition,
            maxsplit=1,
        )[0]
        label = re.split(
            r"[.。]\s*",
            label,
            maxsplit=1,
        )[0]

        return label.strip(
            " \t\r\n.,-"
        ) or "해당 조건"

    def _routing_confidence_label(
        self,
        confidence: str,
    ) -> str:

        if confidence.startswith("높음"):
            return "높음"

        if confidence.startswith("낮음"):
            return "실무 확인 필요"

        return confidence

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
            "departmentContacts": [],
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

    def _readable_section_summary(
        self,
        text: str,
        limit: int = 220,
    ) -> str:

        cleaned = str(text).replace(
            "\x00",
            " ",
        )

        cleaned = re.sub(
            r"<\s*참고자료\s*>",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"(?m)^\s*[qm]\s+(?=[가-힣])",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"[□▫▪◦⦁●■▷ü]+",
            " · ",
            cleaned,
        )
        cleaned = re.sub(
            r"(?:⇨|⇒|→)+",
            " → ",
            cleaned,
        )
        cleaned = re.sub(
            r"\s*-\s*\d+\s*-\s*$",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"\s*·\s*",
            " · ",
            cleaned,
        )
        cleaned = re.sub(
            r"\s*→\s*",
            " → ",
            cleaned,
        )

        return self._truncate(
            cleaned,
            limit,
        )

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
