"""Main application file for the FastAPI app."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from loguru import logger
from slowapi.middleware import SlowAPIMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import request_logging_middleware, security_headers_middleware
from app.api.rate_limiter import limiter
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import register_log_patcher, setup_logging

# ---------------------------------------------------------------------------
# Structured logging setup with Loguru.
# API8: Structured, correlation-ID-enriched logging enables security monitoring
#       and incident traceability across every request.
# ---------------------------------------------------------------------------
setup_logging(["uvicorn.access"])

# ---------------------------------------------------------------------------
# Application instance
# API8: Disable /docs, /redoc, and /openapi.json in production so the API
#       surface is not publicly discoverable.
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager to perform startup and shutdown tasks."""
    # Perform any async startup tasks here (e.g., database connections, background tasks)
    yield
    # Perform any async shutdown tasks here (e.g., closing database connections, flushing logs)
    await logger.complete()  # Ensure all logs are flushed on shutdown


def custom_generate_unique_id(route: APIRoute) -> str:
    """Custom function to generate unique operation IDs for OpenAPI schema."""
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}_{route.name}"


app = FastAPI(
    title="FastAPI OWASP API Security Top 10",
    description="An example FastAPI application demonstrating OWASP API Security Top 10 best practices.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else f"{settings.api_v1_str}/docs",
    redoc_url=None if settings.environment == "production" else f"{settings.api_v1_str}/redoc",
    openapi_url=None
    if settings.environment == "production"
    else f"{settings.api_v1_str}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit/",
    },
    contact={
        "name": "Stephane Mouako",
        "url": "https://github.com/mouakos",
    },
)
# ---------------------------------------------------------------------------
# Middleware registration — Starlette executes in REVERSE order, so the last
# middleware registered here is the outermost (runs first on every request).
#
# Actual execution order (outermost → innermost):
#   CORSMiddleware → CorrelationIdMiddleware → SlowAPIMiddleware
#   → request_logging_middleware → security_headers_middleware
# ---------------------------------------------------------------------------

# 5 (innermost): API8: Security headers — added to every response including 429s
app.middleware("http")(security_headers_middleware)

# 4: API8: Request logging — logs every non-rejected request with its correlation ID
app.middleware("http")(request_logging_middleware)

# 3: API4: Rate limiting — rejects early to cap throughput and protect server resources
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# 2: API8: Correlation ID — assigns X-Request-ID before rate limiting so even
#    rejected requests carry a traceable ID
app.add_middleware(CorrelationIdMiddleware)


def _inject_request_id(record: dict[str, Any]) -> None:
    """Loguru patcher to inject the correlation ID from the request context into log records."""
    request_id = correlation_id.get()
    if request_id:
        record["extra"]["request_id"] = request_id


register_log_patcher(_inject_request_id)


# ---------------------------------------------------------------------------
# API8: Strict CORS — only listed origins may call credentialed endpoints.
#       Avoid allow_origins=["*"] in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    ],
)

# ---------------------------------------------------------------------------
# API8: Global exception handlers to prevent information leakage and
#       ensure consistent error responses.
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# API9: Single versioned router mounted at /api/v1 — no shadow or legacy
#       endpoints exist; the API surface is fully inventoried and controlled.
# ---------------------------------------------------------------------------
app.include_router(api_v1_router, prefix=settings.api_v1_str)
