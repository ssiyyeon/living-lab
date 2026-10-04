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

from backend.schemas.contacts import (
    AdminContactInput,
    ContactDirectoryEntry,
    ContactDirectoryResponse,
)

from backend.services.contact_service import (
    contact_service,
)


# ---------------------------------------------------------
# 연락처 관련 API
#
# 일반 사용자:
# GET /api/contacts
#
# 관리자:
# GET    /api/admin/contacts
# POST   /api/admin/contacts
# PUT    /api/admin/contacts/{contact_id}
# DELETE /api/admin/contacts/{contact_id}
# ---------------------------------------------------------

router = APIRouter(
    prefix="/api",
    tags=["contacts"],
)


# ---------------------------------------------------------
# 일반 사용자용 공용 전화번호부 조회
# ---------------------------------------------------------

@router.get(
    "/contacts",
    response_model=ContactDirectoryResponse,
)
def get_contacts(
    _: dict[str, Any] = Depends(
        get_current_user
    ),
) -> ContactDirectoryResponse:
    """
    일반 로그인 사용자가
    공용 전화번호부를 조회합니다.
    """

    data = (
        contact_service
        .response_data()
    )

    return ContactDirectoryResponse(
        **data
    )


# ---------------------------------------------------------
# 관리자용 공용 전화번호부 조회
# ---------------------------------------------------------

@router.get(
    "/admin/contacts",
    response_model=ContactDirectoryResponse,
)
def get_admin_contacts(
    _: dict[str, Any] = Depends(
        require_admin
    ),
) -> ContactDirectoryResponse:
    """
    관리자 페이지에서
    공용 전화번호부를 조회합니다.
    """

    data = (
        contact_service
        .response_data()
    )

    return ContactDirectoryResponse(
        **data
    )


# ---------------------------------------------------------
# 관리자 연락처 추가
# ---------------------------------------------------------

@router.post(
    "/admin/contacts",
    response_model=ContactDirectoryEntry,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_contact(
    request: AdminContactInput,

    user: dict[str, Any] = Depends(
        require_admin
    ),
) -> ContactDirectoryEntry:
    """
    관리자가 새로운 공용 연락처를 추가합니다.
    """

    try:

        created = (
            contact_service
            .create_contact(
                payload=(
                    request
                    .model_dump()
                ),

                user_id=int(
                    user["id"]
                ),
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),

            detail=str(
                exc
            ),

        ) from exc

    return ContactDirectoryEntry(
        **created
    )


# ---------------------------------------------------------
# 관리자 연락처 수정
# ---------------------------------------------------------

@router.put(
    "/admin/contacts/{contact_id}",
    response_model=ContactDirectoryEntry,
)
def update_admin_contact(
    contact_id: str,

    request: AdminContactInput,

    user: dict[str, Any] = Depends(
        require_admin
    ),
) -> ContactDirectoryEntry:
    """
    기존 공용 연락처를 수정합니다.
    """

    try:

        updated = (
            contact_service
            .update_contact(
                contact_id=contact_id,

                payload=(
                    request
                    .model_dump()
                ),

                user_id=int(
                    user["id"]
                ),
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),

            detail=str(
                exc
            ),

        ) from exc

    except KeyError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),

            detail=(
                "해당 연락처를 찾을 수 없습니다."
            ),

        ) from exc

    return ContactDirectoryEntry(
        **updated
    )


# ---------------------------------------------------------
# 관리자 연락처 숨김
#
# 실제 DB에서 완전히 삭제하지 않고
# is_hidden = 1로 변경
# ---------------------------------------------------------

@router.delete(
    "/admin/contacts/{contact_id}",
)
def delete_admin_contact(
    contact_id: str,

    user: dict[str, Any] = Depends(
        require_admin
    ),
) -> dict[str, bool]:
    """
    공용 전화번호를 사용자 화면에서 숨깁니다.
    """

    try:

        contact_service.hide_contact(
            contact_id=contact_id,

            user_id=int(
                user["id"]
            ),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_400_BAD_REQUEST
            ),

            detail=str(
                exc
            ),

        ) from exc

    except KeyError as exc:

        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),

            detail=(
                "해당 연락처를 찾을 수 없습니다."
            ),

        ) from exc

    return {
        "ok": True
    }