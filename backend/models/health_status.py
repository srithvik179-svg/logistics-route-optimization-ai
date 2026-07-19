"""Pydantic models representing service-level and system-wide health states."""

from pydantic import BaseModel, Field
from typing import List


class ServiceHealth(BaseModel):
    """Represents the individual status check for a specific engine or database layer."""
    name: str = Field(description="Name of the service or layer monitored")
    status: str = Field(description="Status indicating availability: UP, DOWN, DEGRADED")
    response_time_ms: float = Field(description="Operational check response latency in milliseconds")
    detail: str = Field(description="Diagnostic details or error summaries if degraded")


class SystemHealthReport(BaseModel):
    """Aggregates all service statuses into a global health report."""
    overall_status: str = Field(description="Consolidated system state: UP, DOWN, DEGRADED")
    timestamp: str = Field(description="ISO-8601 formatting timestamp")
    services: List[ServiceHealth] = Field(default_factory=list, description="List of monitored backend services")
    checks_count: int = Field(description="Total number of service checks executed")
