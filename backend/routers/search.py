from fastapi import APIRouter, HTTPException

from backend.schemas.search import (
    QuickGuideListResponse,
    SearchRequest,
    SearchResponse,
)

from backend.services.search_service import (
    SearchServiceUnavailable,
    search_service,
)


router = APIRouter(
    prefix="/api",
    tags=["search"],
)


@router.get(
    "/guides",
    response_model=QuickGuideListResponse,
)
def list_quick_guides() -> QuickGuideListResponse:

    return QuickGuideListResponse(
        **search_service.get_quick_guides()
    )


@router.post(
    "/search",
    response_model=SearchResponse,
)
def search_complaint(
    request: SearchRequest,
) -> SearchResponse:

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="검색어를 입력해 주세요.",
        )

    try:
        result = search_service.search(
            query=query,
            top_k=request.top_k,
        )

    except SearchServiceUnavailable:
        raise HTTPException(
            status_code=503,
            detail=(
                "검색 엔진이 아직 준비되지 않았습니다. "
                "feature/data 통합 후 검색 인덱스를 생성해 주세요."
            ),
        )

    return SearchResponse(
        **result
    )
