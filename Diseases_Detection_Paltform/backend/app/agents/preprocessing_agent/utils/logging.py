"""Logging utilities with structured run tracing."""

import logging
import sys
from typing import Optional


def setup_logger(name: str = "ai_preprocessing_agent", log_level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def log_event(
    logger: logging.Logger,
    run_id: str,
    node: Optional[str] = None,
    tool: Optional[str] = None,
    status: Optional[str] = None,
    message: Optional[str] = None,
    level: int = logging.INFO
) -> None:
    """Logs structured workflow events with standard tags."""
    parts = [f"[RUN] {run_id[:8]}"]
    if node:
        parts.append(f"[NODE] {node}")
    if tool:
        parts.append(f"[TOOL] {tool}")
    if status:
        parts.append(f"[STATUS] {status}")
    if message:
        parts.append(f"- {message}")
    logger.log(level, " ".join(parts))
