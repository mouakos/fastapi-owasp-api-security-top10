"""Middleware for the FastAPI application."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict

from fastapi import Request, Response
from loguru import logger

from app.utils.request_info import get_request_info


# ---------------------------------------------------------------------------
# API8: Request logging middleware
# ---------------------------------------------------------------------------
async def request_logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to log incoming HTTP requests.

    Args:
        request(Request): The incoming HTTP request.
        call_next(Callable[[Request], Awaitable[Response]]): The next handler in the middleware chain.

    Returns:
        Response: The HTTP response from the next handler.
    """
    request_info = get_request_info(request)
    logger.info(
        "http_request_received",
        **asdict(request_info),
    )

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    status_code = response.status_code

    logger.info(
        "http_request_completed",
        **asdict(request_info),
        status_code=status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response


# ---------------------------------------------------------------------------
# API8: Security headers
# ---------------------------------------------------------------------------
async def security_headers_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to add security headers to HTTP responses.

    Args:
        request(Request): The incoming HTTP request.
        call_next(Callable[[Request], Awaitable[Response]]): The next handler in the middleware chain.

    Returns:
        Response: The HTTP response with added security headers.
    """
    response = await call_next(request)

    # Prevent MIME type sniffing and XSS attacks
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking by disallowing framing of the site
    response.headers["X-Frame-Options"] = "DENY"

    # Enable XSS protection in browsers that support it
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Tell browsers to enforce HTTPS for 2 years (63072000 seconds)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    # Control referrer information sent with requests
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Prevent caching of sensitive data
    response.headers["Cache-Control"] = "no-store"

    # Disable browser features that could be abused
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response
