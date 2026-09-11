# 듀토리 프론트엔드

React, TypeScript, Vite, Tailwind CSS로 만든 유성구청 당직 근무 지원 화면입니다. 검색, 반복 민원 가이드, 당직 매뉴얼, 공개 연락처를 FastAPI 백엔드에서 불러옵니다.

전체 프로젝트의 최초 설치 방법과 백엔드 실행 순서는 저장소 루트의 [README.md](../README.md)를 먼저 확인하세요.

## 프론트엔드만 실행

```powershell
pnpm install
Copy-Item .env.example .env.local
pnpm dev
```

기본 백엔드 주소는 다음과 같습니다.

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

프로덕션 빌드는 `pnpm build`로 확인합니다.
