from fastapi import (
    FastAPI,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.database import (
    initialize_database,
)

from backend.routers.auth import (
    router as auth_router,
)

from backend.routers.contacts import (
    router as contacts_router,
)

from backend.routers.guides import (
    router as guides_router,
)

from backend.routers.manual import (
    router as manual_router,
)

from backend.routers.search import (
    router as search_router,
)

from backend.services.combined_search_service import (
    combined_search_service,
)

from backend.services.manual_service import (
    manual_service,
)


# ---------------------------------------------------------
# SQLite DB 초기화
# ---------------------------------------------------------

initialize_database()


# ---------------------------------------------------------
# FastAPI 앱 생성
# ---------------------------------------------------------

app = FastAPI(

    title=(
        "Living Lab Complaint Search API"
    ),

    description=(
        "당직 근무자를 위한 "
        "문서 기반 민원 검색 플랫폼 API"
    ),

    version="0.3.0",
)


# ---------------------------------------------------------
# CORS
#
# React:
# localhost:5173
#
# FastAPI:
# localhost:8000
#
# 쿠키 로그인 때문에
# allow_credentials=True 필요
# ---------------------------------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ---------------------------------------------------------
# 기본 API
# ---------------------------------------------------------

@app.get("/")
def root():

    return {

        "message": (
            "Living Lab Backend API"
        ),

        "version": (
            "0.3.0"
        ),
    }


# ---------------------------------------------------------
# 서버 상태 확인
# ---------------------------------------------------------

@app.get("/health")
def health():

    return {

        "status": "ok",

        # 기존 검색 + 관리자 검색
        "search_ready": (
            combined_search_service
            .is_ready
        ),

        "search_error": (
            combined_search_service
            .load_error
        ),

        # 전체 매뉴얼 데이터
        "manual_ready": (
            manual_service
            .is_ready
        ),

        "manual_error": (
            manual_service
            .load_error
        ),

        # SQLite 자체는 main import 시
        # 초기화되므로 정상 실행됐다면 사용 가능
        "database_ready": True,
    }


# ---------------------------------------------------------
# Router 등록
# ---------------------------------------------------------

# 로그인
app.include_router(
    auth_router
)


# 공용 전화번호부
app.include_router(
    contacts_router
)


# 업무 안내
app.include_router(
    guides_router
)


# 전체 매뉴얼
app.include_router(
    manual_router
)


# 민원 검색
app.include_router(
    search_router
)