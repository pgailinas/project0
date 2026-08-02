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

from project0.common.logging_config import configure_logging
from project0.config.paths import PROJECT_ROOT
from project0.config.settings import SETTINGS


logger = logging.getLogger(__name__)


def main() -> None:
    """Run the Project0 Documentation Agent."""

    configure_logging()

    logger.info(
        "%s %s starting.",
        SETTINGS.project_name,
        SETTINGS.application_name,
    )

    logger.info("Project root: %s", PROJECT_ROOT)


if __name__ == "__main__":
    main()
    
