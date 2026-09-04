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
# 개인정보 스크러빙 (3차 버전)
#
# [1차 버전의 버그] 이름과 전화번호가 "같은 줄"에 있을 때만 이름을 마스킹했는데,
# pdfplumber가 표를 일반 텍스트로 풀면 셀이 줄바꿈으로 쪼개져서
#   042)611-2485
#   박종필
#   010-9437-7140
# 처럼 이름이 전화번호와 다른 줄에 오는 경우가 훨씬 많았다. 이 경우 이름이 전혀
# 마스킹되지 않고 그대로 새고 있었다(육안 재검수 중 사용자가 34페이지 "비상연락망"
# 표에서 16명의 실명이 그대로 노출된 걸 발견). tables_by_page(구조화된 표, 행 단위
# 검사)는 원래도 정상 마스킹되고 있었으나 content_by_page(일반 텍스트, 같은 표 내용을
# 다시 담고 있음)에는 이 버그가 있었음 -> 검색엔진이 content_by_page를 그대로
# 색인하므로 실사용 노출 위험이 있었음.
#
# [2차 버전의 버그] 위를 고친 뒤에도 "노진용(2804 / 010-...)"(이름 바로 뒤에 괄호),
# "정용길(공동모금회) [마스킹]"(이름+주석 뒤에 마스킹 마커), "박재현 팀장 010-..."
# (이름과 마스킹 사이에 직급 단어가 낀 경우) 같은 변형 패턴에서 여전히 실명이 샜다
# (사용자가 26페이지 발췌본에서 "구청장 전번", "김보미" 등 추가로 직접 발견).
#
# [최종 수정] 아래 5개 규칙을 순서대로 적용한다.
#  ① 휴대전화(모든 줄) 마스킹
#  ② "구청장"/"부구청장"/"비서실장"/"비서관"처럼 특정 1인을 가리키는 직책과 같은
#     줄에 있는 유선번호는(부서 공용 내선번호와 달리 개인 직통번호로 보고) 마스킹
#  ③ "이름(부가정보)" 패턴 - 괄호 안 또는 괄호 직후 근처에 연락처 흔적이 있을 때만
#     이름을 마스킹(괄호 안에 유선번호가 있으면 그것도 같이 마스킹)
#  ④ 이름이 전화번호와 다른 줄에 있거나("표가 텍스트로 풀리며 줄바꿈"), 부서명
#     뒤에 붙어있는 경우("건설과 전기팀 박영호") - 앞뒤 줄에 연락처 흔적이 있으면 마스킹
#  ⑤ "박재현 팀장 [마스킹]"처럼 이름과 마스킹 마커 사이에 직급 단어가 끼어있는
#     경우 - 마커 바로 앞의 좁은 범위만 역방향으로 훑어서 마스킹(범위를 최소화해
#     무관한 문장이 오탐되는 걸 방지)
# 마스킹 방식은 "○○○"(전체 삭제) 대신 가운데 글자만 가리는 방식 사용(성씨·부서
# 맥락은 유지, 요구사항 검수 피드백 반영).
# ---------------------------------------------------------------------------
MOBILE_RE = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")
LOCAL_WITH_MOBILE_RE = re.compile(r"\d{2,4}-\d{3,4}\((01[016789]-?\d{3,4}-?\d{4})\)")
LANDLINE_RE = re.compile(r"\d{2,4}\)\d{3,4}-\d{3,4}|(?<!\d)\d{2,4}-\d{3,4}-\d{4}(?!\d)")
SINGLE_PERSON_TITLES = ("구청장", "부구청장", "비서실장", "비서관")
NAME_LINE_RE = re.compile(r"^[가-힣]{2,4}$")
TRAILING_NAME_RE = re.compile(r"(?:^|[\s])([가-힣]{2,4})$")
ORG_SUFFIX_RE = re.compile(r"(과|실|팀|국|장|관|부|처|청|회|단|본|동)$")  # 이걸로 끝나면 부서/직책/지명일 확률이 높음
JOB_TITLE_WORDS = {"팀장", "주무관", "과장", "국장", "계장", "반장", "사무관", "주사", "실장"}
NAME_STOPWORDS = {
    "담당부서", "성명", "연락처", "수행비서", "당직사령", "상황근무자", "재난안전상황실", "비서관", "담당자",
    "통보", "작성", "보고", "결정", "전파", "복구", "가동", "안내", "협조", "요청", "파악", "조치", "연락",
    "이용", "설치", "확인", "전송", "처리", "완료", "진행", "준비", "점검", "시행", "적용", "운영", "관리",
    "지원", "제공", "실시", "확대", "축소", "종료", "시작", "상황파악", "현장확인", "즉시", "긴급",
    "유선보고", "처리방법", "답변",
    # 크로스필터 재검증(3글자 이상 한글은 전부 이름 의심 → 마커/표 근접 등으로 교차검증)
    # 중 "마커 바로 앞 단어는 이름"이라는 근접 휴리스틱이 실제로는 이름이 아닌 4글자
    # 안팎의 재난유형·업무 분류어를 붙잡아 마스킹하던 구체 사례들. 표(redact_table)는
    # '성명' 헤더 컬럼으로 위치를 제한해서 해결했지만, 같은 내용이 흐르는 텍스트
    # (content_by_page)에도 중복 추출되어 있어 거기서는 위치 정보가 없어 위치 기반으로
    # 못 거른다 - 그래서 이 표는 실제로 발견된 오탐 단어를 하나씩 불용어로 추가한다.
    "대형사고", "유출사고", "대형화재", "등록바람", "동물병원", "전달사항", "인적사고",
    "자연재난", "사회재난", "비고", "방법", "소음", "먼지", "전역", "발송바람", "숙박시설",
    # "*(먼지)이연주 / 611-2352(010-...)"처럼 "(카테고리)이름 / 번호" 구조에서, 지역번호+
    # 휴대폰이 하나의 마커로 합쳐지며 우연히 이름과 가까워져 "(먼지)"까지 이름으로 오인된
    # 사례(자매 단어 "소음"은 이미 등록돼 있었는데 "먼지"는 누락돼 있었음 - 육안 재검수로 발견).
    # "투투모텔"/"초원모텔"처럼 정확히 4글자인 숙박시설명이 NAME_PAREN_RE의 {2,4} 범위에
    # 꼭 맞아떨어져서 이름으로 오인된 사례(5글자인 "상아장모텔"은 범위를 넘어가 우연히
    # 안전했음 - 글자 수 우연으로 결과가 갈리는 건 근본적으로 불안정하므로 구체 단어를 등록)
    "투투모텔", "초원모텔",
}
# "펫레스규 (이진호, [마스킹])"처럼 앞 단어와 "(" 사이에 공백이 하나 끼는 표기도 있어서
# \s? 로 공백 0~1개를 허용한다(엄격하게 붙어있는 경우만 잡으면 이 변형에서 괄호 안쪽
# 이름 검사 자체가 실행되지 않아 그대로 샌 사례를 발견함).
NAME_PAREN_RE = re.compile(r"(?<![가-힣])([가-힣]{2,4})\s?\(([^)]{0,40})\)")
# "박민호(1992.01.30.)"처럼 이름 뒤 생년월일이 붙는 경우(노숙인/여비 상습수령자 명단 등에서
# 발견 - 전화번호보다 훨씬 민감한 개인식별정보라 별도 패턴으로 잡는다)
BIRTHDATE_RE = re.compile(r"(19|20)\d{2}\.\s?\d{1,2}\.\s?\d{1,2}\.?")
ISOLATED_HANGUL_RE = re.compile(r"(?<![가-힣])[가-힣]{2,4}(?![가-힣])(?!\d)")
# NAME_PAREN_RE는 "(" 바로 앞이 2~4자 한글일 때만 매칭되는데, "야생생물관리협회(민학기,
# 010-...)"나 "재해구호담당자(사회돌봄과 김영두)"처럼 "(" 앞이 5자 이상 이어지는 기관명/
# 직책명이면 애초에 매칭 대상이 아니라서 안쪽의 진짜 이름을 검사조차 못 하고 그대로 샌
# 사례를 육안 재검수로 발견했다(요구사항: search 색인용 텍스트에 실명이 남아있으면 안 됨).
# ANY_PAREN_RE는 "(" 앞 글자 수 제한 없이 모든 괄호를 잡아서, 괄호 "안쪽"의 선두/후미
# 이름 패턴만 별도로 검사한다(괄호 앞 단어는 보지 않으므로 길이 제한이 문제가 안 됨).
ANY_PAREN_RE = re.compile(r"\(([^)]{0,60})\)")
MARKER = "[개인 연락처 비공개]"
contacts_found = []
identified_names_by_page = {}  # {page_num: {원본이름, ...}} - 연락처 근거로 한 번 식별된 이름은
# 같은 페이지 안에서 연락처 없이 또 나와도(예: 각주에 이름만 다시 언급) 마스킹하기 위해 기록


def _remember_name(name, page_num):
    identified_names_by_page.setdefault(page_num, set()).add(name)


def mask_name(name):
    """이름을 가운데 글자만 가려서 마스킹(예: 박문용 -> 박*용, 김보 -> 김*)."""
    name = name.strip()
    if len(name) <= 1:
        return name
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def _is_name_like(tok):
    return tok not in NAME_STOPWORDS and not ORG_SUFFIX_RE.search(tok)


def _mask_mobiles_in_line(line, page_num):
    original = line
    redacted = line
    for m in LOCAL_WITH_MOBILE_RE.finditer(original):
        contacts_found.append({"page": page_num, "raw_line": original, "matched": m.group(0)})
        redacted = redacted.replace(m.group(0), MARKER)
    for m in MOBILE_RE.finditer(redacted):
        contacts_found.append({"page": page_num, "raw_line": original, "matched": m.group(0)})
    redacted = MOBILE_RE.sub(MARKER, redacted)
    return redacted


def _mask_title_landlines_in_line(line, page_num):
    if not any(t in line for t in SINGLE_PERSON_TITLES):
        return line

    def _sub(m):
        contacts_found.append({"page": page_num, "raw_line": line, "matched": m.group(0)})
        return MARKER

    return LANDLINE_RE.sub(_sub, line)


def _mask_name_paren(line, page_num):
    """'이름(부가정보)' 패턴: 괄호 안 또는 괄호 직후 근처에 연락처 흔적이 있을 때만
    이름을 마스킹한다. 괄호 안에 유선번호가 있으면 그것도 같이 마스킹."""

    def _sub(m):
        name, inner = m.group(1), m.group(2)
        # 괄호 "안쪽"이 "이름 / 부가정보" 또는 "이름, 부가정보" 형태면, 바깥쪽 name이
        # 이름처럼 생겼든 아니든(업체명 등도 이름처럼 오인될 수 있음) 상관없이 먼저 이
        # 안쪽 이름부터 확인한다. 순서를 바꾼 이유: "레스큐(이진호, [마스킹])"에서
        # "레스큐"가 이름 판정 규칙을 통과해버려서(조직 접미사로 안 끝남) 바깥쪽만
        # 마스킹되고 정작 안쪽의 진짜 이름 "이진호"는 검사조차 안 되고 그대로 샌 사례를
        # 크로스필터 재검증으로 발견함 - "구조담당자(김명덕 / ...)"처럼 바깥쪽이 설명어라
        # 이름이 아닌 경우만 다루면 이런 유형(바깥쪽이 이름처럼 보이는 오탐)을 놓친다.
        inner_m = re.match(r"^([가-힣]{2,4})\s*[/,]\s*(.*)$", inner)
        if inner_m and _is_name_like(inner_m.group(1)):
            inner_name, rest = inner_m.group(1), inner_m.group(2)
            has_evidence = MARKER in rest or LANDLINE_RE.search(rest) or BIRTHDATE_RE.search(rest)
            if has_evidence:
                contacts_found.append({"page": page_num, "raw_line": line, "matched": m.group(0)})
                _remember_name(inner_name, page_num)
                new_rest = LANDLINE_RE.sub(MARKER, rest)
                sep = inner[len(inner_m.group(1)):len(inner_m.group(1)) + (len(inner) - len(inner_m.group(1)) - len(rest))]
                return f"{name}({mask_name(inner_name)}{sep}{new_rest})"
        after = line[m.end(): m.end() + 20]
        has_birthdate = bool(BIRTHDATE_RE.search(inner))
        has_marker_or_landline = bool(MARKER in inner or LANDLINE_RE.search(inner))
        has_evidence_inside = has_marker_or_landline or has_birthdate
        has_evidence_after = MARKER in after
        if not (has_evidence_inside or has_evidence_after):
            return m.group(0)

        # "이승재 동물병원(...)"처럼 실제 이름 뒤에 업체/기관명이 한 번 더 붙어 "(" 바로
        # 앞 단어(동물병원)만 매치되고 진짜 이름(이승재)을 놓치는 경우 대응: 매치 시작
        # 직전이 공백 하나를 사이에 둔 또 다른 이름 후보면 그것도 같이 마스킹한다.
        before = line[max(0, m.start() - 6): m.start()]
        pm = re.search(r"(?<![가-힣])([가-힣]{2,4}) $", before)
        prefix_is_name = bool(pm and _is_name_like(pm.group(1)))
        is_name = _is_name_like(name)

        # "행정안전부 상황실(044-205-1540)"처럼 이름이 전혀 없는 순수 조직/부서 전화번호까지
        # 마스킹해버린 사례를 육안 재검수로 발견했다("상황실"은 조직접미사라 이름 아님으로
        # 정확히 판정됐지만, 그 뒤 "이름이 없어도 유선번호가 있으면 마스킹한다"는 이전 로직이
        # 남아있어서 실제로는 마스킹돼버렸음). "이름이 근처에 확인될 때만" 마스킹하도록,
        # 바깥쪽(name)과 앞쪽(pm) 둘 다 이름이 아니면 - 즉 이 괄호가 누구의 것인지 특정할
        # 근거가 없으면 - 유선번호/생년월일까지 있어도 원문을 그대로 둔다(마커만 있는 경우는
        # 예외: 마커는 이미 앞선 휴대전화 마스킹 단계를 거쳤다는 뜻이라 개인 정보일 확률이
        # 매우 높음 - 다만 마스킹할 "이름"이 없으니 어차피 여기선 더 할 일이 없다).
        if not (is_name or prefix_is_name):
            return m.group(0)

        contacts_found.append({"page": page_num, "raw_line": line, "matched": m.group(0)})
        new_inner = LANDLINE_RE.sub(MARKER, inner) if LANDLINE_RE.search(inner) else inner
        # 생년월일은 연락처보다 민감한 개인식별정보라 이름과 별도로 항상 마스킹
        if has_birthdate:
            new_inner = BIRTHDATE_RE.sub("[생년월일 비공개]", new_inner)

        prefix = ""
        if prefix_is_name:
            contacts_found.append({"page": page_num, "raw_line": line, "matched": pm.group(1)})
            _remember_name(pm.group(1), page_num)
            prefix = mask_name(pm.group(1)) + " "
        masked_name = mask_name(name) if is_name else name
        if is_name:
            _remember_name(name, page_num)
        if prefix:
            return (prefix, masked_name, new_inner, pm.start(1))
        return f"{masked_name}({new_inner})"

    # 위에서 튜플을 반환한 경우(이름 앞에 또 다른 이름이 붙은 경우) 그 앞부분까지
    # 함께 치환해야 하므로 일반 re.sub 대신 직접 순회하며 조립한다.
    out = []
    last_end = 0
    for m in NAME_PAREN_RE.finditer(line):
        if m.start() < last_end:
            continue
        result = _sub(m)
        if isinstance(result, tuple):
            prefix, masked_name, new_inner, extra_start = result
            out.append(line[last_end:extra_start])
            out.append(f"{prefix}{masked_name}({new_inner})")
        else:
            out.append(line[last_end:m.start()])
            out.append(result)
        last_end = m.end()
    out.append(line[last_end:])
    return "".join(out)


def _mask_names_inside_any_paren(text, page_num):
    """NAME_PAREN_RE가 놓치는 두 가지 경우를 보강한다("(" 앞 글자 수 제한이 없는
    ANY_PAREN_RE 사용, 괄호 앞쪽은 안 보고 괄호 "안쪽"만 검사하므로 안전):

    (a) 괄호 안쪽 선두 이름 - "야생생물관리협회(민학기, 010-...)": "(" 바로 앞 단어가
        8자짜리 기관명이라 NAME_PAREN_RE의 {2,4} 범위를 넘어가 아예 매칭이 안 됐다.
    (b) 괄호 안쪽 후미 이름 - "재해구호담당자(사회돌봄과 김영두)": 이름이 괄호 맨 앞이
        아니라 부서명 뒤에 붙어 있고, 이 괄호 자체엔 연락처 흔적이 없다(증거는 같은 줄
        바로 뒤에 이어지는 "(042-611-2927 / [마스킹])"에 있음) - 그래서 이 괄호가 끝난
        직후 근처(짧은 범위)에 증거가 있으면 이름으로 보고 마스킹한다.
        범위를 "같은 줄 전체"로 잡으면 "(진잠동 일대) 야생생물관리협회(민학기, [마스킹])"
        처럼 뒤쪽 전혀 다른 괄호의 증거 때문에 앞쪽 괄호의 "일대"(그냥 "그 지역"이라는
        뜻)까지 이름으로 오인해서 잘못 마스킹되는 걸 실측으로 확인함 - 그래서 "이 괄호
        직후"로 범위를 좁혔다(뒤쪽 증거만 보고, 괄호 앞쪽/훨씬 뒤쪽은 안 봄).
    두 경우 다 이름이 실제로 개인정보 노출로 이어진 사례를 육안 재검수로 확인하고 추가함.
    """

    def _sub(m):
        inner = m.group(1)

        lead_m = re.match(r"^([가-힣]{2,4})\s*[/,]\s*(.+)$", inner)
        if lead_m and _is_name_like(lead_m.group(1)):
            lname, rest = lead_m.group(1), lead_m.group(2)
            if MARKER in rest or LANDLINE_RE.search(rest) or BIRTHDATE_RE.search(rest):
                _remember_name(lname, page_num)
                contacts_found.append({"page": page_num, "raw_line": text, "matched": m.group(0)})
                sep = inner[len(lname): len(inner) - len(rest)]
                new_rest = LANDLINE_RE.sub(MARKER, rest)
                return f"({mask_name(lname)}{sep}{new_rest})"

        trail_m = re.search(r"(?:^|\s)([가-힣]{2,4})$", inner)
        if trail_m and _is_name_like(trail_m.group(1)):
            # BIRTHDATE_RE는 여기서는 증거로 안 쓴다 - "관내 주요공사현장 연락처(2025.8.5
            # 기준)"처럼 일반 날짜("YYYY.M.D" 형식)에도 반응해서, 뒤에 오는 흔한 단어
            # "기준"까지 이름으로 오인해 마스킹하는 오탐이 실제로 발생함(생년월일이 붙는
            # 실제 사례는 전부 이름이 괄호 "맨 앞"에 오는 다른 함수(_mask_name_paren)에서
            # 이미 처리되고, 여기(후미 이름 규칙)에는 필요 없었음).
            local_evidence = bool(MARKER in inner or LANDLINE_RE.search(inner))
            after = text[m.end(): m.end() + 20]
            nearby_evidence = bool(MARKER in after or LANDLINE_RE.search(after))
            if local_evidence or nearby_evidence:
                tname = trail_m.group(1)
                _remember_name(tname, page_num)
                contacts_found.append({"page": page_num, "raw_line": text, "matched": m.group(0)})
                new_inner = inner[: trail_m.start(1)] + mask_name(tname)
                return f"({new_inner})"

        return m.group(0)

    return ANY_PAREN_RE.sub(_sub, text)


def _mask_job_title_names(line, page_num):
    """'박재현 팀장 [마스킹]'처럼 마커 바로 앞이 직급 단어(팀장/주무관 등)면 그 앞의
    이름까지 한 번 더 거슬러 올라가 마스킹한다(범위를 마커 직전으로 최소화해 무관한
    문장이 오탐되는 걸 방지)."""
    out = line
    search_from = 0
    for m in list(re.finditer(re.escape(MARKER), line)):
        window = line[search_from: m.start()]
        toks = list(ISOLATED_HANGUL_RE.finditer(window))
        cand = None
        if toks:
            last = toks[-1]
            if last.group(0) in JOB_TITLE_WORDS and len(toks) >= 2:
                prev = toks[-2]
                if last.start() - prev.end() <= 2 and _is_name_like(prev.group(0)):
                    cand = prev
            elif _is_name_like(last.group(0)) and window[last.end():].strip() == "":
                # 원래 "마커로부터 3글자 이내"였는데, 이러면 "디아델] ☎[마스킹]"처럼
                # 이름이 아닌 고유명사/일반단어와 마커 사이에 문장부호·기호(]☎* 등)만 끼어
                # 있어도 걸려버린다(교차 필터링 재검증 중 "디아델"(아파트명), "레스큐"
                # (업체명), "소음"/"단지"/"비고" 등 실명이 아닌 단어가 다수 오탐된 걸 발견).
                # 이름이 마커 바로 앞에 "붙어있다"고 볼 수 있는 경우는 공백만 있을 때뿐이므로,
                # 사이에 공백 아닌 문자가 하나라도 있으면 후보에서 제외한다.
                cand = last
        if cand:
            contacts_found.append({"page": page_num, "raw_line": line, "matched": cand.group(0)})
            _remember_name(cand.group(0), page_num)
            abs_start = search_from + cand.start()
            abs_end = search_from + cand.end()
            out = out[:abs_start] + mask_name(cand.group(0)) + out[abs_end:]
        search_from = m.end()
    return out


def redact_text(text, page_num):
    lines = text.split("\n")
    lines = [_mask_title_landlines_in_line(_mask_mobiles_in_line(l, page_num), page_num) for l in lines]
    lines = [_mask_name_paren(l, page_num) for l in lines]
    # ANY_PAREN_RE 기반 보강 패스는 반드시 "줄 단위"로 호출한다(page_num 전체 텍스트를
    # 합쳐서 돌리면 line_has_evidence가 페이지 전체 기준이 되어, 이 이름과 무관한 다른
    # 문단의 괄호까지 "증거 있음"으로 오판해 광범위하게 오탐될 위험이 있음 - 실제 사고
    # 사례("재해구호담당자(사회돌봄과 김영두)")는 같은 "줄" 안에 유선번호가 있어서
    # 줄 단위로 좁혀도 정상적으로 잡힌다).
    lines = [_mask_names_inside_any_paren(l, page_num) for l in lines]

    # 이름이 전화번호와 다른 줄에 있는 경우(표가 텍스트로 풀리면서 줄바꿈됨) 대응.
    # 창(window)은 바로 위/아래 1줄만 본다 - 2줄까지 보면 "경우"처럼 흔한 단어가 우연히
    # 2줄 뒤의 무관한 마스킹 근처에 걸려서 오탐되는 걸 실측으로 확인함(예: "...경우"로
    # 끝나는 문장이 2줄 뒤 다른 사람 이름의 마스킹된 연락처 때문에 이름으로 오인되어
    # "경*"로 깨짐, 그리고 이게 전역 재마스킹으로 같은 페이지의 다른 "경우"까지 전부 오염시킴).
    # 실제 표-텍스트 변환 패턴("이름"과 "연락처"가 줄바꿈만으로 분리)은 항상 바로 인접한
    # 줄이었으므로 ±1로 좁혀도 정상 케이스는 그대로 잡힌다.
    for i, line in enumerate(lines):
        stripped = line.strip()
        if NAME_LINE_RE.match(stripped) and _is_name_like(stripped):
            window = lines[max(0, i - 1): i] + lines[i + 1: i + 2]
            if any(MARKER in w or LANDLINE_RE.search(w) for w in window):
                lines[i] = mask_name(stripped)
                _remember_name(stripped, page_num)
                continue
        m = TRAILING_NAME_RE.search(line)
        if m and not NAME_LINE_RE.match(stripped) and len(stripped) <= 20:
            tok = m.group(1)
            if _is_name_like(tok):
                window = lines[max(0, i - 1): i] + lines[i + 1: i + 2] + [line]
                if any(MARKER in w or LANDLINE_RE.search(w) for w in window):
                    lines[i] = line[: m.start(1)] + mask_name(tok)
                    _remember_name(tok, page_num)

    # 이름과 마스킹된 연락처가 같은 줄에 붙어있는 경우(예: "비서관, 수행비서 [마스킹]")
    for i, line in enumerate(lines):
        if MARKER not in line:
            continue

        def _sub_inline(mm):
            token = mm.group(0)
            if not _is_name_like(token):
                return token
            _remember_name(token, page_num)
            return mask_name(token)

        # (?<![가-힣]) 경계 체크 필수: 이게 없으면 "상아장모텔("처럼 5글자 단어 중간부터
        # 4글자("아장모텔")만 잘라 매칭해버린다(단어 앞에 한글이 더 있는지 확인 안 하면
        # 정규식이 "가장 뒤쪽에서 시작하는 유효한 2~4글자 부분열"을 아무거나 찾아버림 -
        # 크로스필터 재검증으로 "상아**텔" 오염을 발견하고서야 이 함수엔 경계 체크가 아예
        # 없었다는 걸 확인함. 같은 파일의 다른 이름 탐지 정규식들은 전부 이 체크가 있었음).
        lines[i] = re.sub(r"(?<![가-힣])[가-힣]{2,4}(?=\s*[/\(]?\s*\[개인 연락처 비공개\])", _sub_inline, line)

    # 마커가 다음 줄로 넘어가는 경우도 있어("이름 직급\n[마스킹]") 줄 단위가 아니라
    # 합쳐진 전체 텍스트에 대해 마지막으로 한 번 더 훑는다(줄바꿈은 한글이 아니므로
    # ISOLATED_HANGUL_RE의 경계 판정에 영향 없음).
    result = _mask_job_title_names("\n".join(lines), page_num)

    # 같은 페이지 안에서 이미 연락처 근거로 식별된 이름이 다른 곳(각주 등, 연락처 없이
    # 이름만 다시 언급되는 경우)에 마스킹 없이 또 나오면 그것도 마스킹한다.
    # 예: "이승재 동물병원([마스킹])"에서 식별된 "이승재"가 바로 아래 각주
    # "*이승재 동물병원: 야간, 휴일진료 가능..."에 연락처 근거 없이 또 나오는 경우.
    for name in identified_names_by_page.get(page_num, set()):
        result = re.sub(rf"(?<![가-힣]){re.escape(name)}(?![가-힣])", mask_name(name), result)
    return result


CELL_NAME_LEAD_RE = re.compile(r"^([가-힣]{2,4})((?:\([^)]{0,40}\))?)$")
# 위 정규식은 반드시 "이름" 또는 "이름(설명)"이 셀 전체와 정확히 일치할 때만 매칭한다
# (문자열 끝 $ 고정). 처음에 (.*)로 뒤를 열어뒀더니 "녹지산림과\n도시숲팀"처럼 긴
# 단어/구절이 든 셀에서 앞 2~4글자만("녹지산림") 잘려 이름처럼 오인되는 문제가
# 광범위하게 발생했다(부서명·도로명·학교명·업체명 다수 오염 - 교차 필터링 재검증으로 발견).
# "셀 전체가 정확히 이름 모양"이라는 조건으로 좁히면 이런 긴 텍스트는 애초에 $ 앵커에서
# 매칭 실패하므로 안전하다.


NAME_HEADER_RE = re.compile(r"^성\s*명$|^이\s*름$")


def _find_name_column(table):
    """표의 헤더 행에서 '성명'/'이름' 컬럼의 위치(인덱스)를 찾는다.

    처음에는 "행에 연락처 증거가 있으면 그 행의 모든 셀 중 이름처럼 생긴 걸 마스킹"하는
    식으로 했더니, "도로명"(주소 표기 방식을 나타내는 표 값), "재난유형" 컬럼의
    "자연재난"/"인적사고" 같은 분류어, "비고" 헤더 자체까지 전부 이름으로 오인해서
    마스킹해버리는 광범위한 오탐이 발생했다(크로스필터 재검증으로 발견). 이런 값은 전부
    이름 컬럼이 아니라 "주소 종류"/"분류"/"비고" 등 다른 컬럼에 있었다는 공통점이 있다.
    그래서 셀 내용만으로 이름 여부를 추측하는 대신, 헤더에서 실제 "성명"/"이름" 컬럼을
    먼저 찾고 그 컬럼에만 이름 마스킹을 적용하는 방식으로 바꿨다. 헤더를 못 찾으면(성명
    컬럼이 아예 없는 표 - 예: 업체 연락처 목록) None을 반환해서 그 표는 셀 추측 마스킹을
    아예 안 하도록 한다(원문 훼손보다 놓치는 쪽이 낫다는 원칙 - 놓친 이름은
    PII_REVIEW_26PAGES.md 육안 재검수로 잡는다)."""
    for row in table[:3]:  # 헤더는 보통 표의 처음 몇 줄 안에 있음
        for idx, cell in enumerate(row):
            if isinstance(cell, str) and NAME_HEADER_RE.match(cell.strip()):
                return idx
    return None


def redact_table(table, page_num):
    """표는 pdfplumber가 셀 단위로 쪼개서 주는데, '이름'과 '연락처'가 같은 행(row)의
    서로 다른 셀에 나뉘어 들어가는 경우가 많다(예: [None, '백병희(긴급복지지원)',
    '[개인 연락처 비공개]'] - 이름 셀과 마커 셀이 다름). 셀 단위로만 "이 셀 안에 증거가
    있는가"를 보면 이런 경우를 놓친다(실제로 3차 수정 이후에도 육안 재검수 없이 크로스필터
    스캔을 돌려서 이 패턴으로 샌 이름을 다시 발견함). 그래서 먼저 각 셀을 개별적으로
    마스킹한 뒤, "행 전체에 증거(마커/전화번호 패턴)가 있는가"를 다시 판단하고, 있으면
    표에서 찾은 '성명' 컬럼의 셀에 한해서만 "이름(부가정보)" 또는 "이름" 선두 패턴을
    추가로 마스킹한다(컬럼 제한 없이 하면 위 _find_name_column 설명대로 광범위 오탐)."""
    if not table:
        return table
    name_col = _find_name_column(table)
    redacted_rows = []
    for row in table:
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                cell = _mask_title_landlines_in_line(_mask_mobiles_in_line(cell, page_num), page_num)
                cell = _mask_name_paren(cell, page_num)
            new_row.append(cell)
        row_has_evidence = any(
            isinstance(c, str) and (MARKER in c or LANDLINE_RE.search(c) or BIRTHDATE_RE.search(c))
            for c in new_row
        )
        if row_has_evidence and name_col is not None and name_col < len(new_row):
            def _mask_cell(c):
                if not isinstance(c, str):
                    return c
                stripped = c.strip()
                if MARKER in stripped or not stripped:
                    return c
                if re.fullmatch(r"[가-힣]{2,4}", stripped):
                    if not _is_name_like(stripped):
                        return c
                    _remember_name(stripped, page_num)
                    return mask_name(stripped)
                # "백병희(긴급복지지원)"처럼 이름 뒤에 부가정보 괄호가 붙은 셀 - 마커가
                # 다른 셀에 있어서 이 셀 안에서는 증거를 못 찾지만, 행 전체엔 증거가
                # 있으므로(row_has_evidence) 선두 이름은 마스킹한다.
                m = CELL_NAME_LEAD_RE.match(stripped)
                if m and _is_name_like(m.group(1)):
                    _remember_name(m.group(1), page_num)
                    contacts_found.append({"page": page_num, "raw_line": c, "matched": m.group(1)})
                    return mask_name(m.group(1)) + m.group(2)
                return c
            new_row[name_col] = _mask_cell(new_row[name_col])
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
