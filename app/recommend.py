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

_engine = None


def _get_engine() -> SearchEngine:
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine


def recommend(text: str) -> dict:
    return _get_engine().search(text)


def _print_result(text: str) -> None:
    print(f"\n민원: {text}")
    outcome = recommend(text)
    print(f"  [{outcome['근거수준']}]" + (f" {outcome['안내']}" if outcome["안내"] else ""))
    if not outcome["결과"]:
        return
    for r in outcome["결과"]:
        print(f"  - [{r['tier']}] {r['민원유형']} (부서: {r['부서']}, 유사도 {r['유사도']})")
        if r.get("관련문단"):
            print(f"    관련문단: {r['관련문단']}")
        if r.get("참고사항"):
            print(f"    참고사항: {r['참고사항']}")
        if r.get("담당자"):
            print(f"    담당자: {r['담당자']}")


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
