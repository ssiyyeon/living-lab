"""
PDF 원본(private/raw/original_manual.pdf)에서 페이지별 원문 텍스트/표를 그대로 추출한다.
- 원문을 요약/재작성하지 않고 pdfplumber가 추출한 텍스트를 그대로 저장한다.
- 출력은 private/working/ 아래(개인정보 미제거 상태이므로 public 저장소에는 올리지 않음).
- 85페이지 전수 처리 여부를 스스로 검증한다(누락 페이지 있으면 에러로 중단).
"""
import json
import pdfplumber

SRC = "private/raw/original_manual.pdf"
OUT = "private/working/pdf_pages_raw.json"

pages_out = []
with pdfplumber.open(SRC) as pdf:
    total_pages = len(pdf.pages)
    for i, page in enumerate(pdf.pages):
        page_num = i + 1
        text = page.extract_text() or ""
        tables = page.extract_tables()
        pages_out.append({
            "page": page_num,
            "text": text,
            "tables": tables,
            "char_count": len(text),
            "table_count": len(tables),
        })

assert len(pages_out) == total_pages
processed_pages = sorted(p["page"] for p in pages_out)
expected_pages = list(range(1, total_pages + 1))
missing = sorted(set(expected_pages) - set(processed_pages))
if missing:
    raise SystemExit(f"누락된 페이지 발견: {missing}")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({
        "source_file": SRC,
        "total_pages": total_pages,
        "processed_pages": processed_pages,
        "missing_pages": missing,
        "pages": pages_out,
    }, f, ensure_ascii=False, indent=2)

print(f"total_pages={total_pages} processed={len(processed_pages)} missing={missing}")
print(f"saved -> {OUT}")
