from __future__ import annotations

from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)


# ---------------------------------------------------------
# 검색 요청
# ---------------------------------------------------------

class SearchRequest(BaseModel):

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
    )


# ---------------------------------------------------------
# 담당 부서 분기 정보
# ---------------------------------------------------------

class DepartmentRouting(BaseModel):

    department: str

    condition: str

    confidence: str


# ---------------------------------------------------------
# 담당 부서 연락처
# ---------------------------------------------------------

class DepartmentContact(BaseModel):

    department: str = ""

    label: str = ""

    phone: str = ""

    note: str = ""

    sourceUrl: str = ""


# ---------------------------------------------------------
# 상황별 처리 분기
# ---------------------------------------------------------

class DecisionBranch(BaseModel):

    condition: str

    actions: List[str] = Field(
        default_factory=list
    )

    response: str = ""


# ---------------------------------------------------------
# 상급 보고 / 이관 규칙
# ---------------------------------------------------------

class EscalationRule(BaseModel):

    condition: str

    action: str


# ---------------------------------------------------------
# 검색 결과 한 건
# ---------------------------------------------------------

class SearchResult(BaseModel):

    id: str

    kind: str

    category: str

    documentName: str

    civilType: str

    department: str

    departments: List[str] = Field(
        default_factory=list
    )

    departmentContacts: List[
        DepartmentContact
    ] = Field(
        default_factory=list
    )

    paragraphSummary: str

    guidance: str

    note: str = ""

    updatedAt: str = ""

    relevance: int = Field(
        ge=0,
        le=100,
    )

    tags: List[str] = Field(
        default_factory=list
    )

    evidenceLevel: str

    sourceReference: str = ""

    sourcePages: List[int] = Field(
        default_factory=list
    )

    matchedPage: Optional[int] = None

    originalUrl: Optional[str] = None

    candidateCount: Optional[int] = None

    departmentRouting: List[
        DepartmentRouting
    ] = Field(
        default_factory=list
    )

    caseKind: Optional[str] = None

    intakeQuestions: List[str] = Field(
        default_factory=list
    )

    immediateActions: List[str] = Field(
        default_factory=list
    )

    decisionBranches: List[
        DecisionBranch
    ] = Field(
        default_factory=list
    )

    responseScripts: List[str] = Field(
        default_factory=list
    )

    escalationRules: List[
        EscalationRule
    ] = Field(
        default_factory=list
    )

    cautions: List[str] = Field(
        default_factory=list
    )


# ---------------------------------------------------------
# 전체 검색 응답
# ---------------------------------------------------------

class SearchResponse(BaseModel):

    query: str

    tier: str

    message: str

    resultCount: int

    recommendedDepartments: List[
        str
    ] = Field(
        default_factory=list
    )

    relevanceNotice: str

    results: List[
        SearchResult
    ] = Field(
        default_factory=list
    )