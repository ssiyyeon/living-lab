"""
Phase 3(검색/유사도 매칭 엔진) + Phase 4(근거 판정 및 응답 규칙)

요구사항 명세서의 핵심 원칙을 그대로 구현한다:
  - 매뉴얼 = 공식 근거, 1순위
  - 반복 민원 유형(참고사례) = 보조 자료, 2순위 — 공식 대응으로 단정하지 않음
  - 근거가 불충분하거나 없으면 임의로 답변을 생성하지 않고 정보 부족을 안내

검색 방법은 TF-IDF(char+word) 코사인 유사도. 지도학습 분류가 아니라 정보검색(IR)
문제로 접근한다 — 라벨을 맞히는 게 아니라 "이 쿼리와 이 문서가 얼마나 비슷한가"만 본다.
"""

import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from manual.rule_lookup import load_situations, KEYWORDS, match_manual  # noqa: E402
from manual.general_lookup import load_general_docs, match_general, KEYWORDS as KEYWORDS_GENERAL  # noqa: E402
from search.reference_cases import load_reference_cases  # noqa: E402

# 근거 판정 임계치 (search/evaluate_engine.py로 전체 데이터에 대해 검증한 값)
# 매뉴얼 tier는 키워드 매칭(manual/rule_lookup.match_manual)으로만 확정하고,
# 유사도는 참고사례/근거불충분 판정에만 쓴다 — 아래 REFERENCE_THRESHOLD 설명 참고.
REFERENCE_THRESHOLD = 0.10  # 참고사례로 인정할 최소 유사도
MIN_RELEVANCE = 0.03        # 이보다 낮으면 "관련 문서 자체가 없음"으로 판단

NO_RESULT_MESSAGE = (
    "관련 문서에서 해당 민원에 대한 명확한 내용을 찾지 못했습니다. "
    "검색어를 변경하거나 관련 담당 부서에 확인해 주세요."
)
INSUFFICIENT_EVIDENCE_MESSAGE = (
    "검색된 문서만으로는 대응 방법을 명확하게 안내하기 어렵습니다. "
    "아래 관련 문서를 확인하거나 담당 부서에 문의해 주세요."
)


def _build_manual_docs() -> list[dict]:
    situations = load_situations()
    kw_by_key = {}
    for (dept, situation), kws in KEYWORDS.items():
        kw_by_key.setdefault((dept, situation), []).extend(kws)

    docs = []
    for (dept, situation), s in situations.items():
        keywords = kw_by_key.get((dept, situation), [])
        # 처리방법/참고사항 본문이 길어서 그대로 이어붙이면 핵심 키워드가 희석된다.
        # 검색 신호가 되는 제목·키워드는 3번 반복해 가중치를 준다 (title-boost).
        boosted = " ".join([situation, dept] + keywords) + " "
        text = boosted * 6 + " ".join(s.get("처리방법", [])) + " " + " ".join(s.get("참고사항", []))
        docs.append({
            "tier": "매뉴얼",
            "text": text,
            "부서": dept,
            "민원유형": situation,
            "관련문단": "\n".join(s.get("처리방법", [])),
            "참고사항": "\n".join(s.get("참고사항", [])),
            "담당자": "\n".join(s.get("담당자", [])) or None,
            "문서명": "당직 근무요령 및 상황별 매뉴얼",
            "페이지": s.get("페이지"),
        })
    return docs


def _build_general_docs() -> list[dict]:
    """민원 대응 케이스가 아닌 나머지 매뉴얼 내용(당직근무자 준수사항, 청사 시건,
    비상연락망, 소화기 비치 등). manual/parse_general_sections.py 참고."""
    docs_by_title = load_general_docs()
    docs = []
    for title, d in docs_by_title.items():
        keywords = KEYWORDS_GENERAL.get(title, [])
        boosted = " ".join([title] + keywords) + " "
        text = boosted * 6 + " ".join(d.get("내용", []))
        docs.append({
            "tier": "일반매뉴얼",
            "text": text,
            "부서": None,
            "민원유형": title,
            "관련문단": "\n".join(d.get("내용", [])),
            "참고사항": "당직 근무자 본인이 참고하는 내부 근무수칙입니다 (민원 대응 절차 아님).",
            "담당자": None,
            "문서명": "당직 근무요령 및 상황별 매뉴얼",
            "페이지": d.get("페이지범위"),
        })
    return docs


def _build_reference_docs() -> list[dict]:
    cases = load_reference_cases()
    docs = []
    for c in cases:
        text = " ".join([c["유형명"], c["주요부서"], " ".join(c["대표키워드"])])
        docs.append({
            "tier": "참고사례",
            "text": text,
            "부서": c["주요부서"],
            "민원유형": c["유형명"],
            "관련문단": f"과거 유사 민원 {c['건수']}건, 주로 '{c['주요조치유형']}'로 처리됨 (공식 매뉴얼 대응 아님, 참고용)",
            "참고사항": "매뉴얼에 등재되지 않은 상황입니다. 담당 부서 확인 후 처리하세요.",
            "담당자": None,
            "문서명": "반복 민원 유형 (과거 민원 이력 기반 참고자료)",
            "페이지": None,
        })
    return docs


class SearchEngine:
    def __init__(self):
        self.manual_docs = _build_manual_docs()
        self.reference_docs = _build_reference_docs()
        # 일반매뉴얼(당직근무자 준수사항 등)은 민원 대응 케이스가 아니라서 TF-IDF
        # 유사도 검색 대상(doc_matrix)에는 안 넣고, 키워드 정확매칭으로만 찾는다.
        self.general_docs = _build_general_docs()
        self.general_by_title = {d["민원유형"]: d for d in self.general_docs}
        all_docs = self.manual_docs + self.reference_docs

        char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
        word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, token_pattern=r"(?u)\b\w+\b")
        self.union = FeatureUnion([("char", char_vec), ("word", word_vec)])
        self.doc_matrix = self.union.fit_transform([d["text"] for d in all_docs])
        self.n_manual = len(self.manual_docs)
        self.manual_by_key = {(d["부서"], d["민원유형"]): d for d in self.manual_docs}

    def _scores(self, query: str) -> np.ndarray:
        q = self.union.transform([query])
        return cosine_similarity(q, self.doc_matrix)[0]

    def search(self, query: str, top_k: int = 3) -> dict:
        # 키워드가 정확히 일치하면(manual/rule_lookup.match_manual) 유사도 점수와
        # 무관하게 무조건 매뉴얼 확정 응답으로 취급한다. 전체 데이터로 검증해보니
        # 순수 유사도 임계치만 쓰면 키워드가 명백히 일치하는 건도 문서 본문 길이
        # 때문에 임계치를 못 넘겨 "근거불충분"으로 격하되는 회귀가 294건(13%) 있었다.
        # 키워드 일치는 유사도보다 신뢰도가 높은 신호이므로 먼저 확정한다.
        rule_hits = match_manual(query)
        if rule_hits:
            seen = set()
            results = []
            for hit in rule_hits:
                key = (hit["부서"], hit["민원요지"])
                if key in seen or key not in self.manual_by_key:
                    continue
                seen.add(key)
                results.append({**self.manual_by_key[key], "유사도": None})
                if len(results) >= top_k:
                    break
            return {"근거수준": "매뉴얼", "안내": None, "결과": results}

        # 민원 대응 케이스는 아니지만(당직근무자 준수사항, 청사 시건, 소화기 비치 등)
        # 당직자 본인이 근무 중 참고할 수 있는 나머지 매뉴얼 내용. 이것도 키워드
        # 정확매칭으로만 확정한다(위 매뉴얼 tier와 같은 원칙).
        general_hits = match_general(query)
        if general_hits:
            seen = set()
            results = []
            for hit in general_hits:
                title = hit["제목"]
                if title in seen or title not in self.general_by_title:
                    continue
                seen.add(title)
                results.append({**self.general_by_title[title], "유사도": None})
                if len(results) >= top_k:
                    break
            return {"근거수준": "일반매뉴얼", "안내": None, "결과": results}

        # 주의: 매뉴얼 tier는 위의 키워드 매칭에서만 확정한다. TF-IDF 유사도만으로
        # 매뉴얼 확정 응답을 준 버전을 전체 데이터로 검증했더니, 키워드가 없는데
        # 유사도만으로 "매뉴얼"이라고 한 725건의 실제 부서 일치율이 48.7%에 불과했다
        # (키워드 매칭 건은 89.0%). 절반 가까이 틀리는 걸 "공식 매뉴얼 근거"라고
        # 내보내는 건 명세서의 "근거 불충분 시 임의 답변 금지" 원칙 위반이라 판단해
        # 이 경로는 제거했다 — 유사도만 있는 경우는 최대 "참고사례"까지만 인정한다.
        scores = self._scores(query)
        reference_scores = scores[self.n_manual:]

        ref_order = np.argsort(reference_scores)[::-1]
        if reference_scores[ref_order[0]] >= REFERENCE_THRESHOLD:
            hits = [i for i in ref_order[:top_k] if reference_scores[i] >= REFERENCE_THRESHOLD]
            return {
                "근거수준": "참고사례",
                "안내": None,
                "결과": [{**self.reference_docs[i], "유사도": round(float(reference_scores[i]), 3)} for i in hits],
            }

        overall_max = float(scores.max()) if len(scores) else 0.0
        if overall_max < MIN_RELEVANCE:
            return {"근거수준": "결과없음", "안내": NO_RESULT_MESSAGE, "결과": []}

        # 관련성이 아주 없지는 않지만 확정 임계치엔 못 미침 -> 근거 불충분, 그래도 후보는 보여준다
        order = np.argsort(scores)[::-1][:top_k]
        all_docs = self.manual_docs + self.reference_docs
        return {
            "근거수준": "근거불충분",
            "안내": INSUFFICIENT_EVIDENCE_MESSAGE,
            "결과": [{**all_docs[i], "유사도": round(float(scores[i]), 3)} for i in order if scores[i] >= MIN_RELEVANCE],
        }


if __name__ == "__main__":
    engine = SearchEngine()
    demo = [
        "도로에 포트홀이 생겨서 위험합니다",
        "유기견을 발견했어요",
        "가로등이 안 들어와요",
        "노점상 단속해주세요",
        "회의실 예약은 어떻게 하나요",
    ]
    for q in demo:
        r = engine.search(q)
        print(f"\n민원: {q}")
        print(f"  근거수준: {r['근거수준']}" + (f" | {r['안내']}" if r["안내"] else ""))
        for hit in r["결과"]:
            score = "키워드 정확매칭" if hit["유사도"] is None else f"유사도 {hit['유사도']}"
            print(f"  - [{hit['tier']}] {hit['민원유형']} (부서: {hit['부서']}, {score})")
