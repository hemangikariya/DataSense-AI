import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.logging import logger


class CorrelationAndLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate correlation ID if not passed from Gateway
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Extract Workspace Tenant claims if present in headers
        org_id = request.headers.get("X-Organization-ID", "anonymous")
        workspace_id = request.headers.get("X-Workspace-ID", "anonymous")
        request.state.org_id = org_id
        request.state.workspace_id = workspace_id

        # Bind log variables contextually
        logger.bind(
            correlation_id=correlation_id,
            org_id=org_id,
            workspace_id=workspace_id
        )

        start_time = time.time()
        
        logger.info(
            "HTTP request received",
            method=request.method,
            url=str(request.url.path),
            client=request.client.host if request.client else "unknown"
        )

        try:
            response: Response = await call_next(request)
        except Exception:
            raise
        finally:
            process_time = time.time() - start_time
            logger.info(
                "HTTP request completed processing",
                method=request.method,
                url=str(request.url.path),
                duration_ms=round(process_time * 1000, 2)
            )

        # Set header response for tracing verification
        response.headers["X-Correlation-ID"] = correlation_id
        return response
