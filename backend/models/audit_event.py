"""Pydantic model representing security audit events logging details."""

from pydantic import BaseModel, Field
from typing import Optional


class AuditEvent(BaseModel):
    """Represents a trace log entry documenting access attempts or configuration changes."""
    event_id: str = Field(description="Unique identifier UUID for the audit trace")
    timestamp: str = Field(description="ISO-8601 formatting timestamp")
    event_type: str = Field(description="Categorization code: LOGIN, API_ACCESS, ACCESS_DENIED, UNAUTHORIZED")
    user_id: Optional[str] = Field(default=None, description="Initiating user ID principal")
    role: Optional[str] = Field(default=None, description="Role of the initiator")
    resource: str = Field(description="Requested route resource path or action")
    status: str = Field(description="Status result: SUCCESS or FAILED")
    detail: str = Field(description="Explanatory diagnostic detail summary")
