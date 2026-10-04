from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.routers.auth import (
    get_current_user,
    require_admin,
)

from backend.schemas.guides import (
    AdminGuideInput,
    QuickGuide,
    QuickGuideListResponse,
)

from backend.services.guide_service import (
    guide_service,
)


# ---------------------------------------------------------
# /api/guides
# /api/admin/guides
# 관련 API
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api",
    tags=["guides"],
)


# ---------------------------------------------------------
# GuideService의 데이터를
# 프론트에 전달할 형식으로 변환
# ---------------------------------------------------------

def _guide_list_response() -> QuickGuideListResponse:

    guides = (
        guide_service
        .list_guides()
    )

    return QuickGuideListResponse(

        source=(
            guide_service
            .source
        ),

        guides=[
            QuickGuide(
                **guide
            )

            for guide
            in guides
        ],
    )


# ---------------------------------------------------------
# 일반 사용자용 업무 안내 조회
#
# 프론트:
# GET /api/guides
# ---------------------------------------------------------

@router.get(
    "/guides",
    response_model=QuickGuideListResponse,
)
def get_guides(
    _: dict[str, Any] = Depends(
        get_current_user
    ),
) -> QuickGuideListResponse:
    """
    일반 로그인 사용자가
    업무 안내 내용을 조회합니다.

    관리자가 수정한 내용이 있다면
    수정된 내용이 반환됩니다.
    """

    return (
        _guide_list_response()
    )


# ---------------------------------------------------------
# 관리자용 업무 안내 조회
#
# 프론트:
# GET /api/admin/guides
# ---------------------------------------------------------

@router.get(
    "/admin/guides",
    response_model=QuickGuideListResponse,
)
def get_admin_guides(
    _: dict[str, Any] = Depends(
        require_admin
    ),
) -> QuickGuideListResponse:
    """
    관리자 페이지에서
    수정할 업무 안내 목록을 불러옵니다.
    """

    return (
        _guide_list_response()
    )


# ---------------------------------------------------------
# 관리자 업무 안내 수정
#
# 프론트:
# PUT /api/admin/guides/{guide_id}
#
# 여기서:
# - 제목 수정
# - 설명 수정
# - 처리 단계 추가
# - 처리 단계 수정
# - 처리 단계 삭제
# - 주의사항 수정
#
# 모두 처리합니다.
# ---------------------------------------------------------

@router.put(
    "/admin/guides/{guide_id}",
    response_model=QuickGuide,
)
def update_admin_guide(
    guide_id: str,

    request: AdminGuideInput,

    user: dict[str, Any] = Depends(
        require_admin
    ),
) -> QuickGuide:
    """
    관리자 페이지에서 변경한 업무 안내를
    SQLite DB에 저장합니다.
    """

    try:

        saved_guide = (
            guide_service
            .save_guide(

                guide_id=guide_id,

                payload=(
                    request
                    .model_dump(
                        exclude_none=True
                    )
                ),

                user_id=int(
                    user[
                        "id"
                    ]
                ),
            )
        )

    except KeyError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),

            detail=(
                "해당 업무 안내를 찾을 수 없습니다."
            ),

        ) from exc

    return QuickGuide(
        **saved_guide
    )


# ---------------------------------------------------------
# 원본으로 되돌리기
#
# 프론트의:
# "원본으로 되돌리기"
# 버튼과 연결
#
# DELETE /api/admin/guides/{guide_id}
# ---------------------------------------------------------

@router.delete(
    "/admin/guides/{guide_id}",
)
def reset_admin_guide(
    guide_id: str,

    _: dict[str, Any] = Depends(
        require_admin
    ),
) -> dict[str, bool]:
    """
    관리자가 수정했던 내용을 삭제하고
    데이터팀의 기존 매뉴얼 내용으로 되돌립니다.
    """

    try:

        guide_service.reset_guide(
            guide_id
        )

    except KeyError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),

            detail=(
                "해당 업무 안내를 찾을 수 없습니다."
            ),

        ) from exc

    return {
        "ok": True
    }