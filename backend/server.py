"""듀토리 Python 검색 엔진을 브라우저에 제공하는 JSON API 서버."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_FILES = (
    PROJECT_ROOT / "data" / "manual" / "manual_cases.json",
    PROJECT_ROOT / "data" / "manual" / "manual_sections.json",
    PROJECT_ROOT / "data" / "complaints" / "recurring_cases.json",
    PROJECT_ROOT / "search" / "index" / "docs.json",
    PROJECT_ROOT / "search" / "index" / "bm25.pkl",
)
REQUIRED_MODULES = ("rank_bm25",)
MAX_REQUEST_BYTES = 32 * 1024

_engine = None


def service_status() -> dict[str, Any]:
    missing_files = [
        str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        for path in REQUIRED_FILES
        if not path.exists()
    ]
    missing_modules = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    return {
        "ready": not missing_files and not missing_modules,
        "missingFiles": missing_files,
        "missingModules": missing_modules,
    }


def get_engine():
    global _engine
    if _engine is None:
        from search.engine import SearchEngine

        _engine = SearchEngine()
    return _engine


def page_label(document: dict[str, Any]) -> str | None:
    start = document.get("page_start")
    end = document.get("page_end")
    if start is None:
        return None
    return str(start) if end in (None, start) else f"{start}–{end}"


def result_note(document: dict[str, Any]) -> str:
    if document.get("kind") != "recurring_case":
        return "공식 당직 매뉴얼을 근거로 검색된 결과입니다."

    count = document.get("candidate_count")
    count_text = f"과거 유사 민원 {count}건을 바탕으로 한 참고자료입니다. " if count else ""
    gap_note = document.get("content") or ""
    return (
        f"{count_text}공식 매뉴얼의 확정 대응이 아니므로 담당 부서 확인 후 처리하세요."
        + (f"\n\n{gap_note}" if gap_note else "")
    )


def normalize_search_response(raw: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    tier_labels = {
        "manual_exact": "공식 매뉴얼",
        "manual_semantic": "매뉴얼 자동매칭",
        "historical_case": "과거 민원 참고",
        "no_match": "결과 없음",
    }
    documents_by_id = {document["doc_id"]: document for document in documents}
    normalized_results = []

    for result in raw.get("results", []):
        document = documents_by_id.get(result["doc_id"], {})
        departments = document.get("departments") or []
        breadcrumb = document.get("breadcrumb") or []
        is_historical = document.get("kind") == "recurring_case"
        document_name = (
            "반복 민원 유형 (2024~2026년 민원 이력)"
            if is_historical
            else document.get("source") or (breadcrumb[0] if breadcrumb else "당직 근무요령 및 상황별 매뉴얼")
        )

        normalized_results.append(
            {
                "tier": tier_labels.get(raw.get("tier"), raw.get("tier", "검색 결과")),
                "부서": " · ".join(departments) or None,
                "민원유형": result.get("title") or document.get("title") or "제목 없음",
                "관련문단": document.get("content") or document.get("display_text") or "",
                "참고사항": result_note(document),
                "담당자": None,
                "문서명": document_name,
                "페이지": page_label(document),
                "유사도": None,
                "검색점수": result.get("bm25_score"),
            }
        )

    return {
        "근거수준": tier_labels.get(raw.get("tier"), raw.get("tier", "검색 결과")),
        "안내": raw.get("message"),
        "결과": normalized_results,
    }


def run_search(query: str, top_k: int) -> dict[str, Any]:
    status = service_status()
    if not status["ready"]:
        raise SearchServiceNotReady(status)
    engine = get_engine()
    return normalize_search_response(engine.search(query, top_k=top_k), engine.docs)


class SearchServiceNotReady(RuntimeError):
    def __init__(self, status: dict[str, Any]):
        super().__init__("검색 인덱스 또는 Python 패키지가 준비되지 않았습니다.")
        self.status = status


class DutoryApiHandler(BaseHTTPRequestHandler):
    server_version = "DutoryAPI/1.0"

    def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = b"" if status == HTTPStatus.NO_CONTENT else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header(
            "Access-Control-Allow-Origin",
            os.getenv("DUTORY_CORS_ORIGIN", "http://127.0.0.1:5173"),
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _error(self, status: HTTPStatus, code: str, message: str, **details: Any) -> None:
        self._write_json(status, {"error": {"code": code, "message": message, **details}})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._write_json(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/health":
            self._error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "요청한 API 경로가 없습니다.")
            return
        self._write_json(HTTPStatus.OK, service_status())

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/search":
            self._error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "요청한 API 경로가 없습니다.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
                raise ValueError("요청 크기가 올바르지 않습니다.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            query = str(payload.get("query", "")).strip()
            top_k = max(1, min(int(payload.get("topK", 4)), 10))
            if not query:
                raise ValueError("검색어를 입력해 주세요.")
            self._write_json(HTTPStatus.OK, run_search(query, top_k))
        except SearchServiceNotReady as exc:
            self._error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "SEARCH_NOT_READY",
                "검색 인덱스가 준비되지 않았습니다. 설치 후 search/build_index.py를 실행해 주세요.",
                **exc.status,
            )
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, "INVALID_REQUEST", str(exc))
        except Exception as exc:
            print(f"[api:error] {type(exc).__name__}: {exc}")
            self._error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "SEARCH_FAILED",
                "검색 중 오류가 발생했습니다. 서버 로그를 확인해 주세요.",
            )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[api] {self.address_string()} - {format % args}")


def main() -> None:
    host = os.getenv("DUTORY_API_HOST", "127.0.0.1")
    port = int(os.getenv("DUTORY_API_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), DutoryApiHandler)
    print(f"듀토리 API 실행 중: http://{host}:{port}")
    print(f"검색 준비 상태: {json.dumps(service_status(), ensure_ascii=False)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
