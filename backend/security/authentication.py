"""Authentication dependency extracting and validating JWT tokens from headers."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.security.jwt_manager import JWTManager
from backend.security.audit_logger import AuditLogger
from backend.models.security_context import UserPrincipal

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> UserPrincipal:
    """FastAPI security dependency resolving authorization headers.

    Args:
        credentials: Auto-extracted bearer credentials.

    Returns:
        UserPrincipal: Valid authenticated user details.
    """
    if not credentials:
        AuditLogger.record_event(
            event_type="UNAUTHORIZED",
            resource="API_ROUTE",
            status="FAILED",
            detail="Missing Authorization headers."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    principal = JWTManager.decode_token(token)

    if not principal:
        AuditLogger.record_event(
            event_type="UNAUTHORIZED",
            resource="API_ROUTE",
            status="FAILED",
            detail="Invalid JWT signature or expired token."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Success validation log
    return principal
