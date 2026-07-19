"""
민원내용 -> 처리부서 예측 v2 (하이브리드: 규칙 + ML)

v1(baseline) 대비 개선 시도:
1. 특성: char n-gram TF-IDF + word 1~2gram TF-IDF 결합
2. 모델: LinearSVC(하이퍼파라미터 탐색) + 확률 보정(CalibratedClassifierCV)
3. 규칙: 민원내용에 동(洞) 이름이 그대로 등장하면 해당 동 부서에 가점 (동 라벨은 텍스트에
   지역명이 그대로 나오는 비율이 44%뿐이라 "확정 규칙"이 아니라 "가점 신호"로만 사용)
4. 건수 4건 이하 초극소 클래스는 ML로 학습 자체가 불가능(사실상 과거 1~4번 발생) ->
   "기타(데이터부족)"로 묶어서 별도 보고 (모델이 아니라 매뉴얼/규칙으로 보완해야 하는 대상)
"""

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, top_k_accuracy_score
from sklearn.pipeline import FeatureUnion

from common import load_data, group_classes, dong_features, MIN_SAMPLES_FOR_ML


def main():
    df = load_data()
    df = group_classes(df)
    print(f"라벨링된 전체 건수: {len(df)}")
    print(f"ML 학습 클래스 수(건수 {MIN_SAMPLES_FOR_ML} 미만은 '기타(데이터부족)'): {df['y'].nunique()}")

    dong_list = [d for d in df["처리부서"].unique() if d.endswith("동")]

    X_text = df["민원내용"].astype(str)
    y = df["y"]

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
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

    y_pred = clf.predict(X_test)
    print("\n=== Top-1 성능 (v2) ===")
    print(classification_report(y_test, y_pred, zero_division=0))

    classes = clf.classes_
    y_proba = clf.predict_proba(X_test)
    y_test_idx = [list(classes).index(v) for v in y_test]
    top3 = top_k_accuracy_score(y_test_idx, y_proba, k=3, labels=range(len(classes)))
    print(f"Top-3 accuracy: {top3:.3f}")

    # 공통(다빈도) 부서 vs 희귀 부서 그룹별 top-1 정확도 비교
    common_depts = df["처리부서"].value_counts().head(10).index.tolist()
    mask_common = y_test.isin(common_depts)
    acc_common = (y_pred[mask_common.values] == y_test[mask_common].values).mean()
    acc_rare = (y_pred[~mask_common.values] == y_test[~mask_common].values).mean()
    print(f"\n상위 10개 다빈도 부서 top-1 정확도: {acc_common:.3f} (n={mask_common.sum()})")
    print(f"그 외 부서 top-1 정확도: {acc_rare:.3f} (n={(~mask_common).sum()})")

    # 데모: 예시 민원 3건에 대한 top-3 부서 추천
    print("\n=== 데모: top-3 부서 추천 ===")
    samples = X_test_text.sample(5, random_state=1)
    sample_tfidf = union.transform(samples)
    sample_dong = dong_features(samples, dong_list)
    sample_X = hstack([sample_tfidf, sample_dong]).tocsr()
    proba = clf.predict_proba(sample_X)
    for i, (idx, text) in enumerate(samples.items()):
        top3_idx = np.argsort(proba[i])[::-1][:3]
        ranked = [(classes[j], round(proba[i][j], 3)) for j in top3_idx]
        print(f"- 민원: {text[:40]}...")
        print(f"  실제부서: {y_test.loc[idx]}")
        print(f"  추천순위: {ranked}")


if __name__ == "__main__":
    main()
