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
)

from backend.schemas.manual import (
    ManualCatalogResponse,
)

from backend.services.manual_service import (
    manual_service,
)


# ---------------------------------------------------------
# 전체 매뉴얼 API
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api",
    tags=["manual"],
)


# ---------------------------------------------------------
# 전체 매뉴얼 조회
#
# 프론트:
# GET /api/manual
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
    """
    로그인한 사용자가
    전체 매뉴얼을 조회합니다.
    """

    if not manual_service.is_ready:

        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),

            detail=(
                manual_service.load_error
                or
                (
                    "전체 매뉴얼 데이터가 "
                    "준비되지 않았습니다."
                )
            ),
        )


    data = (
        manual_service
        .response_data()
    )


    return ManualCatalogResponse(
        **data
    )