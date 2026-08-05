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
from project0.common.startup_validation import StartupValidationError
from project0.models.context_models import ContextWorkflowType
from project0.models.workflow_models import WorkflowStatus
from project0.platform.platform_dispatcher import (
    create_platform_dispatcher,
)


LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Initialize Project0 and execute the startup platform workflow.

    The Platform Dispatcher now supports both:

    * Startup context workflows
    * Documentation workflows (when configured)

    Startup continues to execute only the context workflow. Future
    command-line options will select additional workflows.
    """

    configure_logging()

    LOGGER.info("Starting Project0.")

    try:
        dispatcher = create_platform_dispatcher()

        #
        # Phase 6:
        # Execute the startup context workflow.
        #
        workflow_result = dispatcher.run_context_workflow(
            context_id="project0-startup-context",
            workflow_type=(
                ContextWorkflowType.GENERAL_DOCUMENTATION
            ),
            workflow_name="Project0 Startup Context",
        )

        #
        # Future:
        #
        # dispatcher.run_documentation_workflow(...)
        #
        # Command-line arguments (or another entry point) will
        # determine which platform workflow is executed.
        #

    except StartupValidationError as exc:
        LOGGER.error("Project0 startup validation failed: %s", exc)
        return 1
    except Exception:
        LOGGER.exception("Unexpected error during Project0 startup.")
        return 1

    if workflow_result.status != WorkflowStatus.COMPLETED:
        LOGGER.error(
            "Project0 startup workflow failed: %s",
            workflow_result.error_message,
        )
        return 1

    LOGGER.info(
        "Project0 initialized successfully with %d context documents.",
        workflow_result.task_results[0].output.source_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
