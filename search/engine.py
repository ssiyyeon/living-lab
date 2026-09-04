"""BM25 기반 매뉴얼·반복 민원 검색 엔진.

공식 매뉴얼을 먼저 검색하고, 충분한 점수가 없을 때만 과거 민원 기반 참고사례를
검색한다. 어느 쪽도 임계치를 넘지 못하면 임의 답변 없이 ``no_match``를 반환한다.
"""

from __future__ import annotations

import json
import pickle
import re
from pathlib import Path


INDEX_DIR = Path(__file__).resolve().parent / "index"
HANGUL_RUN_RE = re.compile(r"[가-힣]+")
ALNUM_RUN_RE = re.compile(r"[A-Za-z0-9]+")

# search/calibrate.py의 표본 질문으로 검증한 값이다.
BM25_EXACT_THRESHOLD = 6.0
HISTORICAL_BM25_THRESHOLD = 5.0

# 기존 임베딩 방식은 무관한 질문의 오탐이 더 높게 측정되어 v1에서 사용하지 않는다.
ENABLE_EMBEDDING_TIER = False


def tokenize(text: str) -> list[str]:
    """한국어 조사가 붙어도 검색되도록 한글 문자열을 문자 바이그램으로 나눈다."""
    tokens: list[str] = []
    for run in HANGUL_RUN_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    tokens.extend(ALNUM_RUN_RE.findall(text))
    return tokens


class SearchEngine:
    def __init__(self) -> None:
        with open(INDEX_DIR / "docs.json", encoding="utf-8") as file:
            self.docs = json.load(file)
        with open(INDEX_DIR / "bm25.pkl", "rb") as file:
            self.bm25 = pickle.load(file)["bm25"]

        self.manual_idx = [
            i for i, doc in enumerate(self.docs)
            if doc["kind"] in ("manual_case", "manual_section")
        ]
        self.recurring_idx = [
            i for i, doc in enumerate(self.docs)
            if doc["kind"] == "recurring_case"
        ]

    def search(self, query: str, top_k: int = 3) -> dict:
        bm25_scores = self.bm25.get_scores(tokenize(query))

        manual_bm25 = sorted(
            ((bm25_scores[i], i) for i in self.manual_idx),
            key=lambda item: -item[0],
        )
        if manual_bm25 and manual_bm25[0][0] >= BM25_EXACT_THRESHOLD:
            manual_hits = [
                item for item in manual_bm25
                if item[0] >= BM25_EXACT_THRESHOLD
            ][:top_k]
            return self._format(manual_hits, "manual_exact", bm25_scores)

        recurring_bm25 = sorted(
            ((bm25_scores[i], i) for i in self.recurring_idx),
            key=lambda item: -item[0],
        )
        if recurring_bm25 and recurring_bm25[0][0] >= HISTORICAL_BM25_THRESHOLD:
            recurring_hits = [
                item for item in recurring_bm25
                if item[0] >= HISTORICAL_BM25_THRESHOLD
            ][:top_k]
            return self._format(recurring_hits, "historical_case", bm25_scores)

        return {
            "tier": "no_match",
            "message": "관련 매뉴얼이나 참고사례를 찾지 못했습니다. 담당부서에 직접 문의해 주세요.",
            "results": [],
        }

    def _format(self, scored: list[tuple[float, int]], tier: str, bm25_scores) -> dict:
        results = []
        for score, index in scored:
            doc = self.docs[index]
            results.append(
                {
                    "doc_id": doc["doc_id"],
                    "kind": doc["kind"],
                    "title": doc["title"],
                    "evidence_level": doc["evidence_level"],
                    "score": round(float(score), 3),
                    "bm25_score": round(float(bm25_scores[index]), 3),
                }
            )
        return {"tier": tier, "results": results}


if __name__ == "__main__":
    engine = SearchEngine()
    for question in (
        "지하차도에 물이 차서 차가 못 지나가요",
        "가스가 터진 것 같아요 냄새나요",
        "고양이가 로드킬 당했어요 사체 좀 치워주세요",
        "가로등이 고장나서 어두워요",
        "오늘 날씨가 좋네요",
    ):
        print(question, engine.search(question))
