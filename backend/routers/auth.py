from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from backend.schemas.auth import AuthStatusResponse, LoginRequest, SetupRequest, UserResponse
from backend.services import auth_service


SESSION_COOKIE = "dutory_session"
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = auth_service.create_session(user_id)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=auth_service.SESSION_HOURS * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=os.getenv("DUTORY_COOKIE_SECURE", "0") == "1",
        path="/",
    )


def require_user(dutory_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = auth_service.user_for_session(dutory_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    return user


def require_admin(user: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return user


@router.get("/status", response_model=AuthStatusResponse)
def auth_status() -> AuthStatusResponse:
    return AuthStatusResponse(needsSetup=auth_service.needs_setup())


@router.post("/setup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def setup_admin(request: SetupRequest, response: Response) -> UserResponse:
    user = auth_service.create_initial_admin(request.username, request.displayName, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="초기 관리자 설정이 이미 완료되었습니다.")
    _set_session_cookie(response, int(user["id"]))
    return UserResponse(**user)


@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, response: Response) -> UserResponse:
    user = auth_service.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호를 확인해 주세요.")
    _set_session_cookie(response, int(user["id"]))
    return UserResponse(**user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, dutory_session: str | None = Cookie(default=None)) -> Response:
    auth_service.delete_session(dutory_session)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/me", response_model=UserResponse)
def current_user(user: dict[str, Any] = Depends(require_user)) -> UserResponse:
    return UserResponse(**user)
