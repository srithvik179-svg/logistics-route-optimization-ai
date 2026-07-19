"""Pydantic model representing a compiled diagnostics system report."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class DiagnosticReport(BaseModel):
    """Encapsulates system telemetry analysis to pinpoint slow paths or error patterns."""
    report_id: str = Field(description="Unique diagnostic report identifier UUID")
    timestamp: str = Field(description="ISO-8601 formatting report timestamp")
    performance_summary: str = Field(description="Human-readable performance health description")
    slowest_services: List[str] = Field(default_factory=list, description="List of names of slowest response services")
    most_requested_apis: List[str] = Field(default_factory=list, description="List of most frequently accessed path strings")
    failure_analysis: Dict[str, Any] = Field(default_factory=dict, description="Dictionary summarizing error code counts")
    recent_exceptions: List[str] = Field(default_factory=list, description="List of recently encountered tracebacks or error messages")
