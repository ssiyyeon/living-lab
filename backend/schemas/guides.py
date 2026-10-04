from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class QuickGuideSection(BaseModel):
    """
    업무 안내 안의 한 개 처리 단계
    """

    title: str

    timeLabel: str = ""

    steps: list[str] = Field(
        default_factory=list
    )

    # 관리자가 새로 추가한 단계라면
    # 추가 날짜를 저장할 수 있음
    addedAt: Optional[str] = None


class QuickGuideContact(BaseModel):
    """
    안내에 연결된 연락처 정보
    """

    group: str

    organization: str

    label: str

    phone: str


class QuickGuide(BaseModel):
    """
    일반 사용자와 관리자 화면에 전달되는
    하나의 업무 안내 전체 데이터
    """

    id: str

    title: str

    description: str

    sourcePages: list[int] = Field(
        default_factory=list
    )

    sections: list[
        QuickGuideSection
    ] = Field(
        default_factory=list
    )

    cautions: list[str] = Field(
        default_factory=list
    )

    contacts: list[
        QuickGuideContact
    ] = Field(
        default_factory=list
    )

    restrictedNotice: Optional[str] = None

    updatedAt: Optional[str] = None


class QuickGuideListResponse(BaseModel):
    """
    여러 업무 안내를 한 번에 반환할 때 사용
    """

    source: str

    guides: list[
        QuickGuide
    ] = Field(
        default_factory=list
    )


class AdminGuideInput(BaseModel):
    """
    관리자가 업무 안내 내용을 수정해서
    백엔드로 보낼 때 사용하는 형식
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    sections: list[
        QuickGuideSection
    ] = Field(
        default_factory=list
    )

    cautions: list[str] = Field(
        default_factory=list
    )