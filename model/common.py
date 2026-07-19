"""
model/ 아래 스크립트(baseline_dept_classifier, dept_classifier_v2, hybrid_router,
train_and_save)가 공유하는 데이터 로딩/전처리 함수. 각 스크립트에 거의 동일한 코드가
복붙되어 있던 것을 한 곳으로 모았다 — 로직을 바꿀 때 한 곳만 고치면 되게 하기 위함.

DATA_DIR은 이 파일(model/common.py) 위치를 기준으로 계산한다. 프로젝트 폴더를
옮기거나 다른 PC에서 클론해도 절대경로를 다시 손볼 필요가 없다.
"""

import glob
import re

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

DATA_DIR = Path(__file__).resolve().parent.parent
MIN_SAMPLES_FOR_ML = 5


def load_data() -> pd.DataFrame:
    files = sorted(glob.glob(str(DATA_DIR / "*.xlsx")))
    dfs = [pd.read_excel(f, header=1) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df = df.dropna(subset=["민원내용", "처리부서"]).copy()
    df["처리부서"] = df["처리부서"].astype(str).str.strip()
    return df


def group_classes(
    df: pd.DataFrame,
    min_samples: int = MIN_SAMPLES_FOR_ML,
    label_col: str = "y",
    other_label: str = "기타(데이터부족)",
) -> pd.DataFrame:
    """건수가 min_samples 미만인 부서를 other_label로 묶어 label_col에 저장한다."""
    counts = df["처리부서"].value_counts()
    too_rare = counts[counts < min_samples].index
    df[label_col] = df["처리부서"].where(~df["처리부서"].isin(too_rare), other_label)
    return df


def dong_features(texts: pd.Series, dong_list: list[str]) -> csr_matrix:
    """민원내용에 각 동 이름이 포함되는지를 0/1 sparse feature로 변환"""
    arr = np.zeros((len(texts), len(dong_list)), dtype=float)
    for j, dong in enumerate(dong_list):
        arr[:, j] = texts.str.contains(re.escape(dong), na=False).astype(float) * 3.0
    return csr_matrix(arr)
