"""
search/engine.py의 임계치(MANUAL_THRESHOLD/REFERENCE_THRESHOLD/MIN_RELEVANCE)가
적당한지 전체 민원 데이터로 검증한다.

지금까지는 15개 정도의 손으로 고른 쿼리로만 확인했는데, 그건 "내가 고른 쉬운
문제"에서만 잘 되는 건지 실제로는 알 수 없다. 이 스크립트는 전체 5,624건에
엔진을 그대로 돌려서:

1. 매뉴얼 규칙이 원래 매칭하는 건(40.4%)을 엔진도 "매뉴얼" 근거수준으로 잡는가
   (유사도 기반 검색이 기존 키워드 규칙과 얼마나 일치하는지 = 회귀 확인)
2. "결과없음"/"근거불충분"으로 빠지는 비율이 얼마나 되는가 (너무 많으면 임계치가
   과함, 너무 적으면 신뢰 못할 것까지 확정 답변 취급 위험)
3. "매뉴얼"/"참고사례"로 확정된 것들의 부서가 실제 처리부서와 얼마나 일치하는가
   (엔진이 확정 응답을 준 것 자체가 신뢰할 만한지 사후 검증)

주의: 참고사례 카드의 예시 문구 자체가 이 데이터에서 뽑힌 것이라, 참고사례
일치율은 다소 낙관적으로 나올 수 있음 (같은 데이터로 카드를 만들고 검증하는 셈).
매뉴얼 일치율은 이런 누수가 없다 (매뉴얼은 PDF 원본에서만 만들어짐).
"""

import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from model.common import load_data  # noqa: E402
from manual.rule_lookup import match_manual  # noqa: E402
from search.engine import SearchEngine  # noqa: E402


def main():
    df = load_data()
    engine = SearchEngine()

    tier_counts = Counter()
    dept_match = Counter()   # tier -> 일치 건수
    dept_total = Counter()   # tier -> 부서 비교 가능 건수 (결과 있고 실제부서도 있는 경우)
    manual_rule_vs_engine = Counter()  # 기존 키워드규칙 매칭 여부 x 엔진 근거수준

    n = len(df)
    for i, row in enumerate(df.itertuples(index=False)):
        text = str(row.민원내용)
        actual_dept = str(row.처리부서).strip() if row.처리부서 else None

        had_rule_hit = bool(match_manual(text))
        result = engine.search(text)
        tier = result["근거수준"]
        tier_counts[tier] += 1
        manual_rule_vs_engine[(had_rule_hit, tier)] += 1

        if result["결과"] and actual_dept:
            top_dept = result["결과"][0]["부서"]
            dept_total[tier] += 1
            if top_dept == actual_dept:
                dept_match[tier] += 1

        if (i + 1) % 1000 == 0:
            print(f"  {i + 1}/{n} 처리...")

    print(f"\n전체 {n}건 검증 결과\n")
    print("=== 근거수준별 분포 ===")
    for tier, cnt in tier_counts.most_common():
        print(f"  {tier}: {cnt}건 ({cnt / n * 100:.1f}%)")

    print("\n=== 기존 키워드 규칙(match_manual) 매칭 여부 x 엔진 근거수준 ===")
    print("  (규칙이 매칭했는데 엔진이 '매뉴얼'이 아니면 회귀 - 임계치가 너무 높다는 신호)")
    for (had_hit, tier), cnt in sorted(manual_rule_vs_engine.items()):
        label = "규칙매칭O" if had_hit else "규칙매칭X"
        print(f"  {label} -> 엔진={tier}: {cnt}건")

    print("\n=== 근거수준별 1순위 부서 일치율 (실제 처리부서 대비) ===")
    for tier in ["매뉴얼", "참고사례", "근거불충분"]:
        total = dept_total.get(tier, 0)
        match = dept_match.get(tier, 0)
        if total:
            print(f"  {tier}: {match}/{total} = {match / total * 100:.1f}%")
        else:
            print(f"  {tier}: 비교 가능 건수 없음")


if __name__ == "__main__":
    main()
