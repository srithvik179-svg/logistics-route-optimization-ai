"""Authentication and security audit routing endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List
from backend.models.user_role import UserRole
from backend.models.security_context import TokenData, UserPrincipal
from backend.models.audit_event import AuditEvent
from backend.security.jwt_manager import JWTManager
from backend.security.authorization import require_permission
from backend.security.audit_logger import AuditLogger

security_router = APIRouter(prefix="/api/v1/security", tags=["Security"])


class TokenRequest(BaseModel):
    """User credentials request model exchange payload."""
    username: str = Field(description="Username credential")
    password: str = Field(description="Password credential")


# Mock user database for validation
MOCK_USERS = {
    "admin": {"password": "admin123", "role": UserRole.ADMINISTRATOR, "id": "user-admin-001"},
    "manager": {"password": "manager123", "role": UserRole.OPERATIONS_MANAGER, "id": "user-mgr-002"},
    "analyst": {"password": "analyst123", "role": UserRole.LOGISTICS_ANALYST, "id": "user-analyst-003"},
    "viewer": {"password": "viewer123", "role": UserRole.VIEWER, "id": "user-viewer-004"}
}


@security_router.post("/auth/token", response_model=TokenData)
def login_for_access_token(payload: TokenRequest):
    """Exchanges mock credentials for a signed JWT access token."""
    username = payload.username
    password = payload.password

    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        AuditLogger.record_event(
            event_type="LOGIN",
            resource="auth/token",
            status="FAILED",
            detail=f"Failed login attempt for username '{username}' due to invalid credentials."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username credentials or password."
        )

    # Issue token
    role = user["role"]
    user_id = user["id"]
    token_data = JWTManager.create_tokens(user_id, username, role)

    AuditLogger.record_event(
        event_type="LOGIN",
        resource="auth/token",
        status="SUCCESS",
        detail=f"User '{username}' logged in successfully.",
        user_id=user_id,
        role=role.value
    )

    return token_data


@security_router.get("/audit-logs", response_model=List[AuditEvent])
def get_security_audit_logs(
    current_user: UserPrincipal = Depends(require_permission("admin:write"))
):
    """Retrieves in-memory security audit events list. Restricted to Administrator role."""
    return AuditLogger.get_logs()
