"""
Exception Handlers
Custom exception handlers for FastAPI to provide consistent error responses
"""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from models.error_models import (
    ErrorResponse,
    ValidationErrorResponse,
    get_utc_timestamp,
)
from utils.exceptions import AudioServiceException

logger = logging.getLogger(__name__)


async def audio_service_exception_handler(
    request: Request, exc: AudioServiceException
) -> JSONResponse:
    """
    Handle custom AudioServiceException and its subclasses

    Returns standardized error response with appropriate status code
    """
    logger.error(
        f"{exc.error_code} on {request.method} {request.url.path}: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    error_response = ErrorResponse(
        error=exc.error_code,
        detail=exc.message,
        status_code=exc.status_code,
        timestamp=get_utc_timestamp(),
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed field information

    Provides clear feedback about what fields failed validation
    """
    # Try to get request body for logging
    request_body = None
    try:
        request_body = await request.body()
        if request_body:
            request_body = request_body.decode("utf-8")
    except Exception:
        request_body = "Unable to read request body"

    logger.error(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "validation_errors": exc.errors(),
            "body": request_body,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    error_response = ValidationErrorResponse(
        detail="Request validation failed",
        timestamp=get_utc_timestamp(),
        validation_errors=exc.errors(),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions

    Logs full error details but returns safe error message to client
    """
    logger.exception(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    error_response = ErrorResponse(
        error="InternalServerError",
        detail="An unexpected error occurred. Please try again later.",
        status_code=500,
        timestamp=get_utc_timestamp(),
        path=str(request.url.path),
    )

    return JSONResponse(status_code=500, content=error_response.model_dump())


def register_exception_handlers(app):
    """
    Register all custom exception handlers with the FastAPI app

    Call this from main.py after creating the app instance
    """
    app.add_exception_handler(AudioServiceException, audio_service_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Custom exception handlers registered")
