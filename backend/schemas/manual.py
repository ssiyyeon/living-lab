from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


# ---------------------------------------------------------
# 상황별 처리 분기
# ---------------------------------------------------------

class ManualDecisionBranch(BaseModel):

    condition: str

    actions: list[str] = Field(
        default_factory=list
    )

    response: str = ""


# ---------------------------------------------------------
# 보고 / 상향 기준
# ---------------------------------------------------------

class ManualEscalationRule(BaseModel):

    condition: str

    action: str


# ---------------------------------------------------------
# 전체 매뉴얼 한 항목
#
# section:
#   일반 매뉴얼 문서
#
# case:
#   상황별 대응 매뉴얼
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# 전체 매뉴얼 응답
#
# GET /api/manual
# ---------------------------------------------------------

class ManualCatalogResponse(BaseModel):

    source: str

    totalCount: int

    entries: list[
        ManualCatalogEntry
    ] = Field(
        default_factory=list
    )