from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
)


# ---------------------------------------------------------
# 공용 전화번호부 한 건
#
# 일반 사용자 화면과 관리자 화면에서
# 공통으로 사용하는 형식
# ---------------------------------------------------------

class ContactDirectoryEntry(BaseModel):

    id: str

    group: str

    organization: str

    label: str

    phone: str

    note: str = ""

    source: str = ""

    sourceUrl: str = ""


# ---------------------------------------------------------
# 전화번호부 전체 조회 응답
#
# GET /api/contacts
# GET /api/admin/contacts
# ---------------------------------------------------------

class ContactDirectoryResponse(BaseModel):

    source: str

    verifiedAt: str

    notice: str

    contacts: list[
        ContactDirectoryEntry
    ] = Field(
        default_factory=list
    )


# ---------------------------------------------------------
# 관리자 연락처 추가/수정 요청
#
# POST /api/admin/contacts
# PUT  /api/admin/contacts/{id}
# ---------------------------------------------------------

class AdminContactInput(BaseModel):

    group: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    organization: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    label: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    phone: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    note: str = Field(
        default="",
        max_length=1000,
    )

    sourceUrl: str = Field(
        default="",
        max_length=1000,
    )