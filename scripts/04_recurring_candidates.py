"""
데이터_요청사항.pdf 7,8번 요구사항: 반복 민원 유형 분석.

절차(요구사항 문서 그대로):
  전체 민원 -> 공식 매뉴얼에서 이미 처리 가능한 유형 확인 -> 매뉴얼에 없는 민원 추출
  -> 빈도분석/TF-IDF/클러스터링으로 후보 생성 -> 사람이 실제 사례 확인 -> 검수
  -> 승인된 유형만 반복 민원으로 등록

이 스크립트는 "사람이 실제 사례 확인" 앞 단계까지만 수행한다.
클러스터링 결과를 그대로 최종 유형으로 등록하는 것은 요구사항 문서가 명시적으로 금지하고
있고, 실제 담당자가 아닌 내가 각 클러스터가 진짜 동일 민원 유형인지 판단할 근거가 없으므로,
모든 후보의 review_result 는 "pending_user_review"로 남기고 recurring_cases.json 은
사용자 승인 전까지 빈 배열로 유지한다.
"""
import json
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

df = pd.read_csv("data/complaints/complaints_clean.csv")
cases = json.load(open("data/manual/manual_cases.json"))

complaint_cases = [c for c in cases if c["category"] == "당직민원처리"]

# 1) 매뉴얼이 이미 다루는 (부서, 제목 키워드) 조합 구성
covered_rules = []
for c in complaint_cases:
    dept = c["departments"][0]
    title_tokens = re.split(r"[,\s/·()]+", c["title"])
    title_tokens = [t for t in title_tokens if len(t) >= 2]
    covered_rules.append({"case_id": c["id"], "department": dept, "tokens": title_tokens})


def is_manual_covered(row):
    dept = row["처리부서_표준"]
    text = str(row["민원내용_원본"])
    for rule in covered_rules:
        if rule["department"] == dept and any(tok in text for tok in rule["tokens"]):
            return rule["case_id"]
    return None

df["manual_case_id"] = df.apply(is_manual_covered, axis=1)
covered = df[df["manual_case_id"].notna()]
uncovered = df[df["manual_case_id"].isna()].copy()

print(f"전체: {len(df)} / 매뉴얼 커버 추정: {len(covered)} / 미커버(클러스터링 대상): {len(uncovered)}")

# 2) 미커버 민원에 대해 부서 단위로 나눠 TF-IDF + KMeans 후보 생성
#    (부서가 다르면 같은 단어가 나와도 다른 업무이므로 부서별로 분리해서 클러스터링한다)
candidates = []
MIN_DEPT_SIZE = 15  # 이 미만이면 클러스터링 의미가 적어 후보 생성 생략
for dept, group in uncovered.groupby("처리부서_표준"):
    if pd.isna(dept) or len(group) < MIN_DEPT_SIZE:
        continue
    texts = group["민원내용_원본"].astype(str).tolist()
    n_clusters = max(2, min(8, len(group) // 20))
    try:
        vec = TfidfVectorizer(max_features=500, token_pattern=r"(?u)\b\w{2,}\b")
        X = vec.fit_transform(texts)
        if X.shape[1] < n_clusters:
            continue
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        terms = vec.get_feature_names_out()
        for k in range(n_clusters):
            idx = [i for i, l in enumerate(labels) if l == k]
            if len(idx) < 10:
                continue
            center = km.cluster_centers_[k]
            top_terms = [terms[i] for i in center.argsort()[::-1][:6]]
            sample_idx = idx[:5]
            candidates.append({
                "candidate_type_hint": " / ".join(top_terms[:3]),
                "department": dept,
                "candidate_count": len(idx),
                "top_terms": top_terms,
                "review_sample_count": len(sample_idx),
                "sample_complaints": group["민원내용_원본"].astype(str).iloc[sample_idx].tolist(),
                "review_result": "pending_user_review",
                "reviewer_note": "",
            })
    except ValueError:
        continue

candidates.sort(key=lambda c: -c["candidate_count"])

# 3) 검수용 CSV (사람이 열어서 승인/반려를 적을 자료)
import csv
with open("data/metadata/recurring_review.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["candidate_type_hint", "department", "candidate_count", "top_terms",
                "review_sample_count", "sample_complaint_1", "sample_complaint_2",
                "review_result", "reviewer_note"])
    for c in candidates:
        samples = c["sample_complaints"] + ["", ""]
        w.writerow([c["candidate_type_hint"], c["department"], c["candidate_count"],
                    "|".join(c["top_terms"]), c["review_sample_count"],
                    samples[0][:200], samples[1][:200],
                    c["review_result"], c["reviewer_note"]])

# recurring_cases.json은 "승인된 유형만" 등록해야 하므로, 사람 검수 전에는 비워둔다.
with open("data/complaints/recurring_cases.json", "w", encoding="utf-8") as f:
    json.dump([], f, ensure_ascii=False, indent=2)

summary = {
    "total_complaints": len(df),
    "manual_covered_estimate": len(covered),
    "manual_covered_by_case": covered["manual_case_id"].value_counts().to_dict(),
    "uncovered_total": len(uncovered),
    "candidates_generated": len(candidates),
    "note": "candidate_count는 클러스터링 결과 추정치이며, review_result가 "
            "'approved'로 바뀌기 전까지는 확정된 반복 민원 유형이 아님",
}
with open("data/metadata/recurring_candidates_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"candidates: {len(candidates)}")
print("saved -> data/metadata/recurring_review.csv, data/complaints/recurring_cases.json(empty, pending review)")
