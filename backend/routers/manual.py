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

from backend.schemas.manual import (
    AdminManualInput,
    ManualAdminDeleteResponse,
    ManualCatalogEntry,
    ManualCatalogResponse,
)

from backend.services.manual_service import (
    manual_service,
)


router = APIRouter(
    prefix="/api",
    tags=["manual"],
)


def _catalog_response(
) -> ManualCatalogResponse:
    data = (
        manual_service
        .response_data()
    )

    return ManualCatalogResponse(
        **data
    )


# ---------------------------------------------------------
# 일반 사용자 전체 매뉴얼 조회
# ---------------------------------------------------------

@router.get(
    "/manual",
    response_model=ManualCatalogResponse,
)
def get_manual_catalog(
    _: dict[str, Any] = Depends(
        get_current_user
    ),
) -> ManualCatalogResponse:
    if not manual_service.is_ready:
        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),

            detail=(
                manual_service.load_error
                or
                "전체 매뉴얼 데이터가 준비되지 않았습니다."
            ),
        )

    return (
        _catalog_response()
    )


# ---------------------------------------------------------
# 관리자 전체 매뉴얼 조회
# ---------------------------------------------------------

@router.get(
    "/admin/manual",
    response_model=ManualCatalogResponse,
)
def get_admin_manual_catalog(
    _: dict[str, Any] = Depends(
        require_admin
    ),
) -> ManualCatalogResponse:
    if not manual_service.is_ready:
        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),

            detail=(
                manual_service.load_error
                or
                "전체 매뉴얼 데이터가 준비되지 않았습니다."
            ),
        )

    return (
        _catalog_response()
    )


# ---------------------------------------------------------
# 관리자 신규 민원 대응 추가
# ---------------------------------------------------------

@router.post(
    "/admin/manual",
    response_model=ManualCatalogEntry,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def create_admin_manual_entry(
    request: AdminManualInput,

    user: dict[str, Any] = Depends(
        require_admin
    ),
) -> ManualCatalogEntry:
    try:
        entry = (
            manual_service
            .create_entry(
                payload=(
                    request
                    .model_dump(
                        exclude_unset=True
                    )
                ),

                user_id=int(
                    user[
                        "id"
                    ]
                ),
            )
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),

            detail=str(
                exc
            ),

        ) from exc

    return ManualCatalogEntry(
        **entry
    )


# ---------------------------------------------------------
# 기존 또는 신규 매뉴얼 수정
# ---------------------------------------------------------

@router.put(
    "/admin/manual/{entry_id}",
    response_model=ManualCatalogEntry,
)
def update_admin_manual_entry(
    entry_id: str,

    request: AdminManualInput,

    user: dict[str, Any] = Depends(
        require_admin
    ),
) -> ManualCatalogEntry:
    try:
        entry = (
            manual_service
            .update_entry(
                entry_id=(
                    entry_id
                ),

                payload=(
                    request
                    .model_dump(
                        exclude_unset=True
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
                "수정할 매뉴얼 항목을 찾을 수 없습니다."
            ),

        ) from exc

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),

            detail=str(
                exc
            ),

        ) from exc

    return ManualCatalogEntry(
        **entry
    )


# ---------------------------------------------------------
# 기존 항목:
#   관리자 수정본 제거 → 원본 복구
#
# 관리자 신규 항목:
#   완전 삭제
# ---------------------------------------------------------

@router.delete(
    "/admin/manual/{entry_id}",
    response_model=ManualAdminDeleteResponse,
)
def delete_or_restore_admin_manual_entry(
    entry_id: str,

    _: dict[str, Any] = Depends(
        require_admin
    ),
) -> ManualAdminDeleteResponse:
    try:
        action = (
            manual_service
            .delete_or_restore(
                entry_id
            )
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),

            detail=(
                "삭제 또는 복구할 매뉴얼 항목을 찾을 수 없습니다."
            ),

        ) from exc

    return ManualAdminDeleteResponse(
        ok=True,
        action=action,
    )