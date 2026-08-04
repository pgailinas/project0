# ============================================================
# Project0 - Platform Dispatcher
#
# File: platform_dispatcher.py
#
# Purpose:
#     Assemble Project0 platform services and coordinate
#     platform-level workflow execution.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from project0.common.startup_validation import validate_startup
from project0.config.settings import SETTINGS
from project0.interfaces.context_builder_interfaces import (
    ContextBuilderInterface,
)
from project0.interfaces.repository_interfaces import RepositoryInterface
from project0.interfaces.workflow_interfaces import WorkflowInterface
from project0.knowledge.context_builder import ContextBuilder
from project0.models.context_models import ContextWorkflowType
from project0.models.workflow_models import (
    WorkflowExecutionResult,
    WorkflowTask,
)
from project0.repository.repository_service import RepositoryService
from project0.workflow.workflow_engine import WorkflowEngine


@dataclass(slots=True)
class PlatformDispatcher:
    """Coordinate Project0 platform services.

    The initial implementation supports read-only context workflows.
    Agent reasoning, repository modification, validation, review, and
    asynchronous execution are intentionally deferred.
    """

    repository: RepositoryInterface
    context_builder: ContextBuilderInterface
    workflow_engine: WorkflowInterface

    def run_context_workflow(
        self,
        context_id: str,
        workflow_type: ContextWorkflowType,
        workflow_name: str = "Build Project0 Context",
        workflow_id: str | None = None,
    ) -> WorkflowExecutionResult:
        """Build workflow-specific context through the Workflow Engine."""

        if not context_id.strip():
            raise ValueError("Context identifier cannot be empty.")

        if not workflow_name.strip():
            raise ValueError("Workflow name cannot be empty.")

        resolved_workflow_id = workflow_id or str(uuid4())

        context_task = WorkflowTask(
            name="Build Documentation Context",
            action=lambda: self.context_builder.build_documentation_context(
                context_id=context_id,
                workflow_type=workflow_type,
            ),
        )

        return self.workflow_engine.execute(
            workflow_name=workflow_name,
            tasks=[context_task],
            workflow_id=resolved_workflow_id,
        )


def create_platform_dispatcher() -> PlatformDispatcher:
    """Validate startup and assemble the default Project0 platform."""

    validate_startup(SETTINGS)

    repository = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    context_builder = ContextBuilder(
        repository_service=repository
    )
    workflow_engine = WorkflowEngine()

    return PlatformDispatcher(
        repository=repository,
        context_builder=context_builder,
        workflow_engine=workflow_engine,
    )
