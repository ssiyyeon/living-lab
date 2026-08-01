"""
웹사이트 백엔드에서 바로 호출할 수 있는 최종 검색 함수.

Phase 3(검색 엔진) + Phase 4(근거 판정)를 구현한 search/engine.py의 얇은 래퍼.
이전 버전은 지도학습 분류 모델(model/*.py)을 썼지만, 요구사항 명세서 확인 후
"근거 없이 임의 답변 생성 금지" 원칙과 맞지 않아 검색/유사도 기반으로 교체했다.

입력: 담당자가 입력한 민원 텍스트
출력: {"근거수준": "매뉴얼"|"참고사례"|"근거불충분"|"결과없음", "안내": str|None, "결과": [...]}
      - 매뉴얼: 공식 대응절차 그대로 (처리방법·참고사항·담당자 연락처 포함)
      - 참고사례: 매뉴얼엔 없지만 과거 반복 민원 이력 기반 참고 정보 (공식 대응 아님)
      - 근거불충분 / 결과없음: 명세서 문구 그대로, 임의로 답을 만들어내지 않음

사용 예:
    from app.recommend import recommend
    outcome = recommend("궁동에서 유기견을 발견했어요")
    print(outcome["근거수준"])
    for r in outcome["결과"]:
        print(r["부서"], r["민원유형"])
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from search.engine import SearchEngine  # noqa: E402
from search.followup import get_followup  # noqa: E402

_engine = None


def _get_engine() -> SearchEngine:
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine


def recommend(text: str) -> dict:
    return _get_engine().search(text)


_EXCEPTION_NUM = "0"


def _ask_followup(followup: dict, dept: str, contact: str) -> None:
    # "이 중 어디에도 안 맞음"은 매번 반복 작성하지 않고, 모든 역질문에 공통으로 붙인다.
    # 억지로 선택지 하나를 고르게 하지 않고, 애매하면 담당 부서로 직접 문의하도록
    # 안내하는 게 "근거 불충분 시 임의 답변 금지" 원칙과 일치한다.
    print(f"    ▶ {followup['질문']}")
    for opt in followup["선택지"]:
        print(f"      {opt['번호']}. {opt['label']}")
    print(f"      {_EXCEPTION_NUM}. 위 어디에도 해당하지 않음 / 애매함")
    try:
        choice = input("      선택 > ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n종료합니다.")
        return

    if choice == _EXCEPTION_NUM:
        print("    → 위 케이스에 해당하지 않는 예외 상황입니다.")
        print(f"      매뉴얼에 정확히 규정되지 않았으니, 임의로 안내하지 말고 {dept}에 직접 문의하세요.")
        if contact:
            print(f"      연락처: {contact}")
        return

    picked = next((opt for opt in followup["선택지"] if opt["번호"] == choice), None)
    if not picked:
        print("      (잘못된 선택입니다. 번호로 다시 입력해주세요)")
        return
    print(f"    → {picked['label']}")
    for line in picked["답변"].split("\n"):
        print(f"      {line}")
    if contact:
        print("    담당자:")
        for line in contact.split("\n"):
            print(f"      {line}")


def _print_result(text: str) -> None:
    print(f"\n민원: {text}")
    outcome = recommend(text)
    print(f"  [{outcome['근거수준']}]" + (f" {outcome['안내']}" if outcome["안내"] else ""))
    if not outcome["결과"]:
        return
    for r in outcome["결과"]:
        score = "키워드 정확매칭" if r["유사도"] is None else f"유사도 {r['유사도']}"
        print(f"  - [{r['tier']}] {r['민원유형']} (부서: {r['부서']}, {score})")

        # 주의: r["tier"]는 문서 자체의 고정 속성이라, 유사도만으로 "근거불충분"
        # 버킷에 들어간 매뉴얼 문서에도 "매뉴얼"로 찍혀있다. 되묻기는 키워드
        # 정확매칭(유사도=None)일 때만 확신을 갖고 띄워야 하므로 이걸로 판단한다.
        is_confirmed_manual = r["tier"] == "매뉴얼" and r["유사도"] is None
        followup = get_followup(r["부서"], r["민원유형"]) if is_confirmed_manual else None
        if followup:
            # 매뉴얼 원문 하나에 여러 세부 케이스가 섞여있는 항목은, 전체를 다 보여주는
            # 대신 되물어서 해당하는 부분만 짧게 안내한다 (search/followup.py 참고)
            _ask_followup(followup, r["부서"], r.get("담당자") or "")
            continue

        if r.get("관련문단"):
            print("    관련문단(매뉴얼 원문 전체):")
            for line in r["관련문단"].split("\n"):
                print(f"      {line}")
        if r.get("참고사항"):
            print("    참고사항:")
            for line in r["참고사항"].split("\n"):
                print(f"      {line}")
        if r.get("담당자"):
            print("    담당자:")
            for line in r["담당자"].split("\n"):
                print(f"      {line}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 예: python3 app/recommend.py "궁동에서 유기견을 발견했어요"
        _print_result(" ".join(sys.argv[1:]))
    else:
        print("민원 내용을 입력하세요. (빈 줄 입력 또는 Ctrl+C로 종료)")
        while True:
            try:
                text = input("\n민원 입력 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n종료합니다.")
                break
            if not text:
                print("종료합니다.")
                break
            _print_result(text)
