"""
data/manual/*.json, data/complaints/recurring_cases.json 을 검색 인덱스로 빌드한다.

방식: 실무에서 FAQ/매뉴얼 검색에 흔히 쓰는 "어휘 검색(BM25) + 의미 검색(임베딩) 하이브리드".
  - BM25: Elasticsearch/Lucene/Solr가 기본으로 쓰는 어휘 검색 알고리즘(rank_bm25 라이브러리).
    정확한 단어가 겹치면 강하게 반응하고, 문서 길이 정규화·단어 흔함(IDF) 보정이 들어있어
    단순 "키워드 포함 개수 세기"보다 "사람"처럼 흔한 단어의 오탐이 줄어든다.
  - 임베딩: 문장 의미를 벡터로 바꿔 코사인 유사도로 비교. "가스 터졌어요" ↔ "가스폭발"처럼
    단어 자체는 안 겹쳐도 뜻이 비슷하면 잡아낸다. 무료 로컬 모델(sentence-transformers,
    paraphrase-multilingual-MiniLM-L12-v2, 다국어 지원)을 써서 API 비용·네트워크 의존이 없다.

임베딩은 계산 비용이 있어 한 번 빌드해서 캐시(search/index/*.npy, *.json)해두고,
질의 시점에는 캐시만 불러와 코사인 유사도 계산만 한다.
"""
import json
import re
import pickle
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi


BUILD_EMBEDDINGS = False

BASE = Path(__file__).resolve().parent.parent
INDEX_DIR = Path(__file__).resolve().parent / "index"
INDEX_DIR.mkdir(exist_ok=True)

HANGUL_RUN_RE = re.compile(r"[가-힣]+")
ALNUM_RUN_RE = re.compile(r"[A-Za-z0-9]+")

# 실무에서 형태소 분석기(mecab/kiwi) 없이 한국어 어휘검색(BM25)을 돌릴 때 흔히 쓰는
# "문자 바이그램(CJK bigram)" 토큰화 방식 — Lucene의 CJKBigramFilter, Elasticsearch의
# 기본 CJK 처리와 같은 원리다. "지하차도에"(조사 결합)와 "지하차도"가 완전히 다른 단어
# 취급되는 문제(형태소 분석 없이는 어절 단위 토큰화가 조사 앞에서 못 끊음)를, 2글자씩
# 겹쳐 자르면 "지하차도"라는 부분열 자체가 토큰으로 남아 자연스럽게 해결된다.
# 숫자/영문(내선번호 등)은 바이그램으로 쪼개면 오히려 의미가 깨지므로 통짜 토큰으로 둔다.
def tokenize(text):
    tokens = []
    for run in HANGUL_RUN_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    tokens.extend(ALNUM_RUN_RE.findall(text))
    return tokens


# 구조/색인용 페이지(실제 답변 내용이 아니라 표지·자체 목차표) - 검색 대상에서 제외.
# 특정 질문과 무관하게 항상 상위권에 뜨는 "일반적으로 그럴듯해 보이는" 문서라 별도 처리 없이는
# 걸러지지 않는다(짧고 다양한 단어를 조금씩 담고 있어 임베딩 유사도가 늘 중간 이상으로 나옴).
INDEX_PAGE_TITLE_MARKERS = ("표지", "목차표", "목차")


def load_documents():
    """manual_cases + manual_sections + recurring_cases 를 하나의 검색 대상 문서 목록으로 통합."""
    cases = json.load(open(BASE / "data/manual/manual_cases.json", encoding="utf-8"))
    sections = json.load(open(BASE / "data/manual/manual_sections.json", encoding="utf-8"))
    recurring = json.load(open(BASE / "data/complaints/recurring_cases.json", encoding="utf-8"))
    action_path = BASE / "data/manual/manual_action_cases.json"
    action_data = json.load(open(action_path, encoding="utf-8")) if action_path.exists() else {"cases": []}
    actions_by_id = {
        item["id"]: item
        for item in action_data.get("cases", [])
        if item.get("id")
    }

    docs = []
    for c in cases:
        body = " ".join(p["text"] for p in c["content_by_page"])
        action_case = actions_by_id.get(c["id"], {})
        search_terms = action_case.get("searchTerms", [])
        action_text = " ".join([
            action_case.get("summary", ""),
            *action_case.get("intakeQuestions", []),
            *action_case.get("immediateActions", []),
        ])
        # BM25 색인용 텍스트(bm25_text)는 제목+키워드만 쓴다(본문 전체 X). 모든 케이스가
        # "본관 당직사령에게 상황보고", "관련 부서에 접수 사항 전파"처럼 거의 동일한 정형
        # 절차 문구를 공유하고 있어서, 본문 전체를 색인하면 이 보일러플레이트 때문에
        # 무관한 질문도 아무 케이스에나 어중간하게 매칭되는 잡음이 생김(calibrate.py 실측:
        # "무단횡단하는 사람이 너무 많아요"가 "가로수 전도" 케이스와 오매칭됨).
        # 제목/키워드는 이미 데이터 파이프라인에서 문서별 변별력 있는 단어만 추출해둔
        # 상태라 이 문제가 없다. 본문 원문(body)은 화면에 그대로 보여줄 표시용으로만 쓴다.
        docs.append({
            "doc_id": c["id"], "kind": "manual_case", "title": c["title"],
            "keywords": c.get("keywords", []),
            "bm25_text": (
                (c["title"] + " ") * 2
                + " ".join(c.get("keywords", []))
                + " "
                + (" ".join(search_terms) + " ") * 3
            ),
            "display_text": c["title"] + " " + action_text + " " + body,
            "evidence_level": "official_manual",
            "breadcrumb": c.get("breadcrumb", []),
        })
    for s in sections:
        if any(marker in s["section"] for marker in INDEX_PAGE_TITLE_MARKERS):
            continue  # 표지/자체 목차표 등은 실제 답변 내용이 아니라 검색 대상에서 제외
        docs.append({
            "doc_id": s["id"], "kind": "manual_section", "title": s["section"],
            "keywords": s.get("keywords", []),
            "bm25_text": (s["section"] + " ") * 2 + " ".join(s.get("keywords", [])),
            "display_text": s["section"] + " " + s["content"],
            "evidence_level": "official_manual",
            "breadcrumb": s.get("breadcrumb", []),
        })
    for i, r in enumerate(recurring):
        docs.append({
            "doc_id": f"recurring_{i:03d}", "kind": "recurring_case", "title": r["type"],
            "keywords": [],
            "bm25_text": (r["type"] + " ") * 2 + " ".join(r.get("main_departments", [])),
            "display_text": r["type"] + " " + " ".join(r.get("main_departments", [])),
            "evidence_level": "historical_case",
            "departments": r.get("main_departments", []),
            "candidate_count": r.get("candidate_count"),
        })
    return docs


def build():
    docs = load_documents()
    tokenized = [tokenize(d["bm25_text"]) for d in docs]
    bm25 = BM25Okapi(tokenized)

    if BUILD_EMBEDDINGS:
        from sentence_transformers import SentenceTransformer

        print("임베딩 모델 로딩 중...")
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        # 임베딩은 BM25와 반대로 문맥이 많을수록 의미 파악에 유리해서 본문(display_text)을 쓴다.
        # 너무 길면 특정 단어 하나에 벡터가 묻히니 앞부분 400자로 제한.
        embed_texts = [
            d["title"] + ". " + d["display_text"][:400]
            for d in docs
        ]
        print(f"{len(embed_texts)}개 문서 임베딩 계산 중...")
        embeddings = model.encode(
            embed_texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
    else:
        # v1은 의미 검색 티어를 사용하지 않으므로 대형 모델 다운로드를 생략한다.
        embeddings = np.empty((len(docs), 0), dtype=np.float32)

    with open(INDEX_DIR / "docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    with open(INDEX_DIR / "bm25.pkl", "wb") as f:
        pickle.dump({"bm25": bm25, "tokenized": tokenized}, f)
    np.save(INDEX_DIR / "embeddings.npy", embeddings)

    print(f"인덱스 저장 완료: {INDEX_DIR}")
    print(f"  - 문서 수: {len(docs)} (manual_case {sum(1 for d in docs if d['kind']=='manual_case')}, "
          f"manual_section {sum(1 for d in docs if d['kind']=='manual_section')}, "
          f"recurring_case {sum(1 for d in docs if d['kind']=='recurring_case')})")


if __name__ == "__main__":
    build()
