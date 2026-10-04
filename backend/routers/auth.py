from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from backend.schemas.auth import (
    AuthStatusResponse,
    AuthUser,
    LoginRequest,
    SetupAdminRequest,
)

from backend.services.auth_service import (
    SESSION_MAX_AGE_SECONDS,
    auth_service,
)


# ---------------------------------------------------------
# /api/auth 로 시작하는 로그인 관련 API
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


# 브라우저에 저장될 로그인 쿠키 이름
SESSION_COOKIE_NAME = (
    "living_lab_session"
)
LEGACY_SESSION_COOKIE_NAME = "dutory_session"


# ---------------------------------------------------------
# 로그인 성공 시 쿠키 저장
# ---------------------------------------------------------

def _set_session_cookie(
    response: Response,
    token: str,
) -> None:
    """
    로그인 성공 후 생성된 세션 토큰을
    브라우저 쿠키에 저장합니다.
    """

    response.delete_cookie(
        key=LEGACY_SESSION_COOKIE_NAME,
        path="/",
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,

        # auth_service.py와 동일하게
        # 12시간 동안 로그인 유지
        max_age=(
            SESSION_MAX_AGE_SECONDS
        ),

        # JavaScript에서 세션 쿠키를
        # 직접 읽지 못하게 보호
        httponly=True,

        # 로컬 개발 환경에서
        # 프론트/백엔드 요청에 사용
        samesite="lax",

        # 지금은 localhost 개발 환경이므로 False
        # 실제 HTTPS 배포 시에는 True로 변경
        secure=False,

        path="/",
    )


# ---------------------------------------------------------
# 현재 로그인 사용자 확인
# ---------------------------------------------------------

def get_current_user(
    request: Request,
) -> dict[str, Any]:
    """
    브라우저 쿠키를 확인해서
    현재 로그인한 사용자를 반환합니다.

    로그인하지 않았다면 401 오류 반환.
    """

    token = request.cookies.get(
        SESSION_COOKIE_NAME
    ) or request.cookies.get(
        LEGACY_SESSION_COOKIE_NAME
    )

    user = (
        auth_service
        .current_user(
            token
        )
    )

    if user is None:

        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "로그인이 필요합니다."
            ),
        )

    return user


# ---------------------------------------------------------
# 관리자 권한 확인
# ---------------------------------------------------------

def require_admin(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    현재 로그인 사용자가
    관리자인지 확인합니다.
    """

    if (
        user.get(
            "role"
        )
        != "admin"
    ):

        raise HTTPException(
            status_code=(
                status
                .HTTP_403_FORBIDDEN
            ),
            detail=(
                "관리자 권한이 필요합니다."
            ),
        )

    return user


# ---------------------------------------------------------
# 관리자 최초 설정 여부
#
# 프론트가 앱 시작 시 가장 먼저 호출
# ---------------------------------------------------------

@router.get(
    "/status",
    response_model=AuthStatusResponse,
)
def auth_status() -> AuthStatusResponse:

    return AuthStatusResponse(
        needsSetup=(
            auth_service
            .needs_setup()
        )
    )


# ---------------------------------------------------------
# 최초 관리자 계정 생성
# ---------------------------------------------------------

@router.post(
    "/setup",
    response_model=AuthUser,
)
def setup_admin(
    request: SetupAdminRequest,
    response: Response,
) -> AuthUser:
    """
    DB에 계정이 하나도 없을 때
    최초 관리자 계정을 생성합니다.

    계정 생성 성공 후 바로 로그인 처리합니다.
    """

    try:

        (
            user,
            token,
        ) = (
            auth_service
            .setup_admin(
                display_name=(
                    request
                    .displayName
                ),

                username=(
                    request
                    .username
                ),

                password=(
                    request
                    .password
                ),
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_409_CONFLICT
            ),
            detail=str(
                exc
            ),
        ) from exc

    # 관리자 생성 성공
    # → 로그인 쿠키도 바로 저장
    _set_session_cookie(
        response,
        token,
    )

    return AuthUser(
        **user
    )


# ---------------------------------------------------------
# 로그인
# ---------------------------------------------------------

@router.post(
    "/login",
    response_model=AuthUser,
)
def login(
    request: LoginRequest,
    response: Response,
) -> AuthUser:
    """
    아이디와 비밀번호를 확인한 뒤
    로그인 세션을 생성합니다.
    """

    result = (
        auth_service
        .login(
            username=(
                request
                .username
            ),

            password=(
                request
                .password
            ),
        )
    )

    # 아이디 또는 비밀번호가 틀림
    if result is None:

        raise HTTPException(
            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "아이디 또는 비밀번호가 올바르지 않습니다."
            ),
        )

    (
        user,
        token,
    ) = result

    # 로그인 성공
    # → 세션 쿠키 저장
    _set_session_cookie(
        response,
        token,
    )

    return AuthUser(
        **user
    )


# ---------------------------------------------------------
# 현재 로그인한 사용자 정보
# ---------------------------------------------------------

@router.get(
    "/me",
    response_model=AuthUser,
)
def me(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> AuthUser:
    """
    현재 로그인 상태인지 확인하고
    로그인 사용자 정보를 반환합니다.
    """

    return AuthUser(
        **user
    )


# ---------------------------------------------------------
# 로그아웃
# ---------------------------------------------------------

@router.post(
    "/logout",
    status_code=204,
)
def logout(
    request: Request,
    response: Response,
) -> None:
    """
    DB의 로그인 세션을 삭제하고
    브라우저 쿠키도 삭제합니다.
    """

    token = request.cookies.get(
        SESSION_COOKIE_NAME
    ) or request.cookies.get(
        LEGACY_SESSION_COOKIE_NAME
    )

    auth_service.logout(
        token
    )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )

    response.delete_cookie(
        key=LEGACY_SESSION_COOKIE_NAME,
        path="/",
    )

    return None
