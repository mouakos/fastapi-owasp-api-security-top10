"""Logging configuration and setup for the FastAPI application."""

import logging
import sys

from loguru import logger

from app.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Format for logs using UTC timestamps
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss!UTC}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level> - "
    "<yellow>{extra}</yellow>"
)

# ---------------------------------------------------------------------------
# Standard-library logging bridge
# ---------------------------------------------------------------------------


class InterceptHandler(logging.Handler):
    """Stdlib logging handler that redirects all records into Loguru.

    Installed as the sole handler on the root logger so that libraries using
    the standard logging module (uvicorn, SQLAlchemy, httpx, …) are captured
    by Loguru's pipeline and formatted/exported consistently with application logs.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Forward a stdlib LogRecord to the equivalent Loguru level.

        Args:
            record: The stdlib log record to forward.
        """
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# ---------------------------------------------------------------------------
# Private setup helpers
# ---------------------------------------------------------------------------


def _setup_sinks(log_level: str, log_to_file: bool, log_serialized: bool) -> None:
    """Configure Loguru sinks for console and file logging.

    Args:
        log_level: Minimum log level string (e.g. "INFO", "DEBUG").
        log_to_file: Whether to log to a file.
        log_serialized: Whether to serialize logs in JSON format.
    """
    logger.add(
        sys.stdout,
        level=log_level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=LOG_FORMAT,
        serialize=log_serialized,
    )

    if log_to_file:
        logger.add(
            "logs/app.log",
            level=log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            format=LOG_FORMAT,
            serialize=log_serialized,
        )


def _disable_loggers(names: list[str]) -> None:
    """Fully disable a list of stdlib loggers.

    Args:
        names: Logger names to disable.
    """
    for name in names:
        log = logging.getLogger(name)
        log.handlers = []
        log.propagate = False
        log.disabled = True


def _intercept_standard_logging(log_level: str) -> None:
    """Route stdlib logging into Loguru.

    Replaces all root logger handlers with a single InterceptHandler so every
    stdlib log record is forwarded to Loguru.

    Args:
        log_level: Minimum log level string applied to the root logger.
    """
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level)

    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def setup_logging(silenced_loggers: list[str] | None = None) -> None:
    """Configure Loguru and route stdlib logging into it.

    Args:
        silenced_loggers: Optional list of stdlib logger names to disable entirely. Defaults to None (no loggers silenced).
    """
    logger.remove()

    logger.configure(extra={"version": settings.version, "environment": settings.environment})

    _setup_sinks(settings.log_level, settings.log_to_file, settings.log_serialized)
    _intercept_standard_logging(settings.log_level)
    if silenced_loggers:
        _disable_loggers(silenced_loggers)
