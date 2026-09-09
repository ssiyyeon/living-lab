# Yuseong-livinglab-dutory
유성구청 리빙랩 - 듀토리팀

## 로컬 개발 실행

프론트엔드와 백엔드를 한 번에 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

실행 후 `http://localhost:5173`을 열어 사용합니다. 검색 요청은 `frontend/.env.local`의 `VITE_API_BASE_URL` 주소로 연결됩니다.
