"""
Phase 2 — 반복 민원 유형 클러스터링

요구사항 명세서: "3개년 당직 민원 목록... 비슷한 민원끼리 묶어 반복 민원 유형과
유사 표현을 만들 예정. 매뉴얼에 없는 내용은 공식 대응으로 단정하지 않고
참고 사례로만 활용."

대상: 매뉴얼 규칙(manual/rule_lookup.match_manual)에 하나도 안 걸리는 민원만
클러스터링한다 — 매뉴얼이 이미 다루는 상황은 그쪽이 1순위 근거이므로 여기서
다시 묶을 필요가 없고, 이 스크립트의 목적은 정확히 "매뉴얼 사각지대"를 찾는 것.

방법: TF-IDF(char+word) + KMeans. 라벨(처리부서)은 클러스터링 자체에는 쓰지
않고, 결과 해석(이 클러스터가 실제로 어느 부서 업무인지)에만 사용한다 —
지도학습이 아니라 비지도 군집화라는 원칙을 지키기 위함.

출력: analysis/recurring_complaint_types.json — 클러스터별 대표 키워드,
건수, 주요 처리부서, 주요 조치유형, 예시 민원 몇 건. 이 파일은 실제 민원
원문을 담고 있어 .gitignore에 등록되어 있다 (공개 저장소에 올리지 않음).
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import FeatureUnion

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from common import load_data  # noqa: E402
from manual.rule_lookup import match_manual  # noqa: E402
from normalize_actions import categorize as categorize_action  # noqa: E402

OUT_PATH = PROJECT_ROOT / "analysis" / "recurring_complaint_types.json"
CANDIDATE_K = [15, 20, 30, 40, 50]
N_EXAMPLES = 3
N_KEYWORDS = 8

# 클러스터 대표 키워드에서 걸러낼 일반 조사/관용구/서식 잔재.
# (클러스터링 자체는 이 단어들을 포함한 전체 텍스트로 하고, "해석용 키워드 표시"에서만 제외)
STOPWORDS = {
    "민원", "요청", "관련", "확인", "부탁드립니다", "부탁드림", "바람", "및", "등", "함",
    "대한", "앞", "인근", "위치", "처리", "조치", "문의", "신고", "회신", "이라고", "합니다",
    "있음", "없음", "해주세요", "주시기", "바랍니다", "010", "042", "번지", "번길",
}


def get_uncovered(df):
    df = df.copy()
    df["매뉴얼매칭"] = df["민원내용"].astype(str).map(lambda t: bool(match_manual(t)))
    return df[~df["매뉴얼매칭"]].reset_index(drop=True)


def pick_k(X, candidates):
    """실루엣 점수로 후보 k 중 가장 나은 것을 고른다."""
    best_k, best_score = candidates[0], -1.0
    for k in candidates:
        km = KMeans(n_clusters=k, n_init=5, random_state=42)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels, sample_size=min(2000, X.shape[0]), random_state=42)
        print(f"  k={k}: silhouette={score:.4f}")
        if score > best_score:
            best_k, best_score = k, score
    return best_k


def top_keywords(word_vec, word_matrix, indices, n=N_KEYWORDS):
    sub = word_matrix[indices]
    mean_scores = np.asarray(sub.mean(axis=0)).ravel()
    vocab = np.array(word_vec.get_feature_names_out())
    order = np.argsort(mean_scores)[::-1]
    keywords = []
    for i in order:
        if mean_scores[i] <= 0:
            break
        word = vocab[i]
        # "요청 관련" 처럼 불용어를 포함한 2-gram도 걸러야 진짜 주제어만 남는다
        if any(tok in STOPWORDS for tok in word.split()):
            continue
        keywords.append(word)
        if len(keywords) >= n:
            break
    return keywords


def main():
    df = load_data()
    uncovered = get_uncovered(df)
    print(f"전체 라벨 건수: {len(df)} / 매뉴얼 미매칭(클러스터링 대상): {len(uncovered)}")

    texts = uncovered["민원내용"].astype(str)

    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2)
    word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, token_pattern=r"(?u)\b\w+\b")
    union = FeatureUnion([("char", char_vec), ("word", word_vec)])
    X = union.fit_transform(texts)
    word_matrix = word_vec.transform(texts)  # 대표 키워드 추출 전용(해석 가능하도록 word만 사용)

    print("\nk 후보 탐색 (silhouette score):")
    best_k = pick_k(X, CANDIDATE_K)
    print(f"선택된 k = {best_k}")

    km = KMeans(n_clusters=best_k, n_init=10, random_state=42)
    cluster_labels = km.fit_predict(X)
    uncovered["cluster"] = cluster_labels

    results = []
    for c in range(best_k):
        idx = np.where(cluster_labels == c)[0]
        if len(idx) == 0:
            continue
        sub = uncovered.iloc[idx]

        dept_counts = sub["처리부서"].dropna().astype(str).str.strip().value_counts()
        dept_top = dept_counts.index[0] if len(dept_counts) else None
        dept_share = round(dept_counts.iloc[0] / dept_counts.sum(), 3) if len(dept_counts) else None

        action_types = sub["당직자조치내용"].dropna().map(categorize_action).value_counts()
        action_top = action_types.index[0] if len(action_types) else None

        keywords = top_keywords(word_vec, word_matrix, idx)
        examples = sub["민원내용"].astype(str).sample(min(N_EXAMPLES, len(sub)), random_state=1).tolist()

        results.append({
            "cluster": int(c),
            "건수": int(len(sub)),
            "대표키워드": keywords,
            "주요처리부서": dept_top,
            "주요처리부서_비율": dept_share,
            "주요조치유형": action_top,
            "예시민원": examples,
            "근거수준": "참고사례",  # 명세서: 매뉴얼에 없는 내용은 공식 대응으로 단정하지 않음
        })

    results.sort(key=lambda r: r["건수"], reverse=True)

    print(f"\n=== 클러스터 {best_k}개, 건수 상위 15개 ===")
    for r in results[:15]:
        print(f"[{r['cluster']}] {r['건수']}건 | 키워드: {', '.join(r['대표키워드'])} "
              f"| 주요부서: {r['주요처리부서']}({r['주요처리부서_비율']}) | 주요조치: {r['주요조치유형']}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
