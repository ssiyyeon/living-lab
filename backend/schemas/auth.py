from __future__ import annotations

from pydantic import BaseModel, Field


class AuthStatusResponse(BaseModel):
    needsSetup: bool


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=200)


class SetupRequest(LoginRequest):
    displayName: str = Field(min_length=1, max_length=40)


class UserResponse(BaseModel):
    id: int
    username: str
    displayName: str
    role: str
