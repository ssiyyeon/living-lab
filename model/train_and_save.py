"""
hybrid_router의 모델(char+word TF-IDF + 동 이름 피처 + CalibratedClassifierCV)을
학습해서 model/artifacts/에 저장한다.

매번 API 요청마다 재학습하지 않도록, 학습은 여기서 한 번만 하고
app/recommend.py는 저장된 아티팩트를 불러오기만 한다.
"""

import json

import joblib
from scipy.sparse import hstack
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC

from common import load_data, group_classes, dong_features, DATA_DIR

ARTIFACT_DIR = str(DATA_DIR / "model" / "artifacts")


def main():
    df = load_data()
    df = group_classes(df)
    dong_list = [d for d in df["처리부서"].unique() if d.endswith("동")]

    X_text = df["민원내용"].astype(str)
    y = df["y"]

    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2)
    word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, token_pattern=r"(?u)\b\w+\b")
    union = FeatureUnion([("char", char_vec), ("word", word_vec)])
    X_tfidf = union.fit_transform(X_text)

    X_dong = dong_features(X_text, dong_list)
    X = hstack([X_tfidf, X_dong]).tocsr()

    base_clf = LinearSVC(C=1.0, class_weight="balanced", max_iter=5000)
    clf = CalibratedClassifierCV(base_clf, cv=3)
    clf.fit(X, y)

    joblib.dump(union, f"{ARTIFACT_DIR}/union.joblib")
    joblib.dump(clf, f"{ARTIFACT_DIR}/classifier.joblib")
    with open(f"{ARTIFACT_DIR}/dong_list.json", "w", encoding="utf-8") as f:
        json.dump(dong_list, f, ensure_ascii=False)

    print(f"학습 완료: 전체 {len(df)}건, 클래스 {y.nunique()}개")
    print(f"저장 위치: {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
