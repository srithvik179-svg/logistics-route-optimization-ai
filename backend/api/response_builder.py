"""API response builder utility wrapping payloads in the standardized APIResponse format."""

import time
from typing import Any, Optional
from backend.models.api_response import APIResponse, APIError


class ResponseBuilder:
    """Helper to wrap return objects uniformly in standardized response formats."""

    @classmethod
    def success(
        cls,
        payload: Any,
        message: str = "Request processed successfully.",
        request_id: str = "N/A",
        execution_time_ms: float = 0.0
    ) -> APIResponse:
        """Wraps success payload in the APIResponse format."""
        return APIResponse(
            status="success",
            message=message,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            request_id=request_id,
            execution_time_ms=round(execution_time_ms, 2),
            payload=payload,
            error=None
        )

    @classmethod
    def error(
        cls,
        code: int,
        detail: str,
        type_str: str = "InternalError",
        message: str = "An error occurred during execution.",
        request_id: str = "N/A",
        execution_time_ms: float = 0.0
    ) -> APIResponse:
        """Wraps error details in the APIResponse format."""
        err = APIError(
            code=code,
            detail=detail,
            type=type_str
        )
        return APIResponse(
            status="error",
            message=message,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            request_id=request_id,
            execution_time_ms=round(execution_time_ms, 2),
            payload=None,
            error=err
        )
