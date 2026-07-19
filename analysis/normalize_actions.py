"""
당직자조치내용 정규화

원본 컬럼은 자유 텍스트라 "담당부서 이첩"류 표현이 띄어쓰기/단어선택(담당·해당·관련)
차이만으로 1,985개 unique 값으로 흩어져 있음. 실질적인 "조치 유형"은 훨씬 적으므로,
키워드 규칙으로 소수의 조치유형 카테고리로 정규화한다.

이 정규화 결과는:
- 조치유형별 통계(예: 부서 이첩 비율, 즉시조치 비율)를 볼 수 있게 해주고
- 나중에 민원내용 -> 조치유형을 보조로 예측하는 모델의 학습 라벨로도 쓸 수 있다.
"""

import glob
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent

# 우선순위대로 검사 (위에서부터 먼저 매칭되는 규칙 적용)
RULES = [
    ("펫레스큐 전달", ["펫레스큐", "펫레스규", "펫 레스큐", "펫레스킁"]),
    ("단속반 전달", ["단속반"]),
    ("재난상황실 안내/전달", ["재난상황실"]),
    ("부서 이첩/이관", ["이첩", "이첨", "이관", "전달", "인계", "지정"]),
    ("현장 조치/출동", ["출동", "현장조치", "현장 조치", "현장확인", "현장 확인"]),
    ("전화/문자 안내", ["문자 전송", "문자전송", "문자 발송", "문자발송", "전화 안내", "전화안내", "유선 안내"]),
    ("단순 접수/등록", ["접수", "등록"]),
    ("처리완료", ["처리완료", "처리 완료", "조치완료", "조치 완료", "전달완료", "전달 완료"]),
    ("안내", ["안내"]),
]


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", "", str(s))


def categorize(action: str) -> str:
    s = str(action)
    for category, keywords in RULES:
        for kw in keywords:
            if kw in s:
                return category
    return "기타(미분류)"


def load_data() -> pd.DataFrame:
    files = sorted(glob.glob(f"{DATA_DIR}/*.xlsx"))
    dfs = [pd.read_excel(f, header=1) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    return df


def main():
    df = load_data()
    actions = df["당직자조치내용"].dropna().astype(str)
    print(f"원본 unique 개수: {actions.nunique()}")
    print(f"공백 제거만 했을 때 unique 개수: {actions.map(normalize_whitespace).nunique()}")

    categories = actions.map(categorize)
    vc = categories.value_counts()
    print(f"\n규칙 기반 정규화 후 카테고리 수: {vc.shape[0]}")
    print(vc)
    print(f"\n전체 대비 커버리지: {(1 - vc.get('기타(미분류)', 0) / len(actions)) * 100:.1f}%")

    print("\n=== '기타(미분류)'로 남은 값 샘플 20개 ===")
    etc_samples = actions[categories == "기타(미분류)"].value_counts().head(20)
    print(etc_samples)

    out = df.copy()
    out["조치유형"] = out["당직자조치내용"].map(lambda x: categorize(x) if pd.notna(x) else None)
    out_path = f"{DATA_DIR}/analysis/action_categorized.csv"
    out[["당직일자", "민원내용", "당직자조치내용", "조치유형", "처리부서"]].to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    main()
