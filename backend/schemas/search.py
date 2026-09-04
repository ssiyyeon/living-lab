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
    phoneNumbers: List[str] = Field(default_factory=list)


class OperatorOption(BaseModel):
    id: str
    label: str
    department: str
    status: str
    statusLabel: str
    actionSteps: List[str] = Field(default_factory=list)


class OperatorGuidance(BaseModel):
    mode: str
    headline: str
    question: Optional[str] = None
    actionSteps: List[str] = Field(default_factory=list)
    options: List[OperatorOption] = Field(default_factory=list)
    caution: str = ""


class SearchResult(BaseModel):
    id: str
    kind: str

    category: str
    documentName: str
    civilType: str

    department: str
    departments: List[str] = Field(default_factory=list)
    departmentContacts: List[DepartmentContact] = Field(
        default_factory=list
    )
    operatorGuidance: OperatorGuidance

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
