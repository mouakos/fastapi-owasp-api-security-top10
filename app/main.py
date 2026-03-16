"""Main application file for the FastAPI app."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi.middleware import SlowAPIMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import request_logging_middleware, security_headers_middleware
from app.api.rate_limiter import limiter
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import register_log_patcher, setup_logging
from app.persistence.database import init_db

# ---------------------------------------------------------------------------
# Structured logging setup with Loguru.
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
    await init_db()
    yield
    await logger.complete()  # Ensure all logs are flushed on shutdown


app = FastAPI(
    title="FastAPI OWASP API Security Top 10",
    description="An example FastAPI application demonstrating OWASP API Security Top 10 best practices.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
    openapi_url=None if settings.environment == "production" else "/openapi.json",
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
# API4: Attach rate limiter middleware to enforce rate limits on endpoints.
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# API8: Security headers on every response
# ---------------------------------------------------------------------------
app.middleware("http")(security_headers_middleware)

# ---------------------------------------------------------------------------
# API8: Request logging middleware to log all incoming requests and responses.
# ---------------------------------------------------------------------------
app.middleware("http")(request_logging_middleware)

# ---------------------------------------------------------------------------
# API8: Correlation ID middleware to trace requests across logs and services.
# ---------------------------------------------------------------------------
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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to the FastAPI OWASP API Security Top 10 example application! Visit /docs for API documentation."
    }


# ---------------------------------------------------------------------------
# API v1 router
# ---------------------------------------------------------------------------
app.include_router(api_v1_router, prefix=settings.api_prefix)
