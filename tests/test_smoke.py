"""
회귀를 잡기 위한 최소 스모크 테스트. pytest 없이 `python3 tests/test_smoke.py`로
바로 실행 가능하게 짰다 (이 프로젝트에 아직 테스트 프레임워크가 없어서 의존성을
늘리지 않는 쪽을 택함).

app.recommend / search.engine 테스트는 analysis/recurring_complaint_types_curated.json
(Phase 2 산출물)이 있어야 돈다. 없으면 그 테스트만 건너뛴다 (먼저
`python3 analysis/cluster_complaints.py` 후 `python3 analysis/curate_recurring_types.py` 실행 필요).
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = 0
_failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS: {name}")
    else:
        _failed += 1
        print(f"  FAIL: {name}  {detail}")


def test_match_manual():
    print("\n[manual.rule_lookup.match_manual]")
    from manual.rule_lookup import match_manual

    hits = match_manual("궁동 근처에서 유기견을 발견했어요")
    depts = [h["부서"] for h in hits]
    check("유기견 -> 지역산업과 매칭", "지역산업과" in depts, depts)

    hits = match_manual("도로에 포트홀이 생겼습니다")
    depts = [h["부서"] for h in hits]
    check("포트홀 -> 건설과 매칭", "건설과" in depts, depts)

    hits = match_manual("오늘 날씨가 참 좋네요")
    check("무관한 텍스트는 매칭 없음", hits == [], hits)


def test_match_general():
    print("\n[manual.general_lookup.match_general]")
    from manual.general_lookup import match_general

    hits = match_general("소화기 어디 있어요")
    titles = [h["제목"] for h in hits]
    check("소화기 -> 소화기 비치 문서 매칭", "소화기 및 질식소화포 비치" in titles, titles)

    hits = match_general("오늘 날씨가 참 좋네요")
    check("무관한 텍스트는 매칭 없음", hits == [], hits)


def test_load_situations_strips_noise():
    print("\n[manual.rule_lookup.load_situations - 잡음 라인 제거]")
    from manual.rule_lookup import load_situations

    situations = load_situations()
    all_lines = [l for s in situations.values() for l in s["처리방법"] + s["참고사항"]]
    has_page_marker = any(l.strip() in ("- 50 -", "- 51 -", "- 52 -") for l in all_lines)
    has_lone_arrow = any(l.strip() == "▼" for l in all_lines)
    check("페이지 마커('- N -') 제거됨", not has_page_marker)
    check("단독 화살표('▼') 제거됨", not has_lone_arrow)


def test_recommend():
    print("\n[app.recommend.recommend / search.engine - 근거수준별 케이스]")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    curated_path = os.path.join(root, "analysis", "recurring_complaint_types_curated.json")
    general_docs_path = os.path.join(root, "manual", "general_docs.json")
    if not os.path.exists(curated_path):
        print("  SKIP: analysis/recurring_complaint_types_curated.json 없음 "
              "(먼저 cluster_complaints.py, curate_recurring_types.py 실행 필요)")
        return
    if not os.path.exists(general_docs_path):
        print("  SKIP: manual/general_docs.json 없음 (먼저 parse_general_sections.py 실행 필요)")
        return

    from app.recommend import recommend

    outcome = recommend("아동학대가 의심되는 상황입니다")
    check("매뉴얼 등재 상황은 근거수준=매뉴얼", outcome["근거수준"] == "매뉴얼", outcome["근거수준"])
    check("매뉴얼 결과에 부서 포함", any(r["부서"] == "아동복지과" for r in outcome["결과"]), outcome["결과"])
    if outcome["결과"]:
        check("매뉴얼 결과에 관련문단 포함", bool(outcome["결과"][0].get("관련문단")))

    outcome2 = recommend("가로등이 안 들어와요 고쳐주세요")
    check(
        "매뉴얼 미등재지만 반복유형인 경우 근거수준=참고사례",
        outcome2["근거수준"] == "참고사례",
        outcome2["근거수준"],
    )

    outcome4 = recommend("소화기 어디 있어요")
    check(
        "민원 대응 케이스가 아닌 내부 근무수칙은 근거수준=일반매뉴얼",
        outcome4["근거수준"] == "일반매뉴얼",
        outcome4["근거수준"],
    )

    outcome3 = recommend("asdkjaslkdj 완전히 무관한 잡담입니다 오늘 저녁 뭐 먹지")
    check(
        "관련 문서 자체가 없으면 근거수준=결과없음",
        outcome3["근거수준"] == "결과없음",
        outcome3["근거수준"],
    )
    check("결과없음일 때 임의 답변을 생성하지 않음(결과 비어있음)", outcome3["결과"] == [])


def test_feedback_roundtrip():
    print("\n[app.feedback.save_feedback / load_feedback_log]")
    import app.feedback as feedback

    with tempfile.TemporaryDirectory() as tmp:
        original_path = feedback.FEEDBACK_LOG_PATH
        feedback.FEEDBACK_LOG_PATH = os.path.join(tmp, "feedback_log.csv")
        try:
            outcome = {"근거수준": "매뉴얼", "결과": [{"부서": "지역산업과"}]}
            feedback.save_feedback("유기견 발견", outcome, correct=True)
            feedback.save_feedback(
                "철도 공사장 소음", outcome, correct=False, actual_dept="철도건설국", note="외부기관"
            )
            df = feedback.load_feedback_log()
            check("피드백 2건 기록됨", len(df) == 2, len(df))
            check("정확한 건 실제부서 자동 채움", df.iloc[0]["실제부서"] == "지역산업과")
            check("틀린 건 실제부서 직접 기록", df.iloc[1]["실제부서"] == "철도건설국")
        finally:
            feedback.FEEDBACK_LOG_PATH = original_path


if __name__ == "__main__":
    test_match_manual()
    test_match_general()
    test_load_situations_strips_noise()
    test_recommend()
    test_feedback_roundtrip()

    print(f"\n{'=' * 40}\n{_passed} passed, {_failed} failed")
    sys.exit(1 if _failed else 0)
