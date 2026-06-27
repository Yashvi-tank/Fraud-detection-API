"""User API validation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    """Registration request payload."""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")


class UserLogin(BaseModel):
    """Login credentials payload."""

    username: str = Field(...)
    password: str = Field(...)


class UserResponse(BaseModel):
    """User account details response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Successful authentication response payload returning JWT access token."""

    access_token: str
    token_type: str = "bearer"
