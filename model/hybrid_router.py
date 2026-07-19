"""
민원내용 -> 담당부서 추천 (하이브리드: 매뉴얼 규칙 + ML 모델)

1) 매뉴얼 키워드 규칙(manual/rule_lookup.py)에 먼저 매칭 시도
   -> 매칭되면 그 부서를 최우선 후보로 올림 (과거 데이터 건수와 무관하게 항상 동작)
2) 남은 후보 슬롯은 ML 모델(dept_classifier_v2와 동일 구성)의 top-N으로 채움
3) 순수 ML만 썼을 때(v2) 대비, 특히 '매뉴얼에 등재된 희귀 상황'에서 얼마나 개선되는지 비교 평가
"""

import sys
import os
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from manual.rule_lookup import match_manual

from common import load_data, group_classes, dong_features, MIN_SAMPLES_FOR_ML


def hybrid_top3(text: str, ml_top3: list[tuple[str, float]]) -> list[str]:
    hits = match_manual(text)
    ranked = []
    for h in hits:
        if h["부서"] not in ranked:
            ranked.append(h["부서"])
    for dept, _ in ml_top3:
        if dept not in ranked:
            ranked.append(dept)
        if len(ranked) >= 3:
            break
    return ranked[:3]


def main():
    df = load_data()
    df = group_classes(df)

    dong_list = [d for d in df["처리부서"].unique() if d.endswith("동")]

    X_text = df["민원내용"].astype(str)
    y = df["y"]

    X_train_text, X_test_text, y_train, y_test, dept_train, dept_test = train_test_split(
        X_text, y, df["처리부서"], test_size=0.2, random_state=42, stratify=y
    )

    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2)
    word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, token_pattern=r"(?u)\b\w+\b")
    union = FeatureUnion([("char", char_vec), ("word", word_vec)])
    X_train_tfidf = union.fit_transform(X_train_text)
    X_test_tfidf = union.transform(X_test_text)

    X_train_dong = dong_features(X_train_text, dong_list)
    X_test_dong = dong_features(X_test_text, dong_list)
    X_train = hstack([X_train_tfidf, X_train_dong]).tocsr()
    X_test = hstack([X_test_tfidf, X_test_dong]).tocsr()

    base_clf = LinearSVC(C=1.0, class_weight="balanced", max_iter=5000)
    clf = CalibratedClassifierCV(base_clf, cv=3)
    clf.fit(X_train, y_train)
    classes = clf.classes_
    proba = clf.predict_proba(X_test)

    # 평가는 ML 학습용으로 그룹핑된 y가 아니라, 실제(원본) 처리부서 라벨 기준으로 한다.
    # (그룹핑된 y로 비교하면 극희귀 부서가 전부 '기타'로 뭉개져서, 규칙이 실제 부서를
    #  정확히 맞혀도 오답으로 채점되는 문제가 있었음)
    truth_list = dept_test.tolist()
    text_list = X_test_text.tolist()
    rare_depts = set(df["처리부서"].value_counts()[df["처리부서"].value_counts() < MIN_SAMPLES_FOR_ML].index)

    ml_top1_correct = 0
    ml_top3_correct = 0
    hy_top1_correct = 0
    hy_top3_correct = 0

    manual_matched_idx = []
    rare_idx = []
    for i, text in enumerate(text_list):
        order = np.argsort(proba[i])[::-1]
        ml_ranked = [(classes[j], proba[i][j]) for j in order[:3]]
        ml_top3_list = [d for d, _ in ml_ranked]

        hy_ranked = hybrid_top3(text, ml_ranked)

        truth = truth_list[i]
        if ml_ranked[0][0] == truth:
            ml_top1_correct += 1
        if truth in ml_top3_list:
            ml_top3_correct += 1
        if hy_ranked[0] == truth:
            hy_top1_correct += 1
        if truth in hy_ranked:
            hy_top3_correct += 1

        if match_manual(text):
            manual_matched_idx.append(i)
        if truth in rare_depts:
            rare_idx.append(i)

    n = len(text_list)
    print(f"전체 테스트 건수: {n} (그중 ML 학습에서 '기타'로 묶인 극희귀 부서 정답 건수: {len(rare_idx)})")
    print(f"매뉴얼 규칙에 매칭된 건수: {len(manual_matched_idx)} ({len(manual_matched_idx)/n*100:.1f}%)")
    print()
    print("=== 전체 비교 (실제 부서명 기준) ===")
    print(f"ML만    - Top-1: {ml_top1_correct/n:.3f} / Top-3: {ml_top3_correct/n:.3f}")
    print(f"하이브리드 - Top-1: {hy_top1_correct/n:.3f} / Top-3: {hy_top3_correct/n:.3f}")

    if manual_matched_idx:
        m_ml1 = sum(1 for i in manual_matched_idx if classes[np.argmax(proba[i])] == truth_list[i])
        m_hy1 = sum(
            1 for i in manual_matched_idx
            if hybrid_top3(text_list[i], [(classes[j], proba[i][j]) for j in np.argsort(proba[i])[::-1][:3]])[0]
            == truth_list[i]
        )
        print()
        print(f"=== 매뉴얼 규칙 매칭된 건({len(manual_matched_idx)}건)만 top-1 비교 ===")
        print(f"ML만: {m_ml1/len(manual_matched_idx):.3f}  하이브리드: {m_hy1/len(manual_matched_idx):.3f}")

    if rare_idx:
        r_ml1 = sum(1 for i in rare_idx if classes[np.argmax(proba[i])] == truth_list[i])
        r_hy1 = sum(
            1 for i in rare_idx
            if hybrid_top3(text_list[i], [(classes[j], proba[i][j]) for j in np.argsort(proba[i])[::-1][:3]])[0]
            == truth_list[i]
        )
        print()
        print(f"=== 극희귀 부서(건수 {MIN_SAMPLES_FOR_ML} 미만, ML은 '기타'로만 예측) 건({len(rare_idx)}건) top-1 비교 ===")
        print(f"ML만: {r_ml1/len(rare_idx):.3f}  하이브리드: {r_hy1/len(rare_idx):.3f}")

    print()
    print("=== 데모 ===")
    demo_texts = [
        "궁동 근처에서 유기견을 발견했어요 구조 부탁드립니다",
        "도로에 포트홀이 생겨서 위험합니다",
        "아동학대가 의심되는 상황입니다 도와주세요",
        "노숙인 한 분이 역 앞에서 귀향여비를 요청하십니다",
    ]
    dtu = union.transform(pd.Series(demo_texts))
    ddo = dong_features(pd.Series(demo_texts), dong_list)
    dX = hstack([dtu, ddo]).tocsr()
    dproba = clf.predict_proba(dX)
    for i, t in enumerate(demo_texts):
        order = np.argsort(dproba[i])[::-1][:3]
        ml_ranked = [(classes[j], round(dproba[i][j], 3)) for j in order]
        hy = hybrid_top3(t, ml_ranked)
        print(f"- {t}")
        print(f"  ML top3: {ml_ranked}")
        print(f"  하이브리드 top3: {hy}")


if __name__ == "__main__":
    main()
