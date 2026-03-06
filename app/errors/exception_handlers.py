"""Global exception handlers for the FastAPI application."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException

from app.errors.exceptions import AppError
from app.schemas.error_response import ErrorResponse
from app.utils.request_info import get_request_info

# Mapping of common HTTP status codes to standardized error codes for consistent API responses
HTTP_ERROR_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    408: "REQUEST_TIMEOUT",
    409: "RESOURCE_CONFLICT",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}


def build_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> ErrorResponse:
    """Create a consistent error content structure as ErrorResponse."""
    content: dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
        },
    }
    if details:
        content["error"]["details"] = details
    return ErrorResponse(**content)


def build_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Log the error event and build a JSONResponse with consistent structure."""
    response_model = build_error_response(error_code, message, details)
    return JSONResponse(
        status_code=status_code, content=response_model.model_dump(exclude_none=True)
    )


def log_error(
    *,
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    event: str,
    details: dict[str, Any] | None = None,
    level: str = "INFO",
    exception: bool = False,
) -> None:
    """Log the error event with structured context."""
    request_info = get_request_info(request)
    log = logger.bind(
        **asdict(request_info),
        status_code=status_code,
        error_code=error_code,
        error_message=message,
    ).opt(exception=exception)
    if details:
        log = log.bind(error_details=details)
    log.log(level, event)


def normalize_validation_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    """Normalize Pydantic/FastAPI validation errors into API error shape."""
    errors: list[dict[str, str]] = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", ()))
        errors.append(
            {
                "field": field,
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )
    return errors


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle all custom application exceptions."""
        log_level = "ERROR" if exc.status_code >= 500 else "INFO"
        log_error(
            request=request,
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            event="app_exception",
            level=log_level,
        )
        return build_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        log_error(
            request=request,
            status_code=422,
            error_code="INVALID_INPUT",
            message="Request validation failed",
            details={"errors": normalize_validation_errors(exc)},
            event="validation_error",
        )
        return build_response(
            status_code=422,
            error_code="INVALID_INPUT",
            message="Request validation failed",
            details={"errors": normalize_validation_errors(exc)},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle standard HTTP exceptions raised by FastAPI or Starlette."""
        error_code = HTTP_ERROR_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
        log_error(
            request=request,
            status_code=exc.status_code,
            error_code=error_code,
            message=str(exc.detail),
            event="http_exception",
        )
        return build_response(
            status_code=exc.status_code,
            error_code=error_code,
            message=str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
        """Catch-all handler for unexpected errors."""
        log_error(
            request=request,
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            event="unhandled_exception",
            level="ERROR",
            exception=True,
        )
        return build_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
        )
