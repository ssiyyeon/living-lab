"""
private/contacts.json(마스킹된 연락처 로그)을 기준으로, 실제 연락처가 있었던 페이지만
모아서 사람이 육안으로 재검수할 수 있는 PII_REVIEW_26PAGES.md를 생성한다.
data/manual/*.json 이 바뀔 때마다(특히 개인정보 마스킹 로직 수정 후) 다시 실행해서
최신 상태로 재생성해야 한다.
"""
import json

cases = json.load(open("data/manual/manual_cases.json", encoding="utf-8"))
sections = json.load(open("data/manual/manual_sections.json", encoding="utf-8"))
contacts = json.load(open("private/contacts.json", encoding="utf-8"))

pages_with_contacts = sorted({c["page"] for c in contacts})

blocks = []
for c in cases:
    for p in c["content_by_page"]:
        if p["page"] in pages_with_contacts:
            blocks.append((p["page"], f"{c['id']}", c["title"], p["text"]))
for s in sections:
    if s["page"] in pages_with_contacts:
        blocks.append((s["page"], f"manual_sections/{s['id']}", s["breadcrumb"][-1], s["content"]))

blocks.sort(key=lambda b: b[0])

lines = [
    "# 개인정보 마스킹 최종본 - 육안 확인용 (자동 재생성)",
    "",
    "> 85페이지 중 실제로 연락처가 있어서 마스킹 처리된 페이지만 모았습니다.",
    "> `[개인 연락처 비공개]`, `[생년월일 비공개]`, `이름 가운데 글자를 *로 가린 표기`가",
    "> 마스킹된 부분입니다. 이 외에 놓친 이름/번호/이메일 등이 있는지만 훑어봐주시면 됩니다.",
    f"> (`scripts/06_generate_pii_review.py`로 자동 생성, 대상 페이지 {len(pages_with_contacts)}개)",
    "",
]
seen_pages = set()
for page, doc_id, title, text in blocks:
    key = (page, doc_id)
    if key in seen_pages:
        continue
    seen_pages.add(key)
    lines.append(f"## p.{page} — {title} ({doc_id})")
    lines.append("")
    lines.append("```")
    lines.append(text)
    lines.append("```")
    lines.append("")

with open("PII_REVIEW_26PAGES.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"연락처가 있던 페이지 {len(pages_with_contacts)}개 -> PII_REVIEW_26PAGES.md 재생성 완료")
