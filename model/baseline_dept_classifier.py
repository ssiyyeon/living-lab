"""
민원내용(자유텍스트) -> 처리부서 예측 베이스라인 모델

목적: 담당자가 민원 텍스트를 입력하면, 어느 부서가 담당할지(top-3)를 추천.
접근: 딥러닝 없이 TF-IDF(char n-gram) + Logistic Regression으로 베이스라인 성능 확인.
      한국어 형태소 분석기 없이도 char n-gram은 조사/어미 변화에 비교적 강건함.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, top_k_accuracy_score
from sklearn.pipeline import Pipeline

from common import load_data, group_classes

RARE_CLASS_THRESHOLD = 10  # 이보다 건수 적은 부서는 "기타"로 묶음


def main():
    df = load_data()
    print(f"라벨링된 전체 건수: {len(df)}")
    df = group_classes(df, min_samples=RARE_CLASS_THRESHOLD, label_col="처리부서_grouped", other_label="기타")
    print(f"그룹핑 후 클래스 수: {df['처리부서_grouped'].nunique()} "
          f"(건수 {RARE_CLASS_THRESHOLD} 미만 부서는 '기타'로 통합)")

    X = df["민원내용"].astype(str)
    y = df["처리부서_grouped"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2)),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\n=== Top-1 성능 ===")
    print(classification_report(y_test, y_pred, zero_division=0))

    classes = pipeline.classes_
    y_proba = pipeline.predict_proba(X_test)
    y_test_idx = [list(classes).index(v) for v in y_test]
    top3 = top_k_accuracy_score(y_test_idx, y_proba, k=3, labels=range(len(classes)))
    print(f"Top-3 accuracy (top 3 부서 후보 안에 정답 포함될 확률): {top3:.3f}")


if __name__ == "__main__":
    main()
