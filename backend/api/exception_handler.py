"""Global exception handlers for the API Gateway formatting error responses uniformly."""

import time
from fastapi import Request
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.api.response_builder import ResponseBuilder
from backend.utils.logger import logger


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles standard HTTPExceptions."""
    request_id = getattr(request.state, "request_id", "N/A")
    exec_time = (time.perf_counter() - getattr(request.state, "start_time", time.perf_counter())) * 1000.0
    
    logger.warning(f"Validation Failed: {exc.detail}")

    res = ResponseBuilder.error(
        code=exc.status_code,
        detail=exc.detail,
        type_str="HTTPException",
        message="HTTP error occurred.",
        request_id=request_id,
        execution_time_ms=exec_time
    )
    return JSONResponse(status_code=exc.status_code, content=res.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles pydantic validation exceptions."""
    request_id = getattr(request.state, "request_id", "N/A")
    exec_time = (time.perf_counter() - getattr(request.state, "start_time", time.perf_counter())) * 1000.0

    errors_summary = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()])
    logger.warning(f"Validation Failed: {errors_summary}")

    res = ResponseBuilder.error(
        code=422,
        detail=errors_summary,
        type_str="ValidationError",
        message="Request model validation failed.",
        request_id=request_id,
        execution_time_ms=exec_time
    )
    return JSONResponse(status_code=422, content=res.model_dump())


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles unhandled general exceptions."""
    request_id = getattr(request.state, "request_id", "N/A")
    exec_time = (time.perf_counter() - getattr(request.state, "start_time", time.perf_counter())) * 1000.0

    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)

    res = ResponseBuilder.error(
        code=500,
        detail=str(exc),
        type_str="InternalError",
        message="An unhandled internal server error occurred.",
        request_id=request_id,
        execution_time_ms=exec_time
    )
    return JSONResponse(status_code=500, content=res.model_dump())
