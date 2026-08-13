# ============================================================
# Project0 - Project0 Platform Logging
#
# File: logging_config.py
#
# Purpose:
#     Configure application-wide logging for Project0.
#
# ============================================================

import logging

from project0.config.settings import SETTINGS


def configure_logging() -> None:
    """
    Configure application-wide console logging.

    Logging is configured once by the application entry point.
    Individual modules should obtain loggers with
    logging.getLogger(__name__).
    """

    logging.basicConfig(
        level=getattr(logging, SETTINGS.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
