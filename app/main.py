"""Main application file for the FastAPI app."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.config import settings
from app.logging import setup_logging

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
setup_logging(["uvicorn.access"])

# ---------------------------------------------------------------------------
# Application instance
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
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit/",
    },
    contact={
        "name": "Stephane Mouako",
        "url": "https://github.com/mouakos",
    },
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Hello World"}
