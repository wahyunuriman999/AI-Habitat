"""Structured JSON logging.

Every log entry is a single JSON line containing at least:
    timestamp, level, logger, message

Request-scoped fields (request_id, method, path, status, duration_ms)
are added automatically by the RequestIdMiddleware when available.

Security: API keys, credentials, and stack traces are never logged.
"""

import json
import logging
import sys
from datetime import datetime, timezone

_EXTRA_FIELDS = (
    "request_id",
    "method",
    "path",
    "status",
    "duration_ms",
)


class StructuredFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _EXTRA_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                entry[key] = value
        return json.dumps(entry, default=str)


def setup_logging() -> logging.Logger:
    """Initialise the application logger with structured JSON output."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    app_logger = logging.getLogger("ai_habitat")
    app_logger.setLevel(logging.INFO)
    if not app_logger.handlers:
        app_logger.addHandler(handler)
    app_logger.propagate = False

    return app_logger
