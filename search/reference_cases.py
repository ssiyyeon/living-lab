"""
Phase 2에서 확정한 "반복 민원 유형"(analysis/curate_recurring_types.py 출력)을
불러온다. 매뉴얼(manual/situations.json)과 달리 이 데이터는 "공식 대응"이 아니라
명세서가 규정한 대로 "참고 사례" 계층으로만 검색 엔진에 사용된다.

원본 JSON은 실제 민원 원문을 포함해 개인정보 우려가 있으므로 .gitignore에
등록되어 있다 — 이 파일(코드)에는 PII가 없고, 데이터 로딩 로직만 있다.
"""

import json
from pathlib import Path

CURATED_PATH = Path(__file__).resolve().parent.parent / "analysis" / "recurring_complaint_types_curated.json"


def load_reference_cases() -> list[dict]:
    if not CURATED_PATH.exists():
        raise FileNotFoundError(
            f"{CURATED_PATH} 가 없습니다. 먼저 다음을 순서대로 실행하세요:\n"
            "  python3 analysis/cluster_complaints.py\n"
            "  python3 analysis/curate_recurring_types.py"
        )
    with open(CURATED_PATH, encoding="utf-8") as f:
        return json.load(f)
