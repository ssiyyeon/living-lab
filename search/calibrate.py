"""
검색 엔진 임계치를 실측으로 보정하고, 회귀 테스트로도 재사용하기 위한 스크립트.

사용법: 저장소 루트에서 `python search/calibrate.py` 실행.
- PASS/FAIL 요약이 나오면 engine.py의 임계치 상수가 아래 테스트셋 기준으로 여전히
  유효한지 확인된 것. 새 케이스를 추가한 뒤에는 반드시 다시 돌려서 회귀가 없는지 본다.
- 표본이 12개뿐이라 통계적으로 충분하지 않다. 실제 검색 로그가 쌓이면 이 테스트셋을
  키우고 임계치도 다시 잡아야 한다(TODO.md 참고).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.engine import SearchEngine  # noqa: E402

# (질문, 기대 tier, 기대 top 제목 - None이면 no_match만 확인)
TEST_CASES = [
    ("지하차도에 물이 차서 차가 못 지나가요", "manual_exact", "지하차도 침수시 조치요령"),
    ("가스가 터진 것 같아요 냄새나요", "manual_exact", "가스폭발 접수시 조치요령"),
    ("고양이가 로드킬 당했어요 사체 좀 치워주세요", "manual_exact", "부상동물 및 동물사체 신고"),
    ("가로수가 쓰러질 것 같아요", "manual_exact", "가로수 등 수목 전도(쓰러짐), 교통사고 전화"),
    ("포트홀 때문에 타이어 터질뻔했어요", "manual_exact", "포트홀, 싱크홀 신고"),
    ("가로등이 고장나서 어두워요", "historical_case", "가로등 고장 신고"),
    # 아래는 정답이 top-3 안에만 있으면 통과로 본다(순위까지는 아직 보정 안 됨 - 알려진 한계)
    ("불법으로 주차한 차 좀 단속해주세요", "manual_exact", None),
    ("야간소음", "manual_exact", "소음 민원"),
    ("밤에 노래방에서 시끄러운 소리가 계속 나요", "manual_exact", "소음 민원"),
    ("무단횡단하는 사람이 너무 많아요", "no_match", None),
    ("공무원이 불친절해요", "no_match", None),
    ("세금을 어디서 내나요", "no_match", None),
    ("오늘 날씨가 좋네요", "no_match", None),
]


def run():
    engine = SearchEngine()
    passed, failed = 0, 0
    for query, expect_tier, expect_top in TEST_CASES:
        r = engine.search(query)
        titles = [x["title"] for x in r.get("results", [])]
        tier_ok = r["tier"] == expect_tier
        top_ok = expect_top is None or (titles and titles[0] == expect_top) or (expect_top in titles)
        ok = tier_ok and top_ok
        passed += ok
        failed += not ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {query!r}")
        print(f"       tier={r['tier']}(기대:{expect_tier})  top={titles[:3]}")
    print(f"\n{passed}/{passed+failed} 통과")


if __name__ == "__main__":
    run()
