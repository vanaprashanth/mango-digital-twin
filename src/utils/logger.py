"""
Simple, reusable logging utility for the Sensor-Free Mango Digital Twin.

Why this exists: scattered `print()` statements are hard to filter, hard to
time-stamp, and disappear once the terminal scrolls past them. This module
gives every script a one-line way to get a logger that:

  - prints readable, time-stamped messages to the console, and
  - also appends them to logs/pipeline.log, so you can scroll back through
    previous runs later (useful when a scheduled/cron run fails overnight).

Usage (put this near the top of any script):

    from src.utils.logger import get_logger
    log = get_logger(__name__)

    log.info("Starting step...")
    log.warning("Something looks off, but continuing")
    log.error("Step failed: %s", error)
"""

from __future__ import annotations

import logging
from pathlib import Path

# Project root = two levels up from this file (src/utils/logger.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logging() -> None:
    """
    Set up console + file handlers exactly once per process, no matter how
    many modules call get_logger(). Safe to call repeatedly.
    """
    global _configured
    if _configured:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for `name` (pass `__name__` from the calling
    module so log lines show which file they came from).
    """
    _configure_root_logging()
    return logging.getLogger(name)
