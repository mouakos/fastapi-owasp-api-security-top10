"""Middleware for the FastAPI application."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict

from fastapi import Request, Response
from loguru import logger

from app.utils.request_info import get_request_info


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
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    status_code = response.status_code
    request_info = get_request_info(request)
    logger.info(
        "http_request_completed",
        **asdict(request_info),
        status_code=status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response
