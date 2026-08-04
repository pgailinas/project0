# ============================================================
# Project0 - Workflow Interfaces
#
# File: workflow_interfaces.py
#
# Purpose:
#     Define the public workflow execution and event-publishing
#     interfaces used by Project0 platform components.
#
# ============================================================

from __future__ import annotations

from typing import Protocol, Sequence

from project0.models.workflow_models import (
    WorkflowExecutionResult,
    WorkflowTask,
)


class WorkflowInterface(Protocol):
    """Public contract for Project0 workflow execution."""

    def execute(
        self,
        workflow_name: str,
        tasks: Sequence[WorkflowTask],
        workflow_id: str | None = None,
    ) -> WorkflowExecutionResult:
        """Execute a workflow and return its structured result."""


class WorkflowEventPublisherInterface(Protocol):
    """Public contract for publishing workflow and task events."""

    def publish(
        self,
        event_name: str,
        workflow_id: str,
        task_id: str | None = None,
    ) -> None:
        """Publish a workflow or task event."""
