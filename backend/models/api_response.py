"""Pydantic models representing standardized enterprise API gateway responses and error structures."""

from pydantic import BaseModel, Field
from typing import Any, Optional


class APIError(BaseModel):
    """Standardized representation of error details in the API response."""
    code: int = Field(description="Numerical HTTP status or custom error code")
    detail: str = Field(description="Detailed error message explaining the failure reason")
    type: Optional[str] = Field(default="InternalError", description="Error categorization type")


class APIResponse(BaseModel):
    """Global envelope wrapping all API request responses and errors uniformly."""
    status: str = Field(description="Status indicating result: success or error")
    message: str = Field(description="Human-readable status summary message")
    timestamp: str = Field(description="ISO-8601 formatted execution timestamp")
    request_id: str = Field(description="Unique request trace identifier UUID")
    execution_time_ms: float = Field(description="Calculation run duration in milliseconds")
    payload: Optional[Any] = Field(default=None, description="Response payload body")
    error: Optional[APIError] = Field(default=None, description="Detailed error information if status is error")
