from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.routers.auth import require_admin
from backend.schemas.admin import AdminContactInput, AdminGuideInput, DeleteResponse
from backend.schemas.search import (
    ContactDirectoryEntry,
    ContactDirectoryResponse,
    QuickGuide,
    QuickGuideListResponse,
)
from backend.services.contact_service import find_contact, hide_contact, merge_contact_directory, save_contact
from backend.services.content_service import delete_guide_override, merge_quick_guides, save_guide_override
from backend.services.search_service import search_service


router = APIRouter(prefix="/api/admin", tags=["admin"])
PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{2,40}$")


def _payload(request: AdminContactInput) -> dict[str, str]:
    if not PHONE_PATTERN.fullmatch(request.phone.strip()):
        raise HTTPException(status_code=422, detail="전화번호 형식을 확인해 주세요.")
    return request.model_dump()


@router.get("/contacts", response_model=ContactDirectoryResponse)
def list_admin_contacts(_: dict[str, Any] = Depends(require_admin)) -> ContactDirectoryResponse:
    return ContactDirectoryResponse(**merge_contact_directory(search_service.get_contact_directory()))


@router.post("/contacts", response_model=ContactDirectoryEntry, status_code=status.HTTP_201_CREATED)
def create_admin_contact(
    request: AdminContactInput,
    user: dict[str, Any] = Depends(require_admin),
) -> ContactDirectoryEntry:
    return ContactDirectoryEntry(
        **save_contact(contact_id=None, payload=_payload(request), user_id=int(user["id"]))
    )


@router.put("/contacts/{contact_id}", response_model=ContactDirectoryEntry)
def update_admin_contact(
    contact_id: str,
    request: AdminContactInput,
    user: dict[str, Any] = Depends(require_admin),
) -> ContactDirectoryEntry:
    if not find_contact(search_service.get_contact_directory(), contact_id):
        raise HTTPException(status_code=404, detail="연락처를 찾지 못했습니다.")
    return ContactDirectoryEntry(
        **save_contact(contact_id=contact_id, payload=_payload(request), user_id=int(user["id"]))
    )


@router.delete("/contacts/{contact_id}", response_model=DeleteResponse)
def delete_admin_contact(
    contact_id: str,
    user: dict[str, Any] = Depends(require_admin),
) -> DeleteResponse:
    contact = find_contact(search_service.get_contact_directory(), contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="연락처를 찾지 못했습니다.")
    hide_contact(contact, int(user["id"]))
    return DeleteResponse(ok=True)


@router.get("/guides", response_model=QuickGuideListResponse)
def list_admin_guides(_: dict[str, Any] = Depends(require_admin)) -> QuickGuideListResponse:
    return QuickGuideListResponse(**merge_quick_guides(search_service.get_quick_guides()))


@router.put("/guides/{guide_id}", response_model=QuickGuide)
def update_admin_guide(
    guide_id: str,
    request: AdminGuideInput,
    user: dict[str, Any] = Depends(require_admin),
) -> QuickGuide:
    base_catalog = search_service.get_quick_guides()
    base_guide = next((guide for guide in base_catalog["guides"] if guide.get("id") == guide_id), None)
    if not base_guide:
        raise HTTPException(status_code=404, detail="업무 안내를 찾지 못했습니다.")
    save_guide_override(
        guide_id=guide_id,
        payload=request.model_dump(),
        user_id=int(user["id"]),
    )
    merged = merge_quick_guides(base_catalog)
    guide = next(item for item in merged["guides"] if item.get("id") == guide_id)
    return QuickGuide(**guide)


@router.delete("/guides/{guide_id}", response_model=DeleteResponse)
def reset_admin_guide(
    guide_id: str,
    _: dict[str, Any] = Depends(require_admin),
) -> DeleteResponse:
    delete_guide_override(guide_id)
    return DeleteResponse(ok=True)
