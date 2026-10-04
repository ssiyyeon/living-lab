from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    """
    로그인 후 프론트에 전달할 사용자 정보
    """

    id: int

    username: str

    displayName: str

    role: Literal[
        "admin",
        "staff",
    ]


class AuthStatusResponse(BaseModel):
    """
    관리자 계정이 아직 만들어지지 않았는지 확인할 때 사용
    """

    needsSetup: bool


class LoginRequest(BaseModel):
    """
    로그인할 때 프론트에서 보내는 데이터
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=200,
    )


class SetupAdminRequest(BaseModel):
    """
    최초 관리자 계정을 만들 때 사용하는 데이터
    """

    displayName: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=200,
    )