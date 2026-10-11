"""Structured JSON logging for production observability."""
from __future__ import annotations

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.utils.config import get_settings


class _JsonFormatter(jsonlogger.JsonFormatter):
    """Adds standard fields to every log record."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["app"] = "oceanguard-ai"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if "timestamp" not in log_record:
            log_record["timestamp"] = self.formatTime(record, self.datefmt)


def configure_logging() -> None:
    """Configure root logger with JSON output for prod, plain text for dev."""
    settings = get_settings()
    root = logging.getLogger()
    # Avoid double-config when reloaded
    if getattr(root, "_oceanguard_configured", False):
        return
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    if settings.app_env == "production":
        handler.setFormatter(_JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root._oceanguard_configured = True


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Convenience helper for emitting structured events."""
    extra = {"event": event, **fields}
    logger.log(level, event, extra=extra)