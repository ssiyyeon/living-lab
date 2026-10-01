from fastapi import APIRouter, Depends, HTTPException

from backend.routers.auth import require_user

from backend.schemas.search import (
    ContactDirectoryResponse,
    ManualCatalogResponse,
    QuickGuideListResponse,
    SearchRequest,
    SearchResponse,
)

from backend.services.search_service import (
    SearchServiceUnavailable,
    search_service,
)
from backend.services.contact_service import merge_contact_directory
from backend.services.content_service import merge_quick_guides


router = APIRouter(
    prefix="/api",
    tags=["search"],
    dependencies=[Depends(require_user)],
)


@router.get(
    "/guides",
    response_model=QuickGuideListResponse,
)
def list_quick_guides() -> QuickGuideListResponse:

    return QuickGuideListResponse(
        **merge_quick_guides(search_service.get_quick_guides())
    )


@router.get(
    "/manual",
    response_model=ManualCatalogResponse,
)
def list_manual_catalog() -> ManualCatalogResponse:

    return ManualCatalogResponse(
        **search_service.get_manual_catalog()
    )


@router.get(
    "/contacts",
    response_model=ContactDirectoryResponse,
)
def list_contact_directory() -> ContactDirectoryResponse:

    return ContactDirectoryResponse(
        **merge_contact_directory(search_service.get_contact_directory())
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
