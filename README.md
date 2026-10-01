# 듀토리(Dutory)

유성구청 야간·휴일 당직자가 민원 내용과 근무 매뉴얼을 빠르게 확인할 수 있는 업무 지원 서비스입니다.

## 주요 기능

- 민원 내용을 검색하면 확인 사항, 처리 순서, 담당 부서와 연락처를 안내합니다.
- 공식 매뉴얼 근거와 과거 민원 처리 사례를 구분해 보여줍니다.
- 근무 타임라인, 당직 기본업무, 근무일지 작성, 당직민원 등록 절차를 제공합니다.
- 85쪽 당직 매뉴얼에서 정리한 71개 문서와 공개 업무 연락처 47건을 사용합니다.
- 자주 쓰는 연락처 고정과 사용자 연락처 추가 기능을 제공합니다. 사용자 설정은 현재 브라우저에 저장됩니다.
- 전체 화면을 열지 않아도 사용할 수 있는 미니 응대 화면을 제공합니다.
- 로그인 후에만 업무 자료를 볼 수 있으며, 첫 실행 시 관리자 계정을 직접 생성합니다.
- 관리자는 업무 안내의 제목·설명·단계·주의사항과 공용 전화번호부를 수정할 수 있고 변경 내용은 모든 사용자에게 반영됩니다.

## 기술 구성

- 프론트엔드: React, TypeScript, Vite, Tailwind CSS
- 백엔드: FastAPI, Pydantic
- 검색: BM25 기반 문서 검색

## 처음 한 번만 준비하기 (Windows PowerShell)

필요한 프로그램은 Python 3.11 이상, Node.js 20 이상, pnpm입니다.

```powershell
git clone https://github.com/ssiyyeon/living-lab.git
cd living-lab

python -m venv .venv-api
.\.venv-api\Scripts\python.exe -m pip install --upgrade pip
.\.venv-api\Scripts\python.exe -m pip install -r .\backend\requirements.txt

cd .\frontend
pnpm install
Copy-Item .env.example .env.local
cd ..
```

`pnpm` 명령이 없다면 Node.js 설치 후 아래 명령으로 활성화할 수 있습니다.

```powershell
corepack enable
corepack prepare pnpm@latest --activate
```

## 프론트엔드와 백엔드 한 번에 실행하기

저장소 루트에서 다음 명령을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

이 스크립트는 검색 인덱스가 없으면 먼저 생성하고, 백엔드와 프론트엔드를 차례로 실행합니다.

- 화면: `http://localhost:5173`
- 백엔드: `http://localhost:8000`
- API 문서: `http://localhost:8000/docs`
- 실행 로그: `tmp/`

처음 접속하면 `관리자 계정 만들기` 화면이 표시됩니다. 관리자 이름, 아이디, 8자 이상의 비밀번호를 입력해 최초 관리자 계정을 만드세요. 이후에는 같은 아이디와 비밀번호로 로그인합니다. 초기 계정 정보는 코드나 Git에 저장되지 않습니다.

## 각각 실행하기

터미널 1에서 백엔드를 실행합니다. 검색 인덱스는 처음 한 번만 만들면 됩니다.

```powershell
.\.venv-api\Scripts\python.exe .\search\build_index.py
.\.venv-api\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

터미널 2에서 프론트엔드를 실행합니다.

```powershell
cd .\frontend
pnpm dev
```

프론트엔드는 `frontend/.env.local`에 적힌 백엔드 주소로 요청합니다.

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

주소를 바꿨다면 Vite 개발 서버를 다시 시작해야 합니다.

## 연결 확인

백엔드가 정상인지 PowerShell에서 확인합니다.

```powershell
Invoke-RestMethod http://localhost:8000/health
```

`status`가 `ok`, `search_ready`가 `True`이면 검색 API까지 준비된 상태입니다. 브라우저에서 `http://localhost:8000/docs`를 열면 API를 직접 시험할 수 있습니다.

주요 API는 다음과 같습니다.

- `GET /api/auth/status`: 최초 관리자 설정 여부
- `POST /api/auth/setup`: 최초 관리자 계정 생성
- `POST /api/auth/login`, `POST /api/auth/logout`: 로그인·로그아웃
- `POST /api/search`: 민원 검색과 대응 안내
- `GET /api/guides`: 반복 민원 상세 가이드
- `GET /api/manual`: 당직 근무 매뉴얼
- `GET /api/contacts`: 공개 업무 연락처
- `GET/POST/PUT/DELETE /api/admin/contacts`: 관리자 공용 연락처 관리
- `GET/PUT/DELETE /api/admin/guides`: 업무 안내 조회·수정·원본 복원

## 자주 생기는 문제

### 화면에 `Failed to fetch`가 표시되는 경우

1. `http://localhost:8000/health`가 열리는지 확인합니다.
2. `frontend/.env.local`의 `VITE_API_BASE_URL`이 실제 백엔드 주소와 같은지 확인합니다.
3. 백엔드와 프론트엔드를 모두 다시 실행합니다.
4. 포트 8000을 다른 프로그램이 사용 중이면 백엔드 포트와 `.env.local` 값을 함께 변경합니다.

### `search_ready`가 `False`인 경우

```powershell
.\.venv-api\Scripts\python.exe .\search\build_index.py
```

명령 실행 후 백엔드를 다시 시작합니다.

### Python 또는 프론트엔드 패키지가 없다고 나오는 경우

위의 “처음 한 번만 준비하기” 절차를 다시 실행합니다. 가상환경 이름은 `.venv-api`와 `.venv` 중 하나를 사용할 수 있으며, 자동 실행 스크립트는 두 이름을 모두 인식합니다.

## 변경 전 확인

```powershell
cd .\frontend
pnpm build
cd ..

.\.venv-api\Scripts\python.exe .\scripts\calibrate_search.py
```

## 팀 작업 흐름

`main`에 통합 내용이 반영된 뒤에는 다음과 같이 최신 코드를 실행합니다.

```powershell
git clone https://github.com/ssiyyeon/living-lab.git
cd living-lab
git pull origin main
```

아직 `integration` 브랜치에서 함께 확인하는 단계라면 다음처럼 전환합니다.

```powershell
git fetch origin
git switch integration
git pull origin integration
```

그 다음 이 README의 설치 및 실행 순서를 따르면 됩니다.

## 데이터와 보안

- 검색 인덱스(`search/index/`)는 Git에 올리지 않으며 로컬에서 생성합니다.
- 원본 민원 자료, 비공개 야간 연락망, 개인정보 파일은 Git에 올리지 않습니다.
- 현재 연락처 즐겨찾기와 사용자 추가 연락처는 브라우저 로컬 저장소에만 저장됩니다.
- 로컬 로그인 계정과 관리자 연락처는 `data/runtime/dutory.sqlite3`에 저장되며 Git에 올라가지 않습니다. 이 파일을 지우면 초기 관리자 설정부터 다시 진행합니다.
- 실제 배포 환경에서는 `DUTORY_COOKIE_SECURE=1`을 설정하고 HTTPS를 사용하며, SQLite 대신 운영용 데이터베이스와 기관 계정 체계를 연결해야 합니다.

데이터 구조는 [README_DATA.md](./README_DATA.md), 검색 구조와 평가 방법은 [README_SEARCH.md](./README_SEARCH.md)에서 더 자세히 확인할 수 있습니다.
