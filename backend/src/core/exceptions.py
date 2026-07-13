import datetime
from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.logging import logger


class APIException(Exception):
    """
    Base application-wide exception context.
    """
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        "API exception intercepted",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        correlation_id=correlation_id
    )

    payload = {
        "error_code": exc.error_code,
        "message": exc.message,
        "correlation_id": correlation_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "details": exc.details
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.warn(
        "Request payload schema validation failure",
        correlation_id=correlation_id,
        errors=exc.errors()
    )

    payload = {
        "error_code": "VALIDATION_FAILURE",
        "message": "The request payload failed schema validation validation guidelines.",
        "correlation_id": correlation_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "details": {"validation_errors": exc.errors()}
    }
    return JSONResponse(status_code=422, content=payload)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.exception(
        "Unhandled system-level runtime exception intercepted",
        correlation_id=correlation_id,
        error=str(exc)
    )

    payload = {
        "error_code": "INTERNAL_SYSTEM_ERROR",
        "message": "An unexpected error occurred during execution. Please contact support.",
        "correlation_id": correlation_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "details": {}
    }
    return JSONResponse(status_code=500, content=payload)
