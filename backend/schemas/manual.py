from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ManualDecisionBranch(BaseModel):
    condition: str

    actions: list[str] = Field(
        default_factory=list
    )

    response: str = ""


class ManualEscalationRule(BaseModel):
    condition: str

    action: str


class ManualCatalogEntry(BaseModel):
    id: str

    entryType: Literal[
        "section",
        "case",
    ]

    group: str

    topic: str

    title: str

    breadcrumb: list[str] = Field(
        default_factory=list
    )

    sourcePages: list[int] = Field(
        default_factory=list
    )

    departments: list[str] = Field(
        default_factory=list
    )

    summary: str = ""

    content: str = ""

    intakeQuestions: list[str] = Field(
        default_factory=list
    )

    immediateActions: list[str] = Field(
        default_factory=list
    )

    decisionBranches: list[
        ManualDecisionBranch
    ] = Field(
        default_factory=list
    )

    responseScripts: list[str] = Field(
        default_factory=list
    )

    escalationRules: list[
        ManualEscalationRule
    ] = Field(
        default_factory=list
    )

    cautions: list[str] = Field(
        default_factory=list
    )

    # 관리자 화면에서 사용할 상태
    isCustom: bool = False

    isModified: bool = False

    addedAt: str | None = None

    updatedAt: str | None = None


class ManualCatalogResponse(BaseModel):
    source: str

    totalCount: int

    entries: list[
        ManualCatalogEntry
    ] = Field(
        default_factory=list
    )


# 관리자 추가/수정 요청
class AdminManualInput(BaseModel):
    entryType: Literal[
        "section",
        "case",
    ] = "case"

    group: str = Field(
        default="민원유형별 대응",
        min_length=1,
        max_length=100,
    )

    topic: str = Field(
        default="",
        max_length=200,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    breadcrumb: list[str] = Field(
        default_factory=list
    )

    sourcePages: list[int] = Field(
        default_factory=list
    )

    departments: list[str] = Field(
        default_factory=list
    )

    summary: str = ""

    content: str = ""

    intakeQuestions: list[str] = Field(
        default_factory=list
    )

    immediateActions: list[str] = Field(
        default_factory=list
    )

    decisionBranches: list[
        ManualDecisionBranch
    ] = Field(
        default_factory=list
    )

    responseScripts: list[str] = Field(
        default_factory=list
    )

    escalationRules: list[
        ManualEscalationRule
    ] = Field(
        default_factory=list
    )

    cautions: list[str] = Field(
        default_factory=list
    )


class ManualAdminDeleteResponse(BaseModel):
    ok: bool

    action: Literal[
        "restored",
        "deleted",
    ]