"""Pydantic models representing user principals and token payloads."""

from pydantic import BaseModel, Field
from typing import List
from backend.models.user_role import UserRole


class UserPrincipal(BaseModel):
    """Represents the authenticated user context (principal) inside security routines."""
    user_id: str = Field(description="Unique user identifier")
    username: str = Field(description="Unique username credentials")
    role: UserRole = Field(description="Assigned RBAC role")
    permissions: List[str] = Field(default_factory=list, description="Computed permission scopes list")


class TokenData(BaseModel):
    """Envelope wrapping generated access and refresh tokens."""
    access_token: str = Field(description="Cryptographically signed JWT access token")
    refresh_token: str = Field(description="Refresh token exchange credential")
    token_type: str = Field(default="bearer", description="Auth token type schema prefix")
    expires_in_seconds: int = Field(default=3600, description="Token duration window")
