"""
프로젝트 전역에서 쓰는 데이터 로딩 함수. analysis/, search/ 스크립트가 공유한다.

DATA_DIR은 이 파일(프로젝트 루트의 common.py) 위치를 기준으로 계산하므로,
프로젝트 폴더를 옮기거나 다른 PC에서 클론해도 절대경로를 다시 손볼 필요가 없다.
"""

import glob
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent


def load_data() -> pd.DataFrame:
    files = sorted(glob.glob(str(DATA_DIR / "*.xlsx")))
    dfs = [pd.read_excel(f, header=1) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df = df.dropna(subset=["민원내용", "처리부서"]).copy()
    df["처리부서"] = df["처리부서"].astype(str).str.strip()
    return df
