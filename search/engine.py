"""
하이브리드 검색 엔진: BM25(어휘) 우선 → 임베딩(의미) 보조 → 반복민원(참고) → 담당부서 안내.

판정 근거 수준을 항상 결과에 표시한다(요구사항 문서 9번: 공식매뉴얼/과거민원 근거 수준 분리 원칙).
  - manual_exact       : BM25로 확실한 단어 일치 (가장 신뢰 높음)
  - manual_semantic     : 단어는 안 겹치지만 임베딩 의미 유사도로 찾음 (매뉴얼 원문이되, 자동매칭이라 표기)
  - historical_case    : 매뉴얼에 없어 과거 민원 통계로만 참고 제공 (공식 답변 아님, 항상 명시)
  - no_match           : 아무 것도 임계치를 못 넘음 → 담당부서 직접 문의 안내
"""
import json
import re
import pickle
from pathlib import Path

import numpy as np

INDEX_DIR = Path(__file__).resolve().parent / "index"
ACTION_CASES_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "manual"
    / "manual_action_cases.json"
)
HANGUL_RUN_RE = re.compile(r"[가-힣]+")
ALNUM_RUN_RE = re.compile(r"[A-Za-z0-9]+")

# 임계치는 search/calibrate.py로 12개 질문(정답 7 + 오답 5) 실측해서 정한 값.
# 표본이 작아 향후 실제 검색 로그가 쌓이면 재보정이 필요함(README_SEARCH.md 참고).
BM25_EXACT_THRESHOLD = 6.0
HISTORICAL_BM25_THRESHOLD = 5.0

# 임베딩(의미 유사도) 티어는 v1에서 비활성화한다.
# calibrate.py 실측 결과, 무관한 질문("오늘 날씨가 좋네요" 0.624, "공무원이 불친절해요" 0.654)의
# 유사도가 진짜 정답("시끄러운 소리" 질문 vs 소음 민원 케이스, 0.455)보다 더 높게 나오는
# 역전 현상이 나타났다 — 즉 지금 쓰는 범용 다국어 임베딩 모델 + 문서당 텍스트 양으로는
# 전역 임계치 하나로 참/거짓을 가를 수 없다(켜두면 오탐이 진짜 매칭보다 많아짐).
# 켜서 얻는 이득(구어체 재현율)보다 잃는 것(엉뚱한 오탐)이 커서, 근거가 불확실한 상태로
# 배포하지 않는다는 원칙에 따라 비활성화 상태로 둔다. 재활성화하려면 (a) 반복민원처럼
# 문서 텍스트를 더 길고 구체적으로 만들거나 (b) 한국어 특화 임베딩 모델로 교체 후
# 다시 calibrate.py로 검증이 필요하다.
ENABLE_EMBEDDING_TIER = False
EMBEDDING_THRESHOLD = 0.72


def tokenize(text):
    # build_index.py의 바이그램 토큰화와 반드시 동일해야 BM25 점수가 맞는다(인덱싱 시점과
    # 질의 시점의 토큰화 방식이 다르면 어휘검색 자체가 성립하지 않음).
    tokens = []
    for run in HANGUL_RUN_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    tokens.extend(ALNUM_RUN_RE.findall(text))
    return tokens


class SearchEngine:
    def __init__(self):
        self.docs = json.load(open(INDEX_DIR / "docs.json", encoding="utf-8"))
        with open(INDEX_DIR / "bm25.pkl", "rb") as f:
            cache = pickle.load(f)
        self.bm25 = cache["bm25"]
        self.embeddings = None
        self.model = None

        if ENABLE_EMBEDDING_TIER:
            from sentence_transformers import SentenceTransformer

            self.embeddings = np.load(INDEX_DIR / "embeddings.npy")
            self.model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2"
            )

        # 검색 결과는 당직자가 바로 행동할 수 있는 상황별 사례만 대상으로 한다.
        # 일반 문서 조각(manual_section)은 근거 데이터로 남기되 답변 후보에서는 제외한다.
        self.manual_idx = [i for i, d in enumerate(self.docs) if d["kind"] == "manual_case"]
        self.recurring_idx = [i for i, d in enumerate(self.docs) if d["kind"] == "recurring_case"]
        self.doc_index_by_id = {
            document["doc_id"]: index
            for index, document in enumerate(self.docs)
        }
        self.action_aliases = self._load_action_aliases()

    @staticmethod
    def _normalize_phrase(text):
        return re.sub(
            r"[^가-힣A-Za-z0-9]+",
            "",
            str(text),
        ).lower()

    def _load_action_aliases(self):
        if not ACTION_CASES_PATH.exists():
            return []

        with ACTION_CASES_PATH.open(encoding="utf-8") as file:
            action_data = json.load(file)

        aliases = []
        for case in action_data.get("cases", []):
            doc_id = case.get("id")
            doc_index = self.doc_index_by_id.get(doc_id)
            if doc_index is None:
                continue

            terms = [case.get("title", ""), *case.get("searchTerms", [])]
            for term in terms:
                normalized = self._normalize_phrase(term)
                if len(normalized) >= 2:
                    aliases.append((normalized, doc_index))

        return aliases

    def _action_alias_match(self, query):
        normalized_query = self._normalize_phrase(query)
        if len(normalized_query) < 2:
            return None

        matches = []
        for alias, doc_index in self.action_aliases:
            if alias == normalized_query:
                score = 200 + len(alias)
            elif alias in normalized_query:
                score = 150 + len(alias)
            elif normalized_query in alias:
                score = 100 + len(normalized_query)
            else:
                continue

            matches.append((score, doc_index))

        if not matches:
            return None

        return max(matches, key=lambda item: item[0])

    def _bm25_scores(self, query):
        return np.array(self.bm25.get_scores(tokenize(query)))

    def _embedding_scores(self, query):
        if self.model is None or self.embeddings is None:
            return np.zeros(len(self.docs))

        qvec = self.model.encode([query], normalize_embeddings=True)[0]
        return self.embeddings @ qvec

    def search(self, query, top_k=3):
        bm25_scores = self._bm25_scores(query)
        emb_scores = self._embedding_scores(query)

        # 시민이 실제로 쓰는 표현(예: "야간소음", "밤에 시끄러워요")을
        # 행동 매뉴얼 사례의 명시적 별칭에 우선 연결한다. 범용 의미 검색보다
        # 오탐 가능성이 낮고, 결과에 즉시 조치·조건별 대응을 붙일 수 있다.
        alias_match = self._action_alias_match(query)
        if alias_match:
            alias_score, doc_index = alias_match
            bm25_scores[doc_index] = alias_score
            return self._format(
                [(alias_score, doc_index)],
                "manual_exact",
                bm25_scores,
                emb_scores,
            )

        # 1) 매뉴얼(케이스+일반문서) 중 BM25 확실한 일치
        manual_bm25 = [(bm25_scores[i], i) for i in self.manual_idx]
        manual_bm25.sort(key=lambda x: -x[0])
        if manual_bm25 and manual_bm25[0][0] >= BM25_EXACT_THRESHOLD:
            return self._format(manual_bm25[:top_k], "manual_exact", bm25_scores, emb_scores)

        # 2) 매뉴얼 중 임베딩 의미 유사도 (v1: 비활성화, 위 ENABLE_EMBEDDING_TIER 주석 참고)
        if ENABLE_EMBEDDING_TIER:
            manual_emb = [(emb_scores[i], i) for i in self.manual_idx]
            manual_emb.sort(key=lambda x: -x[0])
            if manual_emb and manual_emb[0][0] >= EMBEDDING_THRESHOLD:
                return self._format(manual_emb[:top_k], "manual_semantic", bm25_scores, emb_scores)

        # 3) 반복 민원(참고용, 공식 아님) - BM25만 사용한다.
        #    반복민원 문서는 "유형명 + 부서명" 정도로 텍스트가 짧아(예: "유기동물 보호중 신고
        #    지역산업과") 임베딩이 모든 질문에 비슷하게 중간 이상 유사도를 주는 문제가
        #    calibrate.py 실측에서 확인됨(예: "오늘 날씨가 좋네요"에도 0.786 유사도로 매칭).
        #    실제 민원 예문이 각 유형에 연결되면 임베딩도 다시 켤 수 있음(TODO.md 참고).
        rec_bm25 = [(bm25_scores[i], i) for i in self.recurring_idx]
        rec_bm25.sort(key=lambda x: -x[0])
        if rec_bm25 and rec_bm25[0][0] >= HISTORICAL_BM25_THRESHOLD:
            return self._format(rec_bm25[:top_k], "historical_case", bm25_scores, emb_scores)

        # 4) 폴백
        return {"tier": "no_match", "message": "관련 매뉴얼/참고사례를 찾지 못했습니다. 담당부서에 직접 문의해주세요.", "results": []}

    def _format(self, scored, tier, bm25_scores, emb_scores):
        results = []
        for score, i in scored:
            d = self.docs[i]
            results.append({
                "doc_id": d["doc_id"], "kind": d["kind"], "title": d["title"],
                "evidence_level": d["evidence_level"],
                "score": round(float(score), 3),
                "bm25_score": round(float(bm25_scores[i]), 3),
                "embedding_score": round(float(emb_scores[i]), 3),
            })
        return {"tier": tier, "results": results}


if __name__ == "__main__":
    engine = SearchEngine()
    for q in ["지하차도에 물이 차서 차가 못 지나가요", "가스가 터진 것 같아요 냄새나요",
              "고양이가 로드킬 당했어요 사체 좀 치워주세요", "밤에 노래방에서 시끄러운 소리가 계속 나요",
              "무단횡단하는 사람이 너무 많아요"]:
        r = engine.search(q)
        print(f"\n질문: {q}")
        print(f"  tier: {r['tier']}")
        for res in r.get("results", []):
            print(f"    - {res['title']} (bm25={res['bm25_score']}, emb={res['embedding_score']})")
        if r["tier"] == "no_match":
            print(f"  → {r['message']}")
