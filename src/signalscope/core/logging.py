"""Structured logging setup for local and managed runtimes."""

from __future__ import annotations

import logging
import sys
from typing import Any

from pythonjsonlogger.json import JsonFormatter

from signalscope.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure concise JSON logs suitable for Cloud Logging ingestion."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
            rename_fields={"levelname": "severity", "asctime": "timestamp"},
        )
    )
    handler.addFilter(RequestContextFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())


class RequestContextFilter(logging.Filter):
    """Adds a stable request identifier field when a caller omits it."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            setattr(record, "request_id", "-")
        return True


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter[logging.Logger]:
    """Create a logger adapter carrying structured contextual fields."""

    return logging.LoggerAdapter(logging.getLogger(name), context)
