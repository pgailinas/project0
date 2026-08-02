# ============================================================
# Project0 - Documentation Agent
#
# File: main.py
#
# Purpose:
#     Provide the application entry point.
#
# ============================================================

import logging
import sys

from project0.common.logging_config import configure_logging
from project0.common.startup_validation import (
    StartupValidationError,
    validate_startup,
)
from project0.config.settings import load_settings

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Initialize and validate the Project0 application."""

    configure_logging()

    LOGGER.info("Starting Project0.")

    try:
        settings = load_settings()
        validate_startup(settings)
    except StartupValidationError as exc:
        LOGGER.error("Project0 startup validation failed: %s", exc)
        return 1
    except Exception:
        LOGGER.exception("Unexpected error during Project0 startup.")
        return 1

    LOGGER.info("Project0 initialized successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
    
