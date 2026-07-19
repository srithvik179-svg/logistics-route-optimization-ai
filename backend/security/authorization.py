"""Authorization dependency service checking permission scopes for role-based access control (RBAC)."""

from fastapi import Depends, HTTPException, status
from backend.security.authentication import get_current_user
from backend.security.audit_logger import AuditLogger
from backend.models.security_context import UserPrincipal


class PermissionChecker:
    """RBAC validation checker generating FastAPI dependency parameters."""

    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    def __call__(
        self,
        current_user: UserPrincipal = Depends(get_current_user)
    ) -> UserPrincipal:
        """Dependency invocation logic checking current user principal scopes.

        Args:
            current_user: Authenticated user context.

        Returns:
            UserPrincipal: Authenticated user context if authorized.
        """
        if self.required_permission not in current_user.permissions:
            AuditLogger.record_event(
                event_type="ACCESS_DENIED",
                resource=f"Permission: {self.required_permission}",
                status="FAILED",
                detail=f"User '{current_user.username}' with role '{current_user.role.value}' has insufficient scopes.",
                user_id=current_user.user_id,
                role=current_user.role.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient permissions. Required: '{self.required_permission}'"
            )

        # Successful check audit log
        AuditLogger.record_event(
            event_type="API_ACCESS",
            resource=f"Permission: {self.required_permission}",
            status="SUCCESS",
            detail=f"User '{current_user.username}' successfully accessed resource.",
            user_id=current_user.user_id,
            role=current_user.role.value
        )
        return current_user


# Global helper shortcuts
def require_permission(permission: str) -> PermissionChecker:
    """Returns a PermissionChecker dependency hook for route protections."""
    return PermissionChecker(permission)
