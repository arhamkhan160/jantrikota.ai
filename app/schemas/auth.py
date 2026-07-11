"""
schemas/auth.py
Auth request/response models.
"""

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    user: dict | None = None


class UserResponse(BaseModel):
    id: str | None = None
    email: str | None = None
