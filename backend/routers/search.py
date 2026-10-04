from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from backend.routers.auth import (
    get_current_user,
)

from backend.schemas.search import (
    SearchRequest,
    SearchResponse,
)

from backend.services.combined_search_service import (
    combined_search_service,
)

from backend.services.search_service import (
    SearchServiceUnavailable,
)


# ---------------------------------------------------------
# 검색 API
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api",
    tags=["search"],
)


# ---------------------------------------------------------
# 민원 검색
#
# 기존 데이터팀 검색
# +
# 관리자 수정/추가 안내 검색
#
# 두 결과를 합쳐서 반환
# ---------------------------------------------------------

@router.post(
    "/search",
    response_model=SearchResponse,
)
def search_complaint(
    request: SearchRequest,

    _: dict[str, Any] = Depends(
        get_current_user
    ),
) -> SearchResponse:

    query = (
        request
        .query
        .strip()
    )


    # 빈 검색어 방지
    if not query:

        raise HTTPException(
            status_code=400,

            detail=(
                "검색어를 입력해 주세요."
            ),
        )


    try:

        result = (
            combined_search_service
            .search(
                query=query,

                top_k=(
                    request
                    .top_k
                ),
            )
        )


    except SearchServiceUnavailable as exc:

        raise HTTPException(
            status_code=503,

            detail=(
                "검색 엔진이 아직 준비되지 않았습니다. "
                "검색 데이터와 인덱스를 확인해 주세요."
            ),

        ) from exc


    return SearchResponse(
        **result
    )