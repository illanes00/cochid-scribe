"""Structured logging configuration using structlog.

This module provides a configured structlog logger that outputs JSON in production
and human-readable format in development. All logging should use get_logger()
instead of print() or the standard logging module.

Usage:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("user.login", user_id="123", ip="192.168.1.1")
    logger.error("payment.failed", order_id="456", error="Insufficient funds")
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.config import get_settings


def _add_app_context(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add application context to log entries."""
    settings = get_settings()
    event_dict["service"] = settings.app_name
    event_dict["environment"] = settings.environment
    return event_dict


def configure_logging() -> None:
    """Configure structlog for the application.

    In production (ENVIRONMENT=production): JSON output for log aggregation
    In development: Human-readable colored console output
    """
    settings = get_settings()
    is_production = settings.environment == "production"

    # Shared processors that run regardless of environment
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _add_app_context,
    ]

    if is_production:
        # Production: JSON format for log aggregation (ELK, Datadog, etc.)
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured structlog logger.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        A bound structlog logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("document.created", slug="my-doc", doc_type="paper")
    """
    return structlog.get_logger(name)


# Module-level logger for this module
logger = get_logger(__name__)
