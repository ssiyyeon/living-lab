"""
검색 엔진 임계치를 실측으로 보정하고, 회귀 테스트로도 재사용하기 위한 스크립트.

사용법: 저장소 루트에서 `python search/calibrate.py` 실행.
- PASS/FAIL 요약이 나오면 engine.py의 임계치 상수가 아래 테스트셋 기준으로 여전히
  유효한지 확인된 것. 새 케이스를 추가한 뒤에는 반드시 다시 돌려서 회귀가 없는지 본다.
- 대화형 대표 문장과 공식 매뉴얼 31개, 반복민원 26개를 함께 검사한다.
- 실제 검색 로그가 쌓이면 표현별 테스트를 계속 추가하고 임계치도 다시 잡아야 한다.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from search.engine import SearchEngine  # noqa: E402

# (질문, 기대 tier, 기대 top 제목 - None이면 no_match만 확인)
TEST_CASES = [
    ("지하차도에 물이 차서 차가 못 지나가요", "manual_exact", "지하차도 침수시 조치요령"),
    ("가스가 터진 것 같아요 냄새나요", "manual_exact", "가스폭발 접수시 조치요령"),
    ("고양이가 로드킬 당했어요 사체 좀 치워주세요", "manual_exact", "부상동물 및 동물사체 신고"),
    ("가로수가 쓰러질 것 같아요", "manual_exact", "가로수 등 수목 전도(쓰러짐), 교통사고 전화"),
    ("포트홀 때문에 타이어 터질뻔했어요", "manual_exact", "포트홀, 싱크홀 신고"),
    ("가로등이 고장나서 어두워요", "historical_case", "가로등 고장 신고"),
    ("불법으로 주차한 차 좀 단속해주세요", "manual_exact", "불법주정차 신고"),
    ("야간소음", "manual_exact", "소음 민원"),
    ("밤에 노래방에서 시끄러운 소리가 계속 나요", "manual_exact", "소음 민원"),
    ("가로등 고장 신고", "historical_case", "가로등 고장 신고"),
    ("보안등이 꺼져서 길이 너무 어두워요", "historical_case", "가로등 고장 신고"),
    ("불법 현수막 철거해주세요", "historical_case", "불법 현수막 철거 요청"),
    ("가드레일이 파손됐어요", "historical_case", "도로 시설물 파손 신고"),
    ("공원 운동기구가 파손됐어요", "historical_case", "공원 시설물 훼손·하자 신고"),
    ("화물차가 매일 밤샘주차 중이에요", "historical_case", "화물차 등 밤샘주차 단속 요청"),
    ("장애인 주차구역에 불법주차했어요", "historical_case", "장애인 주차구역 관련 신고·문의"),
    ("생계지원금 신청 문의", "historical_case", "생계지원금·수급자 관련 문의"),
    ("공사장 관련 민원 문의", "historical_case", "공사장 관련 민원·문의"),
    ("CCTV 영상을 확인하고 싶어요", "historical_case", "CCTV 열람·확인 문의"),
    ("무단횡단하는 사람이 너무 많아요", "no_match", None),
    ("공무원이 불친절해요", "no_match", None),
    ("세금을 어디서 내나요", "no_match", None),
    ("오늘 날씨가 좋네요", "no_match", None),
]


def load_catalog_cases():
    manual_data = json.load(
        open(
            BASE / "data/manual/manual_cases.json",
            encoding="utf-8",
        )
    )
    intent_data = json.load(
        open(
            BASE / "data/complaints/search_intents.json",
            encoding="utf-8",
        )
    )

    manual_titles = {
        case["id"]: case["title"]
        for case in manual_data
    }
    cases = [
        (
            case["title"],
            "manual_exact",
            case["title"],
            None,
        )
        for case in manual_data
    ]

    for intent in intent_data.get("intents", []):
        related_ids = intent.get("relatedManualCaseIds", [])
        if related_ids:
            cases.append(
                (
                    intent["title"],
                    "manual_exact",
                    manual_titles[related_ids[0]],
                    intent["title"],
                )
            )
        else:
            cases.append(
                (
                    intent["title"],
                    "historical_case",
                    intent["title"],
                    None,
                )
            )

    return cases


def run():
    engine = SearchEngine()
    passed, failed = 0, 0
    cases = [
        (*case, None)
        for case in TEST_CASES
    ] + load_catalog_cases()

    for query, expect_tier, expect_top, expect_related in cases:
        r = engine.search(query)
        titles = [x["title"] for x in r.get("results", [])]
        tier_ok = r["tier"] == expect_tier
        top_ok = (
            (expect_top is None and not titles)
            or (titles and titles[0] == expect_top)
        )
        related_ok = expect_related is None or expect_related in titles[1:]
        ok = tier_ok and top_ok and related_ok
        passed += ok
        failed += not ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {query!r}")
        print(f"       tier={r['tier']}(기대:{expect_tier})  top={titles[:3]}")
        if expect_related:
            print(f"       related={expect_related!r} 포함={related_ok}")
    print(f"\n{passed}/{passed+failed} 통과")


if __name__ == "__main__":
    run()
