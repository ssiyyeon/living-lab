from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.database import initialize_database
from backend.routers.admin import router as admin_router
from backend.routers.auth import router as auth_router

from backend.routers.search import (
    router as search_router,
)

from backend.services.search_service import (
    search_service,
)


app = FastAPI(
    title="Living Lab Complaint Search API",
    description=(
        "당직 근무자를 위한 "
        "문서 기반 민원 검색 플랫폼 API"
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return {
        "message": "Living Lab Backend API",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "search_ready": search_service.is_ready,
        "search_error": (
            None
            if search_service.is_ready
            else search_service.load_error
        ),
    }


app.include_router(search_router)
app.include_router(auth_router)
app.include_router(admin_router)
