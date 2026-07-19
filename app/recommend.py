"""
웹사이트 백엔드에서 바로 호출할 수 있는 최종 추천 함수.

입력: 담당자가 입력한 민원 텍스트
출력: {"출처": "매뉴얼" | "ML예측(매뉴얼 미등재)", "안내": str, "결과": [...]}
      - 매뉴얼에 있는 상황이면 매뉴얼 기반 결과만 반환 (처리방법·참고사항·담당자 연락처 포함)
      - 매뉴얼에 없는 상황일 때만 ML 예측을 "참고용"으로 반환 (신뢰도만 있고 처리방법 없음)

사용 예:
    from app.recommend import recommend
    outcome = recommend("궁동에서 유기견을 발견했어요")
    print(outcome["출처"], outcome["안내"])
    for r in outcome["결과"]:
        print(r["부서"], r["근거"])
"""

import json
import os
import re

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_DIR = os.path.join(BASE_DIR, "model", "artifacts")

import sys
sys.path.insert(0, BASE_DIR)
from manual.rule_lookup import match_manual, load_situations

_union = None
_clf = None
_dong_list = None
_situations = None


def _load_artifacts():
    global _union, _clf, _dong_list, _situations
    if _union is None:
        _union = joblib.load(os.path.join(ARTIFACT_DIR, "union.joblib"))
        _clf = joblib.load(os.path.join(ARTIFACT_DIR, "classifier.joblib"))
        with open(os.path.join(ARTIFACT_DIR, "dong_list.json"), encoding="utf-8") as f:
            _dong_list = json.load(f)
        _situations = load_situations()


def _dong_features(text: str) -> csr_matrix:
    arr = np.zeros((1, len(_dong_list)), dtype=float)
    for j, dong in enumerate(_dong_list):
        if dong in text:
            arr[0, j] = 3.0
    return csr_matrix(arr)


def _ml_top3(text: str) -> list[tuple[str, float]]:
    x_tfidf = _union.transform([text])
    x_dong = _dong_features(text)
    x = hstack([x_tfidf, x_dong]).tocsr()
    proba = _clf.predict_proba(x)[0]
    order = np.argsort(proba)[::-1][:5]  # 필터링 후에도 3개를 채울 수 있게 넉넉히 뽑음
    classes = _clf.classes_
    return [(classes[i], float(proba[i])) for i in order]


def _situation_detail(dept: str, situation: str) -> dict | None:
    s = _situations.get((dept, situation))
    if not s:
        return None
    return {
        "민원요지": s["민원요지"],
        "처리방법": "\n".join(s["처리방법"][:15]),  # 너무 길면 앞부분만
        "참고사항": "\n".join(s["참고사항"][:10]),
        "담당자": s["담당자"][0] if s["담당자"] else "",
        "페이지": s["페이지"],
    }


def recommend(text: str) -> dict:
    """민원 텍스트를 받아 추천 결과를 반환한다.

    매뉴얼이 1순위 근거다: 직원은 실제로 매뉴얼을 근거로 대응하므로, 매뉴얼에 등재된
    상황이면 그 결과만 반환한다(신뢰도 낮은 ML 추측을 섞어서 헷갈리게 하지 않음).
    매뉴얼에 없는 완전히 새로운 상황일 때만 ML 예측을 "참고용"으로 보여준다.
    """
    _load_artifacts()

    manual_hits = match_manual(text)
    seen_depts = set()
    manual_results = []
    for hit in manual_hits:
        if hit["부서"] in seen_depts:
            continue
        detail = _situation_detail(hit["부서"], hit["민원요지"])
        manual_results.append({
            "부서": hit["부서"],
            "근거": f"매뉴얼 규칙 매칭 (키워드: '{hit['매칭키워드']}')",
            **(detail or {}),
        })
        seen_depts.add(hit["부서"])

    if manual_results:
        return {
            "출처": "매뉴얼",
            "안내": "매뉴얼에 등재된 상황입니다. 아래 대응절차를 따르세요.",
            "결과": manual_results,
        }

    ml_results = []
    for dept, prob in _ml_top3(text):
        if dept == "기타(데이터부족)":
            continue
        ml_results.append({
            "부서": dept,
            "근거": "ML 모델 예측 (과거 민원 데이터 기반, 매뉴얼 미등재)",
            "신뢰도": round(prob, 3),
        })
        if len(ml_results) >= 3:
            break

    return {
        "출처": "ML예측(매뉴얼 미등재)",
        "안내": "매뉴얼에 없는 상황으로 보입니다. 아래는 과거 민원 이력 기반 참고용 예측이며, "
                "담당자 판단으로 확인 후 처리하고 새로운 상황이라면 매뉴얼 업데이트를 건의하세요.",
        "결과": ml_results,
    }


def _print_result(text: str) -> None:
    print(f"\n민원: {text}")
    outcome = recommend(text)
    print(f"  [{outcome['출처']}] {outcome['안내']}")
    if not outcome["결과"]:
        print("  (추천할 부서를 찾지 못했습니다)")
        return
    for r in outcome["결과"]:
        line = f"  - [{r['부서']}] {r['근거']}"
        if "신뢰도" in r:
            line += f" (신뢰도 {r['신뢰도']})"
        print(line)
        if r.get("처리방법"):
            print(f"    처리방법: {r['처리방법']}")
            if r.get("참고사항"):
                print(f"    참고사항: {r['참고사항']}")
            print(f"    담당자: {r['담당자']}")


if __name__ == "__main__":
    import sys

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
