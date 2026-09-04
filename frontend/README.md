# 듀토리 프론트엔드

유성구청 당직 근무자를 위한 문서 기반 민원 검색 화면입니다. Figma Make에서 내보낸 React 코드를 기준으로, 실제 화면에서 사용하지 않는 UI 컴포넌트와 에셋 및 의존성을 제거했습니다.

## 실행

```bash
pnpm install
pnpm dev
```

프로덕션 빌드는 `pnpm build`로 확인할 수 있습니다.

검색하려면 프로젝트 루트에서 검색 인덱스를 한 번 만들고 Python API도 함께 실행해야 합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe search\build_index.py
.\.venv\Scripts\python.exe backend\server.py
```

## 현재 상태

- React + Vite + Tailwind CSS 기반 화면
- 검색창과 결과 목록은 `/api/search`를 통해 최신 `feature/data`의 BM25 검색 엔진과 연결
- 개발 서버는 `/api` 요청을 `http://127.0.0.1:8000`으로 전달
- 우측 보조 패널과 초기 공지·바로가기 영역은 아직 UI 확인용 샘플 데이터 사용

개인정보가 포함될 수 있는 매뉴얼 JSON이나 민원 원본은 프론트엔드에 포함하지 않습니다.
