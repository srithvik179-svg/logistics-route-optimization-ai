"""Pydantic model representing a trace event log entry for engine executions."""

from pydantic import BaseModel, Field
from typing import Optional


class TraceEvent(BaseModel):
    """Logs the performance footprint of single internal engine processing runs."""
    trace_id: str = Field(description="Unique trace identifier UUID")
    timestamp: str = Field(description="ISO-8601 formatting trace timestamp")
    service_name: str = Field(description="Name of the execution engine triggered")
    execution_time_ms: float = Field(description="Calculation run latency in milliseconds")
    status: str = Field(description="Run status: SUCCESS or ERROR")
    error_message: Optional[str] = Field(default=None, description="Detailed error log if execution failed")
