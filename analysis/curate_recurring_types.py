"""
Phase 2 클러스터(analysis/cluster_complaints.py 출력) 중 사람이 검토해서
"반복 민원 유형"으로 확정한 것만 골라 병합한다.

GROUPS의 클러스터 ID 매핑은 analysis/cluster_complaints.py를 실행한 뒤
analysis/recurring_complaint_types.json을 사람이 직접 훑어보고 정한 것이다
(자동 병합이 아니라 수작업 큐레이션). 나머지 클러스터는 "~후 전화 요망"류
문체 유사성으로 묶인 잡음이라 판단해 폐기했다.

출력은 개별 민원 원문을 포함하므로 .gitignore에 등록되어 있다.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "analysis" / "recurring_complaint_types.json"
OUT_PATH = PROJECT_ROOT / "analysis" / "recurring_complaint_types_curated.json"

# 유형명 -> 병합할 클러스터 ID 목록 (analysis/cluster_complaints.py 실행 결과를 보고 수작업 확정)
#
# "도로 침수/배수", "중앙분리대/가드레일 파손", "제설 작업 요청"은 이전 버전에서는
# 여기 있었지만, manual/parse_disaster_manual.py로 재난유형별 행동매뉴얼(대설·
# 지하차도침수·도로낙하물 조치요령)을 추가 파싱한 뒤 매뉴얼 키워드로 승격되어
# 더 이상 "매뉴얼에 없는 참고사례"가 아니게 됐다 — 그래서 여기서 제거했다.
GROUPS = {
    "가로등 고장/불량": [6, 15, 23, 28, 14],
    "노점상 단속": [25],
    "불법 현수막 철거": [13],
    "쓰레기 무단투기": [18],
    "미성년자 주류판매 단속": [22],
}

N_KEYWORDS = 10
N_EXAMPLES = 3


def main():
    with open(SRC_PATH, encoding="utf-8") as f:
        clusters = {r["cluster"]: r for r in json.load(f)}

    curated = []
    for name, ids in GROUPS.items():
        members = [clusters[i] for i in ids if i in clusters]
        if not members:
            print(f"경고: {name}의 클러스터 ID가 최신 결과에 없음 (재클러스터링 후 ID가 바뀌었을 수 있음) — 건너뜀")
            continue

        total = sum(m["건수"] for m in members)
        dept_votes: dict[str, int] = {}
        for m in members:
            dept_votes[m["주요처리부서"]] = dept_votes.get(m["주요처리부서"], 0) + m["건수"]
        dept = max(dept_votes, key=dept_votes.get)

        keywords = []
        for m in members:
            for kw in m["대표키워드"]:
                if kw not in keywords:
                    keywords.append(kw)
        keywords = keywords[:N_KEYWORDS]

        examples = []
        for m in members:
            examples.extend(m["예시민원"])
        examples = examples[:N_EXAMPLES]

        action_votes: dict[str, int] = {}
        for m in members:
            if m["주요조치유형"]:
                action_votes[m["주요조치유형"]] = action_votes.get(m["주요조치유형"], 0) + m["건수"]
        action = max(action_votes, key=action_votes.get) if action_votes else None

        curated.append({
            "유형명": name,
            "건수": total,
            "주요부서": dept,
            "대표키워드": keywords,
            "예시민원": examples,
            "주요조치유형": action,
            "근거수준": "참고사례",
        })

    curated.sort(key=lambda r: r["건수"], reverse=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(curated, f, ensure_ascii=False, indent=2)

    print(f"확정된 반복 민원 유형 {len(curated)}개 저장: {OUT_PATH}")
    for r in curated:
        print(f"- {r['유형명']}: {r['건수']}건, 주요부서 {r['주요부서']}")


if __name__ == "__main__":
    main()
