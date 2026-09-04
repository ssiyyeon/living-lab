# 듀토리 — 당직 매뉴얼 검색 웹사이트

유성구청 당직 근무자가 민원 내용을 검색하면 공식 매뉴얼 또는 과거 민원 참고자료를 근거와 함께 보여주는 프로젝트입니다.

## 실행

처음 한 번 API 환경과 검색 인덱스를 준비합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe search\build_index.py
```

그다음 두 터미널에서 API와 프론트엔드를 각각 실행합니다.

```powershell
# 터미널 1 — 프로젝트 루트
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 터미널 2 — frontend 폴더
pnpm install
pnpm dev
```

브라우저에서 `http://127.0.0.1:5173`을 엽니다. 개발 중 `/api` 요청은 Vite가 `http://127.0.0.1:8000`으로 전달합니다.

## 문서

- 데이터 정리·마스킹: `README_DATA.md`
- 검색 로직과 검증 결과: `README_SEARCH.md`
- API 실행: `backend/README.md`
- 프론트엔드: `frontend/README.md`
