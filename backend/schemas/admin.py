from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class AdminContactInput(BaseModel):
    group: str = Field(min_length=1, max_length=40)
    organization: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=2, max_length=40)
    note: str = Field(default="", max_length=300)
    sourceUrl: str = Field(default="", max_length=500)


class DeleteResponse(BaseModel):
    ok: bool


class AdminGuideSectionInput(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    timeLabel: str = Field(default="", max_length=100)
    steps: List[str] = Field(default_factory=list)


class AdminGuideInput(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=300)
    sections: List[AdminGuideSectionInput] = Field(default_factory=list)
    cautions: List[str] = Field(default_factory=list)
