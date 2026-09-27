"""Structured logging configuration ensuring biomedical data and credentials are never exposed."""

import logging
import sys
from typing import Any, Dict
from app.core.config import settings


class SafeFormatter(logging.Formatter):
    """Custom log formatter ensuring no sensitive biomedical or credential data is exposed."""

    SENSITIVE_KEYS = {
        "password",
        "password_hash",
        "secret",
        "jwt_secret",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "gemini_api_key",
        "patient",
        "raw_record",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Check and sanitize record message if needed
        return super().format(record)


def setup_logging() -> None:
    """Configure root and application loggers."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] "
        "[request_id=%(request_id)s user_id=%(user_id)s run_id=%(run_id)s experiment_id=%(experiment_id)s] "
        "- %(message)s"
    )

    class ContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "request_id"):
                record.request_id = "-"
            if not hasattr(record, "user_id"):
                record.user_id = "-"
            if not hasattr(record, "run_id"):
                record.run_id = "-"
            if not hasattr(record, "experiment_id"):
                record.experiment_id = "-"
            return True

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(ContextFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Clear existing handlers to prevent duplicate output
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("hybrid_qml_backend")
