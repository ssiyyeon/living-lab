# 검색 API

`feature/data`의 BM25 검색 엔진을 프론트엔드에서 호출할 수 있게 하는 로컬 JSON API입니다.

## 처음 한 번 준비

프로젝트 루트에서 가상환경을 만들고, API 실행에 필요한 작은 패키지를 설치한 뒤 검색 인덱스를 생성합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe search\build_index.py
```

최신 `feature/data`에 포함된 개인정보 마스킹 완료 데이터가 인덱스의 입력으로 사용됩니다.

- `data/manual/manual_cases.json`
- `data/manual/manual_sections.json`
- `data/complaints/recurring_cases.json`

생성되는 `search/index/`는 재생성 가능한 로컬 캐시라 Git에 올라가지 않습니다.

## 실행

```powershell
.\.venv\Scripts\python.exe backend\server.py
```

기본 주소는 `http://127.0.0.1:8000`입니다.

- `GET /api/health`: 데이터·인덱스·패키지 준비 상태 확인
- `POST /api/search`: `{"query":"도로에 포트홀이 생겼어요","topK":4}` 형식으로 검색
