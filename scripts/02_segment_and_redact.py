"""
private/working/pdf_pages_raw.json(85페이지 원문 추출본)을 입력으로 받아 계층 구조를 살려서
manual_sections.json / manual_cases.json 을 만든다.

[이 버전으로 다시 짠 이유]
1차 버전은 목차의 8개 섹션을 전부 "같은 레벨의 플랫한 리스트"로 취급하고, 그 밑에서
케이스가 아닌 페이지에는 내가 임의로 지어낸 라벨(예: "(개요/보고기준)")을 붙였다.
실제로는 8개 섹션 중 다수가 내부에 자체 하위구조(①~⑥ 번호, Ⅰ/Ⅱ/Ⅲ 로마숫자, 1./2.
번호, 심지어 26페이지처럼 자체 표지+48/52페이지처럼 자체 목차표를 가진 것)를 갖고 있었고,
이를 무시하고 플랫하게 쪼개면서 두 가지 실수가 생겼다:
  - "재난상황 시 당직사령..." 섹션(p26)이 별도 표지 페이지를 갖는 하위 매뉴얼이라는 걸
    놓치고 그냥 "일반 참고문서"로만 취급함
  - "당직근무 민원처리 매뉴얼" 섹션의 케이스 경계를 정규식(부서명 브라켓 + "민원요지")으로만
    잡다 보니, 52페이지 자체에 있는 "부서별/민원상황/페이지" 자체 목차표와 다르게 분할됨
    (예: "무인민원발급기" 관련 3개 항목을 정규식으로는 1개로 잘못 병합)

그래서 이번 버전은:
  - 문서 전체를 실제로 다시 눈으로 읽고(하단 참고), 8개 섹션 내부의 진짜 하위구조를
    breadcrumb(조상 제목 목록)으로 모든 레코드에 남긴다.
  - "당직근무 민원처리 매뉴얼"의 케이스 경계는 정규식 대신 52페이지 자체 목차표를
    pdfplumber로 직접 읽어서(=문서 스스로 선언한 목차) 그대로 사용한다.
"""
import json
import re
import csv
import math
from collections import Counter

RAW_PATH = "private/working/pdf_pages_raw.json"
DOC_TITLE = "당직 근무요령 및 상황별 매뉴얼"
SOURCE = "당직 근무요령 및 상황별 매뉴얼 (대전광역시 유성구, 2026.5.)"
TOP = DOC_TITLE

with open(RAW_PATH, encoding="utf-8") as f:
    raw = json.load(f)
pages = {p["page"]: p for p in raw["pages"]}
assert raw["total_pages"] == 85

# ---------------------------------------------------------------------------
# 개인정보 스크러빙 (1차 버전과 동일한 규칙)
# ---------------------------------------------------------------------------
MOBILE_RE = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")
LOCAL_WITH_MOBILE_RE = re.compile(r"\d{2,4}-\d{3,4}\((01[016789]-?\d{3,4}-?\d{4})\)")
contacts_found = []


def redact_line(line, page_num):
    original = line
    redacted = line
    for m in LOCAL_WITH_MOBILE_RE.finditer(original):
        contacts_found.append({"page": page_num, "raw_line": original, "matched": m.group(0)})
        redacted = redacted.replace(m.group(0), "[개인 연락처 비공개]")
    for m in MOBILE_RE.finditer(redacted):
        contacts_found.append({"page": page_num, "raw_line": original, "matched": m.group(0)})
    redacted = MOBILE_RE.sub("[개인 연락처 비공개]", redacted)
    if "[개인 연락처 비공개]" in redacted and redacted != original:
        redacted = re.sub(r"[가-힣]{2,4}(?=\s*[/\(]?\s*\[개인 연락처 비공개\])", "○○○", redacted)
    return redacted


def redact_text(text, page_num):
    return "\n".join(redact_line(l, page_num) for l in text.split("\n"))


def redact_table(table, page_num):
    if not table:
        return table
    redacted_rows = []
    for row in table:
        new_row = [redact_line(cell, page_num) if isinstance(cell, str) else cell for cell in row]
        row_has_redacted_phone = any(isinstance(c, str) and "[개인 연락처 비공개]" in c for c in new_row)
        if row_has_redacted_phone:
            new_row = [
                "○○○" if (isinstance(c, str) and re.fullmatch(r"[가-힣]{2,4}", c.strip())) else c
                for c in new_row
            ]
        redacted_rows.append(new_row)
    return redacted_rows


def page_record(pnum, breadcrumb):
    page = pages[pnum]
    return {
        "page": pnum,
        "breadcrumb": breadcrumb,
        "content": redact_text(page["text"], pnum),
        "tables": [redact_table(t, pnum) for t in page["tables"]] if page["tables"] else [],
        "document_title": DOC_TITLE,
        "source": SOURCE,
        "evidence_level": "official_manual",
    }


# ---------------------------------------------------------------------------
# 담당부서 원문(departments_raw) -> 배열(departments) 파싱
#
# 근거: 데이터_요청사항.pdf 3장 예시 케이스("지하차도 침수시 조치요령" = manual_case_003)의
# 실제 원문은 "재난안전상황실(상황근무자) 건설과(전기팀, 하수팀)"이고, 문서가 제시한 정답은
# "departments": ["건설과 전기팀", "건설과 하수팀"] 이다. 이 정답과 원문을 대조해서 아래
# 두 가지 규칙을 역산했다:
#   1. "OO과"/"OO실" 뒤에 괄호가 오면, 괄호 안 내용을 그 부서 소속 팀으로 보고
#      "OO과 팀명" 형태로 펼친다. 괄호 안에 쉼표로 여러 팀이 있으면 각각 별도 항목으로 분리.
#   2. "재난안전상황실"은 실제로 현장에 나가 조치하는 부서가 아니라 상황을 보고받는 창구라서
#      최종 departments 배열에서는 제외한다(원문에는 남기고 departments_raw로 보존).
# 이 규칙으로 manual_case_003을 실제로 돌려서 위 정답과 정확히 일치하는지 아래 assert로
# 검증한다(라인 참고: "assert parse_departments(...) 검증" 블록).
# ---------------------------------------------------------------------------
DEPT_TOKEN_RE = re.compile(r"([가-힣0-9]+(?:과|실))(?:\(([^)]*)\))?")
DEPT_EXCLUDE = {"재난안전상황실"}  # 실무 처리부서가 아니라 상황보고 창구 (위 근거 참고)


def parse_departments(raw):
    if not raw:
        return []
    result = []
    for name, detail in DEPT_TOKEN_RE.findall(raw):
        if name in DEPT_EXCLUDE:
            continue
        detail = detail.strip()
        if not detail:
            result.append(name)
            continue
        subs = [s.strip() for s in detail.split(",") if s.strip()]
        for s in subs:
            result.append(f"{name} {s}")
    return result


# ---------------------------------------------------------------------------
# 핵심 검색 키워드(keywords) 추출
#
# 근거: 위와 같은 case_003 예시의 keywords 정답은 ["지하차도","침수","배수펌프","배수로"]인데,
# 4개 전부 이 케이스 본문(content_by_page) 안에 문자 그대로 존재하는 단어임을 실측 확인했다
# (요구사항 3장 "원문의 의미를 AI가 새롭게 작성하지 않기" 원칙과 일치하려면 keywords도
# 본문에 실재하는 단어만 뽑아야 한다는 뜻으로 해석).
#
# 방식: 71개 문서(manual_cases + manual_sections) 전체를 코퍼스로 놓고, 각 문서 안에서
# "이 문서에는 자주 나오지만 다른 문서에는 잘 안 나오는 단어"에 높은 점수를 주는 방식
# (TF-IDF와 동일한 원리를 외부 라이브러리 없이 순수 파이썬으로 구현 - 새 의존성 추가 없음).
# 제목에 나온 단어는 가중치를 2배 줘서 우선순위를 높인다.
# ---------------------------------------------------------------------------
KEYWORD_STOPWORDS = {
    "조치요령", "발생시", "처리", "확인", "안내", "경우", "관련", "신고", "방법", "사항",
    "요청", "조치", "해당", "위치", "이후", "완료", "진행", "필요", "연락", "대응", "상황",
    "근무", "당직", "민원", "부서", "담당", "비고", "페이지", "성명", "연락처", "보고",
    "기준", "이내", "이상", "가능", "발생", "구분", "번호", "내용", "작성", "등록",
    "개인", "비공개",  # 개인정보 마스킹 문구("[개인 연락처 비공개]")가 키워드로 새는 것 방지
    "여부", "가장", "대하여", "아님", "정보", "빠른", "번", "제", "조",  # 조사성/기능어 잡음
}
# "OO시"(예: 침수시->침수)처럼 단어 뒤에 바로 붙은 시점 조사를 떼어내되, 너무 짧아지면
# (2자 미만) 원래 단어가 더 온전하므로 그대로 둔다.
KEYWORD_TRAILING_SUFFIXES = ("시에", "시")


def _strip_trailing_suffix(word):
    for suf in KEYWORD_TRAILING_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 2:
            return word[: -len(suf)]
    return word


def tokenize_for_keywords(text):
    # 순수 숫자/영문 조합(전화 내선번호, 법조문 번호, "17시"에서 시점조사를 뗀 뒤 남는 "17" 등)은
    # 검색 키워드로서 의미가 약해 제외한다. 조사 제거(_strip_trailing_suffix) 이후에
    # 한글 포함 여부를 다시 검사해야, 예를 들어 "17시" -> "17"처럼 조사를 뗀 결과가
    # 숫자만 남는 경우까지 걸러낼 수 있다(제거 전에만 검사하면 이 케이스를 놓친다).
    raw_tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
    tokens = [_strip_trailing_suffix(w) for w in raw_tokens]
    tokens = [w for w in tokens if re.search(r"[가-힣]", w)]
    return [w for w in tokens if w not in KEYWORD_STOPWORDS and len(w) >= 2]


def build_keywords_for_corpus(docs, top_n=8):
    """docs: [{"id": ..., "title": ..., "text": ...}, ...] -> {id: [keyword, ...]}"""
    doc_freq = Counter()
    per_doc_tokens = {}
    for d in docs:
        toks = set(tokenize_for_keywords(d["title"] + " " + d["text"]))
        per_doc_tokens[d["id"]] = toks
        doc_freq.update(toks)
    n_docs = len(docs)
    result = {}
    for d in docs:
        term_freq = Counter(tokenize_for_keywords(d["title"] + " " + d["text"]))
        title_tokens = set(tokenize_for_keywords(d["title"]))
        scored = []
        for tok, freq in term_freq.items():
            score = freq * math.log(n_docs / doc_freq[tok])
            if tok in title_tokens:
                score *= 2
            scored.append((score, tok))
        scored.sort(key=lambda x: (-x[0], x[1]))
        result[d["id"]] = [tok for score, tok in scored[:top_n] if score > 0]
    return result


# manual_case_003 앵커 검증: 요구사항 문서가 직접 제시한 정답과 일치하는지 확인
_anchor = parse_departments("재난안전상황실(상황근무자) 건설과(전기팀, 하수팀)")
assert _anchor == ["건설과 전기팀", "건설과 하수팀"], f"departments 파싱 앵커 검증 실패: {_anchor}"

# ---------------------------------------------------------------------------
# 1) 일반 참고 문서 구간의 계층 구조 (근거: private/raw/original_manual.pdf 를
#    Read 도구로 4~21p, 22~32p, 37~52p를 직접 눈으로 읽고 확인한 실제 제목/번호)
#    각 튜플: (시작p, 끝p, breadcrumb 마지막 항목들(리스트), skip 여부)
# ---------------------------------------------------------------------------
GENERAL_RANGES = [
    (1, 1, ["표지"], True),
    (2, 2, ["당직근무 타임라인별 정리"], False),
    (3, 3, ["목차"], True),
    # 1. 당직근무자 준수사항 (p4~15) - 내부에 2개 하위블록 존재
    (4, 6, ["당직근무자 준수사항", "당직근무 시 준수사항 (①~⑥번 항목)"], False),
    (7, 15, ["당직근무자 준수사항", "야간·휴일 재난시 상황전파 현황 보고"], False),
    # 2. 청사 보안 및 시건 (p16~20)
    (16, 20, ["청사 보안 및 시건"], False),
    # 3. 휴일 직원 비상연락 및 애사 문자통보 (p21)
    (21, 21, ["휴일 직원 비상연락 및 애사 문자통보"], False),
    # 4. 비상 발령 및 비상 소집 (p22~25) - ①~④ 4개 하위블록
    (22, 22, ["비상 발령 및 비상 소집", "① 비상발령 시 당직사령 임무"], False),
    (23, 23, ["비상 발령 및 비상 소집", "② 유성구 비상소집 연락체계도"], False),
    (24, 24, ["비상 발령 및 비상 소집", "③ 유성구 비상근무 요령"], False),
    (25, 25, ["비상 발령 및 비상 소집", "④ 유관기관 비상연락 체계도"], False),
    # 5. 재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼 (p26~48)
    #    p26은 이 소단원 자체의 표지(본문 전체 표지 p1과 같은 형식) - 별도 발견 사항
    (26, 26, ["재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼", "(하위 표지)"], False),
    (27, 27, ["재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼", "Ⅰ. 재난상황 발생시 조치요령"], False),
    (28, 31, ["재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼", "Ⅱ. 중요재난(상황)의 동시 보고 기준"], False),
    # Ⅲ. 재난유형별 행동매뉴얼의 "개요" 부분(가/나/다, 소규모/중규모/대규모 단계별 조치) -
    # 케이스(1-1~1-3, 2-1~2-7)는 아래 3)에서 별도 처리
    (32, 32, ["재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼", "Ⅲ. 재난유형별 행동매뉴얼",
              "1. 자연재난 발생시 조치요령(개요: 예비특보·주의보·경보 단계별)"], False),
    (37, 40, ["재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼", "Ⅲ. 재난유형별 행동매뉴얼",
              "2. 사회재난 발생시 조치요령(개요: 소규모·중규모·대규모 단계별, 부서별 재난담당)"], False),
    (48, 48, ["재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼", "재난관리 책임기관 연락체계도"], False),
    # 6. 당직근무일지 작성 (p49~50)
    (49, 50, ["당직근무일지 작성"], False),
    # 7. 당직민원 등록 (p51)
    (51, 51, ["당직민원 등록"], False),
    # 8. 당직근무 민원처리 매뉴얼 (p52~85) - p52는 이 섹션 자체의 목차표
    (52, 52, ["당직근무 민원처리 매뉴얼", "(부서별 민원상황 자체 목차표)"], False),
    # p85는 84p 케이스("이동식 차수판 대여")와 무관한 별개 부록 - 원문 대조로 확인함
    (85, 85, ["당직근무 민원처리 매뉴얼", "부록: 소화기 및 질식소화포 비치"], False),
]

manual_sections = []
sec_id_seq = 1
for start, end, tail, skip in GENERAL_RANGES:
    for pnum in range(start, end + 1):
        if skip:
            continue
        rec = page_record(pnum, [TOP] + tail)
        rec["id"] = f"manual_section_{sec_id_seq:03d}"
        rec["section"] = tail[-1]
        manual_sections.append(rec)
        sec_id_seq += 1

# ---------------------------------------------------------------------------
# 2) 재난유형별 행동매뉴얼 케이스 (p33~36 자연재난, p41~47 사회재난) - 정규식 분할
#    (이 구간은 "1-1.", "2-3." 처럼 케이스 헤딩이 명확해서 정규식으로도 데이터_요청사항.pdf의
#    예시(지하차도 침수, page 36~36)와 정확히 일치함을 이미 확인했음)
# ---------------------------------------------------------------------------
DISASTER_HEAD_RE = re.compile(r"^(\d)-(\d+)\.\s*(.+)$")
DISASTER_CASE_RANGES = [(33, 36), (41, 47)]


def split_disaster_cases(ranges):
    cases = []
    for start, end in ranges:
        current = None
        for pnum in range(start, end + 1):
            lines = [l for l in pages[pnum]["text"].split("\n") if l.strip()]
            first_line = lines[0] if lines else ""
            m = DISASTER_HEAD_RE.match(first_line)
            if m:
                if current:
                    cases.append(current)
                major, minor, title = m.groups()
                category = "자연재난" if major == "1" else "사회재난"
                parent_label = ("1. 자연재난 발생시 조치요령" if major == "1"
                                 else "2. 사회재난 발생시 조치요령")
                current = {
                    "case_no": f"{major}-{minor}", "title": title.strip(), "category": category,
                    "breadcrumb": [TOP, "재난상황 시 당직사령 및 재난상황실 상황요원 행동매뉴얼",
                                    "Ⅲ. 재난유형별 행동매뉴얼", parent_label],
                    "page_start": pnum, "page_end": pnum, "pages": [pnum],
                }
            else:
                if current is None:
                    raise SystemExit(f"disaster: page {pnum} has no open case -> {first_line!r}")
                current["page_end"] = pnum
                current["pages"].append(pnum)
        if current:
            cases.append(current)
    return cases


disaster_cases = split_disaster_cases(DISASTER_CASE_RANGES)

# 각 케이스의 "가. 근무사항" 담당부서 원문 라인을 departments_raw로 보관(파싱 왜곡 방지)
for case in disaster_cases:
    for pnum in case["pages"]:
        lines = pages[pnum]["text"].split("\n")
        for i, l in enumerate(lines):
            if "근무사항" in l and i + 1 < len(lines):
                case["departments_raw"] = lines[i + 1].strip()
                break
        if case.get("departments_raw"):
            break

# ---------------------------------------------------------------------------
# 3) 당직근무 민원처리 매뉴얼 케이스 (p53~84) - 52페이지 "자체 목차표"를 그대로 사용
#    근거: 52페이지 표 컬럼 [부서별, 민원상황, 페이지]. 이 "페이지"는 이 하위매뉴얼만의
#    내부 인쇄 페이지 번호이며, 실제 PDF 페이지와 대조한 결과 전 항목에서
#    "PDF페이지 = 표의 페이지 + 4" 로 정확히 일치함(21개 행 전수 검증).
#    부서 셀이 비어있는(세로병합) 행은 바로 위 행의 부서를 그대로 이어받는다.
# ---------------------------------------------------------------------------
PRINTED_TO_PDF_OFFSET = 4


def load_complaint_index_from_p52():
    table = pages[52]["tables"][0]
    rows = table[1:]  # 헤더 제외
    entries = []
    last_dept = None
    for row in rows:
        dept_cell, topic_cell, page_cell = row
        if not page_cell or not str(page_cell).strip().isdigit():
            continue  # 표 끝의 빈 행
        dept = dept_cell.replace("\n", ",") if dept_cell else last_dept
        last_dept = dept
        entries.append({
            "department": dept,
            "title": topic_cell.strip(),
            "pdf_page_start": int(page_cell.strip()) + PRINTED_TO_PDF_OFFSET,
        })
    return entries


complaint_index = load_complaint_index_from_p52()
complaint_index.sort(key=lambda e: e["pdf_page_start"])
COMPLAINT_LAST_PAGE = 84  # p85는 별개 부록(위 GENERAL_RANGES에서 처리)

complaint_cases = []
for i, entry in enumerate(complaint_index):
    start = entry["pdf_page_start"]
    end = (complaint_index[i + 1]["pdf_page_start"] - 1) if i + 1 < len(complaint_index) else COMPLAINT_LAST_PAGE
    complaint_cases.append({
        "title": entry["title"],
        "category": "당직민원처리",
        "department": entry["department"],
        "breadcrumb": [TOP, "당직근무 민원처리 매뉴얼"],
        "page_start": start, "page_end": end, "pages": list(range(start, end + 1)),
    })

# ---------------------------------------------------------------------------
# 4) manual_cases.json 조립
# ---------------------------------------------------------------------------
manual_cases = []
seq = 1
for c in disaster_cases:
    page_texts, page_tables = [], []
    for pnum in c["pages"]:
        page_texts.append({"page": pnum, "text": redact_text(pages[pnum]["text"], pnum)})
        if pages[pnum]["tables"]:
            page_tables.append({"page": pnum, "tables": [redact_table(t, pnum) for t in pages[pnum]["tables"]]})
    manual_cases.append({
        "id": f"manual_case_{seq:03d}", "case_no": c["case_no"], "title": c["title"],
        "category": c["category"], "breadcrumb": c["breadcrumb"],
        "page_start": c["page_start"], "page_end": c["page_end"],
        "departments_raw": c.get("departments_raw"),
        "departments": parse_departments(c.get("departments_raw")),
        "keywords": [],
        "content_by_page": page_texts, "tables_by_page": page_tables,
        "document_title": DOC_TITLE, "source": SOURCE, "evidence_level": "official_manual",
    })
    seq += 1

for c in complaint_cases:
    page_texts, page_tables = [], []
    for pnum in c["pages"]:
        page_texts.append({"page": pnum, "text": redact_text(pages[pnum]["text"], pnum)})
        if pages[pnum]["tables"]:
            page_tables.append({"page": pnum, "tables": [redact_table(t, pnum) for t in pages[pnum]["tables"]]})
    manual_cases.append({
        "id": f"manual_case_{seq:03d}", "case_no": None, "title": c["title"],
        "category": c["category"], "breadcrumb": c["breadcrumb"],
        "page_start": c["page_start"], "page_end": c["page_end"],
        "departments_raw": c["department"],
        "departments": [d.strip() for d in (c["department"] or "").split(",") if d.strip()],
        "keywords": [],
        "content_by_page": page_texts, "tables_by_page": page_tables,
        "document_title": DOC_TITLE, "source": SOURCE, "evidence_level": "official_manual",
    })
    seq += 1

# ---------------------------------------------------------------------------
# 4-1) keywords 채우기 (manual_cases + manual_sections 71건을 하나의 코퍼스로 취급)
# ---------------------------------------------------------------------------
_kw_docs = []
for c in manual_cases:
    _text = " ".join(p["text"] for p in c["content_by_page"])
    _kw_docs.append({"id": c["id"], "title": c["title"], "text": _text})
for s in manual_sections:
    _title = s["breadcrumb"][-1]
    _kw_docs.append({"id": s["id"], "title": _title, "text": s["content"]})

_keywords_by_id = build_keywords_for_corpus(_kw_docs)
for c in manual_cases:
    c["keywords"] = _keywords_by_id[c["id"]]
for s in manual_sections:
    s["keywords"] = _keywords_by_id[s["id"]]

# case_003 앵커 검증: 요구사항 문서 예시 키워드 4개(지하차도/침수/배수펌프/배수로)가
# ① 전부 본문에 실재하는 단어인지, ② 실제로 자동 추출된 keywords에 대부분 포함되는지 확인
_case3 = next(c for c in manual_cases if c["title"] == "지하차도 침수시 조치요령")
_case3_text = " ".join(p["text"] for p in _case3["content_by_page"])
_anchor_kw = ["지하차도", "침수", "배수펌프", "배수로"]
for _kw in _anchor_kw:
    assert _kw in _case3_text, f"keywords 앵커 검증 실패: '{_kw}'가 본문에 없음"
_matched = sum(1 for _kw in _anchor_kw if _kw in _case3["keywords"])
assert _matched >= 3, f"keywords 앵커 검증 실패: 자동추출 결과 {_case3['keywords']}에 정답 4개 중 {_matched}개만 포함"

# ---------------------------------------------------------------------------
# 5) 85페이지 전수 배정 검증 + pdf_page_mapping.csv
# ---------------------------------------------------------------------------
page_assignment = {}
for start, end, tail, skip in GENERAL_RANGES:
    for pnum in range(start, end + 1):
        if skip:
            page_assignment[pnum] = ("제외(내용없음)", "-", tail[-1])
        else:
            sec = next(s for s in manual_sections if s["page"] == pnum)
            page_assignment[pnum] = ("일반참고문서", sec["id"], " > ".join(tail))

for case in manual_cases:
    for pnum in range(case["page_start"], case["page_end"] + 1):
        page_assignment[pnum] = ("상황별대응매뉴얼", case["id"], case["title"])

all_pages = set(range(1, 86))
assigned_pages = set(page_assignment.keys())
missing = sorted(all_pages - assigned_pages)
if missing:
    raise SystemExit(f"배정되지 않은 페이지 발견: {missing}")

with open("data/metadata/pdf_page_mapping.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["page", "처리여부", "분류", "document_id", "비고"])
    for pnum in range(1, 86):
        classification, doc_id, note = page_assignment[pnum]
        처리여부 = "O" if classification != "제외(내용없음)" else "제외"
        w.writerow([pnum, 처리여부, classification, doc_id, note])

# ---------------------------------------------------------------------------
# 6) 저장
# ---------------------------------------------------------------------------
with open("data/manual/manual_cases.json", "w", encoding="utf-8") as f:
    json.dump(manual_cases, f, ensure_ascii=False, indent=2)
with open("data/manual/manual_sections.json", "w", encoding="utf-8") as f:
    json.dump(manual_sections, f, ensure_ascii=False, indent=2)
with open("private/contacts.json", "w", encoding="utf-8") as f:
    json.dump(contacts_found, f, ensure_ascii=False, indent=2)

print(f"disaster cases: {len(disaster_cases)}, complaint cases(52p 목차표 기반): {len(complaint_cases)}")
print(f"manual_cases: {len(manual_cases)}, manual_sections: {len(manual_sections)}")
print(f"redacted personal contacts found: {len(contacts_found)}")
print("85페이지 전수 배정 검증 통과")
