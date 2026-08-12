"""최종 산출물을 모두 읽어 data/metadata/dataset_summary.json 으로 집계한다."""
import json
import csv
import pandas as pd

manual_cases = json.load(open("data/manual/manual_cases.json", encoding="utf-8"))
manual_sections = json.load(open("data/manual/manual_sections.json", encoding="utf-8"))
cleaning_report = json.load(open("data/metadata/cleaning_report.json", encoding="utf-8"))
recurring_summary = json.load(open("data/metadata/recurring_candidates_summary.json", encoding="utf-8"))
complaints = pd.read_csv("data/complaints/complaints_clean.csv")
page_mapping = list(csv.DictReader(open("data/metadata/pdf_page_mapping.csv", encoding="utf-8")))

summary = {
    "manual": {
        "source_document": "당직 근무요령 및 상황별 매뉴얼 (대전광역시 유성구, 2026.5.)",
        "total_pdf_pages": 85,
        "pages_excluded_no_content": len([r for r in page_mapping if r["처리여부"] == "제외"]),
        "manual_cases_count": len(manual_cases),
        "manual_cases_disaster": len([c for c in manual_cases if c["category"] in ("자연재난", "사회재난")]),
        "manual_cases_complaint": len([c for c in manual_cases if c["category"] == "당직민원처리"]),
        "manual_sections_count": len(manual_sections),
    },
    "complaints": {
        "years": [2024, 2025, 2026],
        "original_rows_total": cleaning_report["combined"]["total_original_rows"],
        "final_rows_total": cleaning_report["combined"]["total_final_rows"],
        "final_rows_by_year": complaints.groupby("연도").size().to_dict(),
        "per_year_detail": {y: cleaning_report[y] for y in ["2024", "2025", "2026"]},
    },
    "recurring_complaint_candidates": {
        "candidates_generated": recurring_summary["candidates_generated"],
        "manual_covered_estimate": recurring_summary["manual_covered_estimate"],
        "uncovered_total": recurring_summary["uncovered_total"],
        "review_completed": recurring_summary.get("review_completed", False),
        "review_approved_candidates": recurring_summary.get("review_approved_candidates"),
        "review_rejected_candidates": recurring_summary.get("review_rejected_candidates"),
        "final_recurring_types": recurring_summary.get("final_recurring_types_after_merge"),
        "final_recurring_types_total_count": recurring_summary.get("final_recurring_types_total_count"),
        "status": ("검수 완료, recurring_cases.json에 최종 유형 등록됨"
                    if recurring_summary.get("review_completed")
                    else "사람 검수 대기 (recurring_review.csv 확인 후 승인된 건만 recurring_cases.json에 등록 예정)"),
    },
    "personal_info_handling": {
        "private_dir_git_tracked": None,  # 최종 검증 단계에서 채움
        "redacted_contact_matches_in_manual": None,  # 최종 검증 단계에서 채움
    },
}

with open("data/metadata/dataset_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
