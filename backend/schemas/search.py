from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="사용자가 입력한 민원 내용 또는 검색어",
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
        description="반환할 최대 검색 결과 수",
    )


class DepartmentRouting(BaseModel):
    department: str
    condition: str
    confidence: str


class DepartmentContact(BaseModel):
    department: str
    label: str
    phone: str
    note: str
    sourceUrl: str


class DecisionBranch(BaseModel):
    condition: str
    actions: List[str] = Field(default_factory=list)
    response: str


class EscalationRule(BaseModel):
    condition: str
    action: str


class QuickGuideSection(BaseModel):
    title: str
    timeLabel: str
    steps: List[str] = Field(default_factory=list)


class QuickGuideContact(BaseModel):
    group: str
    organization: str
    label: str
    phone: str


class QuickGuide(BaseModel):
    id: str
    title: str
    description: str
    sourcePages: List[int] = Field(default_factory=list)
    sections: List[QuickGuideSection] = Field(default_factory=list)
    cautions: List[str] = Field(default_factory=list)
    contacts: List[QuickGuideContact] = Field(default_factory=list)
    restrictedNotice: Optional[str] = None


class QuickGuideListResponse(BaseModel):
    source: str
    guides: List[QuickGuide] = Field(default_factory=list)


class ContactDirectoryEntry(BaseModel):
    id: str
    group: str
    organization: str
    label: str
    phone: str
    note: str
    source: str
    sourceUrl: str


class ContactDirectoryResponse(BaseModel):
    source: str
    verifiedAt: str
    notice: str
    contacts: List[ContactDirectoryEntry] = Field(default_factory=list)


class ManualCatalogEntry(BaseModel):
    id: str
    entryType: str
    group: str
    topic: str
    title: str
    breadcrumb: List[str] = Field(default_factory=list)
    sourcePages: List[int] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    summary: str
    content: str
    intakeQuestions: List[str] = Field(default_factory=list)
    immediateActions: List[str] = Field(default_factory=list)
    decisionBranches: List[DecisionBranch] = Field(default_factory=list)
    responseScripts: List[str] = Field(default_factory=list)
    escalationRules: List[EscalationRule] = Field(default_factory=list)
    cautions: List[str] = Field(default_factory=list)


class ManualCatalogResponse(BaseModel):
    source: str
    totalCount: int
    entries: List[ManualCatalogEntry] = Field(default_factory=list)


class SearchResult(BaseModel):
    id: str
    kind: str

    category: str
    documentName: str
    civilType: str

    department: str
    departments: List[str] = Field(default_factory=list)
    departmentContacts: List[DepartmentContact] = Field(default_factory=list)

    paragraphSummary: str
    keyActions: List[str] = Field(default_factory=list)
    originalText: str = ""
    guidance: str
    note: str

    updatedAt: str
    relevance: int = Field(ge=0, le=100)
    tags: List[str] = Field(default_factory=list)

    evidenceLevel: str

    sourceReference: str
    sourcePages: List[int] = Field(default_factory=list)
    matchedPage: Optional[int] = None
    originalUrl: Optional[str] = None

    candidateCount: Optional[int] = None

    departmentRouting: List[DepartmentRouting] = Field(
        default_factory=list
    )

    caseKind: Optional[str] = None
    intakeQuestions: List[str] = Field(default_factory=list)
    immediateActions: List[str] = Field(default_factory=list)
    decisionBranches: List[DecisionBranch] = Field(default_factory=list)
    responseScripts: List[str] = Field(default_factory=list)
    escalationRules: List[EscalationRule] = Field(default_factory=list)
    cautions: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    tier: str
    message: str

    resultCount: int

    recommendedDepartments: List[str] = Field(
        default_factory=list
    )

    relevanceNotice: str

    results: List[SearchResult] = Field(
        default_factory=list
    )
