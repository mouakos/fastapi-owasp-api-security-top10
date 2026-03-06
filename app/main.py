"""Main application file for the FastAPI app."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.errors.exception_handlers import register_exception_handlers
from app.logging import setup_logging
from app.middleware import request_logging_middleware, security_headers_middleware

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
    # Perform any additional startup tasks here (e.g. warmup, preloading) if needed
    yield
    await logger.complete()  # Ensure all logs are flushed on shutdown


app = FastAPI(
    title="FastAPI OWASP API Security Top 10",
    description="An example FastAPI application demonstrating OWASP API Security Top 10 best practices.",
    version=settings.version,
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
# API8: Security headers on every response
# ---------------------------------------------------------------------------
app.middleware("http")(security_headers_middleware)

# ---------------------------------------------------------------------------
# API8: Request logging middleware to log all incoming requests and responses.
# ---------------------------------------------------------------------------
app.middleware("http")(request_logging_middleware)

# ---------------------------------------------------------------------------
# API8: Strict CORS — only listed origins may call credentialed endpoints.
#       Avoid allow_origins=["*"] in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# --------------------------------------------------------------------------
# API8: Global exception handlers to prevent information leakage and
#       ensure consistent error responses.
# ---------------------------------------------------------------------------
register_exception_handlers(app)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Hello World"}
