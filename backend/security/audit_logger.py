"""Audit logging service recording security-related events to trace files and memory registers."""

import os
import time
import json
import uuid
from typing import List, Optional
from backend.models.audit_event import AuditEvent
from backend.config import BASE_DIR

AUDIT_LOG_PATH = os.path.join(BASE_DIR, "logs", "audit.log")


class AuditLogger:
    """Records authentication, authorization, and permission logs centrally."""

    _in_memory_logs: List[AuditEvent] = []
    _max_memory_logs = 100

    @classmethod
    def record_event(
        cls,
        event_type: str,
        resource: str,
        status: str,
        detail: str,
        user_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> AuditEvent:
        """Records a structured security trace event to log files and memory.

        Args:
            event_type: LOGIN, API_ACCESS, ACCESS_DENIED, etc.
            resource: Path or target resource.
            status: SUCCESS or FAILED.
            detail: Context diagnostic details.
            user_id: User identifier.
            role: Active role name.

        Returns:
            AuditEvent: Documented audit event.
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            event_type=event_type,
            user_id=user_id,
            role=role,
            resource=resource,
            status=status,
            detail=detail
        )

        # 1. Append in-memory registry
        cls._in_memory_logs.append(event)
        if len(cls._in_memory_logs) > cls._max_memory_logs:
            cls._in_memory_logs.pop(0)

        # 2. Append file registry
        try:
            os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
            with open(AUDIT_LOG_PATH, "a") as f:
                f.write(json.dumps(event.model_dump()) + "\n")
        except Exception as e:
            # Fallback console logs
            print(f"Failed writing audit log: {str(e)}")

        print(f"[AUDIT LOG] {event.timestamp} | {event.event_type} | User: {event.user_id} | Status: {event.status} | Detail: {event.detail}")
        return event

    @classmethod
    def get_logs(cls) -> List[AuditEvent]:
        """Returns the in-memory buffered audit logs."""
        return cls._in_memory_logs
