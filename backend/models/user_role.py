"""Enums and permissions mappings for Role-Based Access Control (RBAC)."""

from enum import Enum
from typing import List, Dict


class UserRole(str, Enum):
    """Available user roles in the enterprise system."""
    ADMINISTRATOR = "Administrator"
    OPERATIONS_MANAGER = "Operations Manager"
    LOGISTICS_ANALYST = "Logistics Analyst"
    BUSINESS_ANALYST = "Business Analyst"
    EXECUTIVE_VIEWER = "Executive Viewer"
    READ_ONLY_USER = "Read-Only User"
    VIEWER = "Viewer"
    SYSTEM_SERVICE = "System Service"


# Map roles to their specific permission scopes
ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.ADMINISTRATOR: [
        "analytics:read",
        "optimization:write",
        "inventory:read",
        "transit:read",
        "cost:read",
        "sla:read",
        "decision:read",
        "system:read",
        "admin:write"
    ],
    UserRole.OPERATIONS_MANAGER: [
        "analytics:read",
        "optimization:write",
        "inventory:read",
        "transit:read",
        "cost:read",
        "sla:read",
        "decision:read"
    ],
    UserRole.LOGISTICS_ANALYST: [
        "analytics:read",
        "optimization:write",
        "transit:read",
        "cost:read",
        "sla:read"
    ],
    UserRole.BUSINESS_ANALYST: [
        "analytics:read",
        "inventory:read",
        "cost:read",
        "sla:read",
        "decision:read"
    ],
    UserRole.VIEWER: [
        "analytics:read"
    ],
    UserRole.SYSTEM_SERVICE: [
        "analytics:read",
        "optimization:write",
        "inventory:read",
        "transit:read",
        "cost:read",
        "sla:read",
        "decision:read",
        "system:read"
    ]
}
