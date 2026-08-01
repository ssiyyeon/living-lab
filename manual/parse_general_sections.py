"""
매뉴얼 PDF 중 "민원 대응 케이스" 형식이 아닌 나머지 내용(당직근무자 준수사항,
청사 보안/시건, 비상연락망, 재난보고체계 개요, 당직일지 작성법, 소화기 비치 등)을
파싱해 manual/general_docs.json으로 저장한다.

Phase 0에서는 "부서→민원요지→처리방법" 형식의 케이스 28개만 다뤘는데, 사용자가
"PDF 85페이지 전체 내용이 빠짐없이 들어가야 한다"고 요구해서 나머지도 반영한다.
다만 이 내용들은 민원 대응 케이스가 아니라 당직자 본인이 자기 근무를 위해
참고하는 내부 문서라서, situations.json과는 성격이 달라 별도 파일로 분리했다.

주의: p16~20(청사 보안 및 시건), p48(재난관리책임기관 연락체계도)은 원래 도면·
흐름도라서 텍스트로 뽑으면 줄글이 아니라 단어들이 흩어진 형태로 나온다. 그래도
"빠짐없이 반영"하라는 요구사항에 따라 원문 그대로 포함했다 — 검색은 되지만
사람이 읽기엔 매뉴얼 원본 PDF를 직접 보는 게 낫다.
"""

import json
import re
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent
PDF_PATH = PROJECT_ROOT.parent / "2. ★(유성구) 당직 근무요령 및 상황별 매뉴얼_26. 5..pdf"
OUT_PATH = PROJECT_ROOT / "general_docs.json"

_NOISE_PATTERNS = [
    re.compile(r"^-\s*\d+\s*-$"),
    re.compile(r"^[▼⇓⇒⇔⇕]+$"),
    re.compile(r"^-$"),
]

# (제목, 시작 페이지, 끝 페이지) — 모두 1-based, inclusive. 케이스 28개(Phase 0,
# manual/rule_lookup.py 대상)로 이미 다룬 페이지는 제외했다.
SECTIONS = [
    ("당직근무자 준수사항", 4, 6),
    ("재난상황 보고체계 개요", 7, 15),
    ("청사 보안 및 시건", 16, 20),
    ("휴일 비상연락·비상발령 및 소집체계", 21, 25),
    ("재난상황 당직사령 개요 및 1-1 자연재난(태풍·호우 등) 조치요령", 26, 34),
    ("재난관리책임기관 연락체계도", 48, 48),
    ("당직근무일지 작성 및 당직민원 등록", 49, 51),
    ("소화기 및 질식소화포 비치", 85, 85),
]


def _clean_lines(lines: list[str]) -> list[str]:
    return [l for l in lines if not any(p.match(l.strip()) for p in _NOISE_PATTERNS)]


def main():
    doc = fitz.open(PDF_PATH)
    docs = []
    for title, start_page, end_page in SECTIONS:
        lines: list[str] = []
        for page_num in range(start_page, end_page + 1):
            page_text = doc[page_num - 1].get_text()
            lines.extend(l.strip() for l in page_text.split("\n") if l.strip())
        lines = _clean_lines(lines)
        docs.append({
            "제목": title,
            "페이지범위": f"p{start_page}~{end_page}" if start_page != end_page else f"p{start_page}",
            "내용": lines,
        })
        print(f"추출: {title} ({'p%d~%d' % (start_page, end_page) if start_page != end_page else f'p{start_page}'}, {len(lines)}줄)")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print(f"\n총 {len(docs)}개 문서 저장 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
