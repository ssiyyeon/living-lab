"""
private/raw 의 3개년 당직민원 엑셀을 원본은 절대 수정하지 않고 읽기만 하여,
1) 원본 현황(행/열/결측/중복)을 실측하고
2) 정제 결과를 data/complaints/complaints_clean.csv 로 저장하고
3) 무엇을 왜 제외했는지 data/metadata/cleaning_report.json 에 기록한다.

정제 원칙(데이터_요청사항.pdf 5,6번 요구사항 그대로 적용):
- 원본 컬럼은 반드시 보존한다 (민원내용_원본, 처리부서_원본 등 접미사로 유지).
- 부서명 등 "공백 차이"만 다른 값만 표준화한다. 조직 단위 자체가 다른 값
  (예: "건설과" vs "건설과 도로관리팀")은 임의로 합치지 않는다.
- 연도별 컬럼 구조 차이(2026년에만 당직구분/처리상태 컬럼 존재)는 표준 컬럼셋에
  없는 값은 결측으로 남기는 방식으로 흡수한다(임의 추정 금지).
"""
import json
import re
import pandas as pd

FILES = {
    2024: "private/raw/complaints_2024.xlsx",
    2025: "private/raw/complaints_2025.xlsx",
    2026: "private/raw/complaints_2026.xlsx",
}

STD_COLS = ["연도", "No_원본", "당직일자", "당직구분", "민원인명", "민원내용_원본",
            "당직자조치내용", "처리부서_원본", "처리상태", "출처파일"]


def load_raw(year, path):
    # 1행: 타이틀("당직민원 목록조회"), 2행: 실제 헤더 -> header=1(0-index)
    df = pd.read_excel(path, header=1, dtype=str)
    return df


def normalize_dept(v):
    """공백만 다듬는다. 조직 단위 자체를 합치는 로직은 넣지 않는다."""
    if pd.isna(v):
        return v
    return re.sub(r"\s+", "", str(v).strip())


report = {}
all_clean = []
raw_frames = {}

for year, path in FILES.items():
    df = load_raw(year, path)
    raw_frames[year] = df
    original_rows = len(df)
    columns = list(df.columns)

    # 원본 컬럼명은 연도별로 다를 수 있으므로(예: 2026만 당직구분/처리상태 존재)
    # 존재하는 컬럼만 표준 이름으로 매핑한다.
    col_map = {
        "No.": "No_원본", "당직일자": "당직일자", "당직구분": "당직구분",
        "민원인명": "민원인명", "민원내용": "민원내용_원본",
        "당직자조치내용": "당직자조치내용", "처리부서": "처리부서_원본",
        "처리상태": "처리상태",
    }
    df = df.rename(columns=col_map)

    blank_content = df["민원내용_원본"].isna() | (df["민원내용_원본"].astype(str).str.strip() == "")
    blank_dept = df["처리부서_원본"].isna() | (df["처리부서_원본"].astype(str).str.strip() == "")
    full_dup = df.duplicated(keep="first")

    n_blank_content = int(blank_content.sum())
    n_blank_dept = int((blank_dept & ~blank_content).sum())  # 내용은 있는데 부서만 빈 행 별도 카운트
    n_dup = int((full_dup & ~blank_content & ~blank_dept).sum())

    exclude_mask = blank_content | blank_dept | full_dup
    kept = df.loc[~exclude_mask].copy()

    # "_원본" 컬럼은 글자 하나도 건드리지 않는다(민원내용_원본에 .str.strip()을 적용하면
    # "_원본"이라는 이름과 달리 실제 원본과 달라지는 문제가 있었음 - 앞뒤공백 있는 행이
    # 3개년 합쳐 876건 존재했었다). 표준화가 필요하면 처리부서처럼 별도 "_표준" 컬럼을 만든다.
    kept["처리부서_표준"] = kept["처리부서_원본"].apply(normalize_dept)
    kept["연도"] = year
    kept["출처파일"] = path.split("/")[-1]

    for c in STD_COLS:
        if c not in kept.columns:
            kept[c] = pd.NA

    # 요구사항 5장 "부서명 표기 차이" / "조치내용 표기 차이" 체크 + 11장 "부서명 정규화 건수" 기록
    n_dept_normalized = int(
        (kept["처리부서_원본"].dropna().astype(str) != kept["처리부서_표준"].dropna().astype(str)).sum()
    )
    action_col = kept["당직자조치내용"]
    n_action_whitespace_diff = int(
        action_col.dropna().astype(str).apply(lambda s: s != s.strip()).sum()
    )

    all_clean.append(kept[STD_COLS + ["처리부서_표준"]])

    report[str(year)] = {
        "source_file": path,
        "original_rows": original_rows,
        "original_columns": columns,
        "removed_empty_complaint_text": n_blank_content,
        "removed_empty_department": n_blank_dept,
        "removed_duplicates": n_dup,
        "final_rows": len(kept),
        "department_name_normalized_count": n_dept_normalized,
        "action_text_whitespace_variance_count": n_action_whitespace_diff,
        "action_text_note": "당직자조치내용은 원본 컬럼 하나뿐이라 정제하지 않고 그대로 보존함"
                             "(표기 차이는 확인했으나 별도 표준 컬럼을 만들 필요가 없다고 판단)",
    }
    print(f"{year}: original={original_rows} final={len(kept)} "
          f"(blank_content={n_blank_content}, blank_dept_only={n_blank_dept}, dup={n_dup}, "
          f"dept_normalized={n_dept_normalized}, action_ws_diff={n_action_whitespace_diff})")

combined = pd.concat(all_clean, ignore_index=True)
combined.to_csv("data/complaints/complaints_clean.csv", index=False, encoding="utf-8-sig")

report["combined"] = {
    "total_original_rows": sum(r["original_rows"] for r in report.values()),
    "total_final_rows": len(combined),
    "years": list(FILES.keys()),
}

with open("data/metadata/cleaning_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\ncombined final rows: {len(combined)}")
print("saved -> data/complaints/complaints_clean.csv, data/metadata/cleaning_report.json")
