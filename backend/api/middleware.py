"""API Gateway middleware for tracing, logging, timing, and formatting responses."""

import uuid
import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from backend.api.response_builder import ResponseBuilder
from backend.utils.logger import logger


class APIGatewayMiddleware(BaseHTTPMiddleware):
    """Intercepts incoming API requests to track timing, log calls, and format JSON responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only process requests under the /api/ prefix
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        # Tracing and timing setup
        req_id = str(uuid.uuid4())
        request.state.request_id = req_id
        request.state.start_time = time.perf_counter()

        logger.info(f"Request Received: {request.method} {request.url.path} | Request ID: {req_id}")

        try:
            response = await call_next(request)
        except Exception as e:
            # Let the exception handler catch it
            raise e

        # Wrap successful JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            # Reconstruct response body
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            try:
                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                body_json = None

            if body_json is not None:
                # Check if it is already formatted as APIResponse
                is_wrapped = isinstance(body_json, dict) and "status" in body_json and "execution_time_ms" in body_json
                
                if not is_wrapped:
                    exec_time = (time.perf_counter() - request.state.start_time) * 1000.0
                    wrapped = ResponseBuilder.success(
                        payload=body_json,
                        message="Request processed successfully.",
                        request_id=req_id,
                        execution_time_ms=exec_time
                    )
                    
                    body_bytes = json.dumps(wrapped.model_dump()).encode("utf-8")
                    
                    # Update content length headers
                    response.headers["content-length"] = str(len(body_bytes))

            # Recreate StreamingResponse
            async def body_iterator():
                yield body_bytes

            response = StreamingResponse(
                body_iterator(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        exec_time_total = (time.perf_counter() - request.state.start_time) * 1000.0
        logger.info(f"Response Generated: {request.method} {request.url.path} | Status: {response.status_code} | Time: {exec_time_total:.2f} ms")
        return response
