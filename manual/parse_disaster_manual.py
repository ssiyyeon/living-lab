"""
매뉴얼 PDF 중 "재난유형별 행동매뉴얼"(p33~47, Ⅲ장) 섹션을 파싱해
manual/situations.json에 추가한다.

배경: Phase 0에서는 PDF 뒷부분의 "당직근무 민원처리 매뉴얼"(p52~) 19개 상황만
추출했는데, 실사용 중 "이 앞쪽 재난 섹션도 매뉴얼 아니냐"는 지적을 받고 다시
확인해보니 실제로 p33~47에 대설(제설)/지하차도침수/도로낙하물/화재/가스폭발/
산불/건축물붕괴/구제역·AI 등 9개 상황이 "가.근무사항 + 나.비상연락망" 형식으로
빠짐없이 정리되어 있었다. 이 중 Phase 2 클러스터링에서 "매뉴얼에 없는 참고사례"로
분류했던 "제설 작업 요청"(1-2)과 "도로 침수/배수"(1-3), "중앙분리대·낙하물"(2-2)이
사실은 이미 공식 매뉴얼에 있었다는 뜻 — 그 부분은 참고사례에서 매뉴얼로 승격해야 한다.

1-1(태풍·호우, 자연재난 일반)과 사회재난 개요 페이지는 개별 민원 대응이라기보다
기관 내부 보고체계 위주라 제외했다(당직자가 특정 민원에 바로 매칭해 쓸 절차가 아님).
"""

import json
import re
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).resolve().parent
PDF_PATH = PROJECT_ROOT.parent / "2. ★(유성구) 당직 근무요령 및 상황별 매뉴얼_26. 5..pdf"
SITUATIONS_PATH = PROJECT_ROOT / "situations.json"

_NOISE_PATTERNS = [
    re.compile(r"^-\s*\d+\s*-$"),
    re.compile(r"^[▼⇓⇒⇔⇕]+$"),
    re.compile(r"^-$"),
]

# (0-based 페이지 인덱스, 부서, 담당자 요약) — 페이지 원문을 직접 읽고 확정한 값
DISASTER_SITUATIONS = [
    (34, "건설과", "건설과 도로관리팀(박종필 010-9437-7140)"),
    (35, "건설과", "건설과 전기팀/하수팀(양종삼 010-8919-1195, 김을구 010-6828-3606)"),
    (40, "건설과", "건설과 전기팀(양종삼 010-8919-1195) / 생활보장과 희망복지지원팀(이재민 발생시)"),
    (41, "건설과", "건설과 도로관리팀 / 청소행정과 청소행정팀(도로소통 장애 없을 시)"),
    (42, "푸른환경과", "푸른환경과 수질관리팀"),
    (43, "지역산업과", "지역산업과 농축산유통팀"),
    (44, "지역산업과", "지역산업과 에너지팀 / 푸른환경과 환경정책팀"),
    (45, "녹지산림과", "녹지산림과 산림팀"),
    (46, "건축과", "건축과 건축1팀/건축2팀"),
]

_HEADER_PATTERN = re.compile(r"^\d-\d\.\s*(.+)$")


def _clean_lines(lines: list[str]) -> list[str]:
    return [l for l in lines if not any(p.match(l.strip()) for p in _NOISE_PATTERNS)]


def parse_disaster_situations() -> list[dict]:
    doc = fitz.open(PDF_PATH)
    situations = []
    for page_idx, dept, contact in DISASTER_SITUATIONS:
        text = doc[page_idx].get_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        lines = _clean_lines(lines)

        header_line = next((l for l in lines if _HEADER_PATTERN.match(l)), None)
        situation = _HEADER_PATTERN.match(header_line).group(1) if header_line else f"p{page_idx + 1} 상황"

        situations.append({
            "부서": dept,
            "민원요지": situation,
            "처리방법": lines,
            "참고사항": ["재난유형별 행동매뉴얼(Ⅲ장) 항목 — 세부 비상연락망은 원본 매뉴얼 p." + str(page_idx + 1) + " 참고"],
            "담당자": [contact],
            "페이지": page_idx + 1,
        })
    return situations


def main():
    with open(SITUATIONS_PATH, encoding="utf-8") as f:
        existing = json.load(f)
    existing_keys = {(s["부서"], s["민원요지"]) for s in existing}

    new_situations = parse_disaster_situations()
    added = 0
    for s in new_situations:
        key = (s["부서"], s["민원요지"])
        if key in existing_keys:
            print(f"이미 있음, 건너뜀: {key}")
            continue
        existing.append(s)
        added += 1
        print(f"추가: {s['부서']} - {s['민원요지']} (p.{s['페이지']})")

    with open(SITUATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n{added}건 추가, 총 {len(existing)}개 상황 -> {SITUATIONS_PATH}")


if __name__ == "__main__":
    main()
