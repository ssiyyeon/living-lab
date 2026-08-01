"""
manual/general_docs.json(케이스 형식이 아닌 나머지 PDF 내용)에 대한 키워드 사전.

manual/rule_lookup.py의 match_manual()과 성격은 같지만(키워드 있으면 확정),
대상이 "민원 대응 케이스"가 아니라 "당직자 본인이 근무 중 참고하는 내부 문서"라서
파일을 분리했다. 예: "소화기 어디있어요" 같은 건 민원이 아니라 당직자 자신의
질문이므로 search/engine.py에서 "일반매뉴얼"이라는 별도 근거수준으로 구분해 응답한다.
"""

import json
from pathlib import Path

GENERAL_DOCS_PATH = Path(__file__).resolve().parent / "general_docs.json"


def _ensure_exists() -> None:
    if not GENERAL_DOCS_PATH.exists():
        raise FileNotFoundError(
            f"{GENERAL_DOCS_PATH} 가 없습니다. 먼저 다음을 실행하세요:\n"
            "  python3 manual/parse_general_sections.py"
        )

# 제목 -> 트리거 키워드
KEYWORDS = {
    "당직근무자 준수사항": [
        "당직근무시간", "당직 근무시간", "출입자 통제", "청사 방호", "동물사체처리 신고접수대장",
        "당직함", "관용차량",
    ],
    "재난상황 보고체계 개요": ["재난상황 보고체계", "재난 보고체계", "재난상황 보고 방법"],
    "청사 보안 및 시건": ["청사 시건", "청사 잠금", "출입문 잠금 방법", "청사 보안", "문 잠그는"],
    "휴일 비상연락·비상발령 및 소집체계": [
        "비상연락망 확인", "비상소집 절차", "비상 발령 기준", "애사 문자", "직원 상가",
    ],
    "재난상황 당직사령 개요 및 1-1 자연재난(태풍·호우 등) 조치요령": [
        "태풍 예비특보", "호우 예비특보", "자연재난 보고체계",
    ],
    "재난관리책임기관 연락체계도": ["재난관리책임기관", "재난기관 연락처", "비상연락체계도"],
    "당직근무일지 작성 및 당직민원 등록": [
        "당직일지", "당직근무일지", "당직보고 작성", "당직민원 등록 방법", "당직민원 등록 절차",
    ],
    "소화기 및 질식소화포 비치": ["소화기 위치", "소화기 어디", "질식소화포 위치", "소화기 비치 장소"],
}


def load_general_docs() -> dict:
    _ensure_exists()
    with open(GENERAL_DOCS_PATH, encoding="utf-8") as f:
        docs = json.load(f)
    return {d["제목"]: d for d in docs}


def match_general(text: str) -> list[dict]:
    """민원(질문) 텍스트에서 일반 근무수칙 문서 키워드를 찾아 (제목, 매칭키워드) 목록 반환"""
    hits = []
    for title, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                hits.append({"제목": title, "매칭키워드": kw})
                break
    return hits
