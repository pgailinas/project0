# ============================================================
# Project0 - Workflow Engine
#
# File: workflow_engine.py
#
# Purpose:
#     Coordinate sequential task execution between Project0
#     platform components and AI agents.
#
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from project0.interfaces.workflow_interfaces import (
    WorkflowEventPublisherInterface,
)
from project0.models.workflow_models import (
    TaskExecutionResult,
    TaskStatus,
    WorkflowExecutionResult,
    WorkflowStatus,
    WorkflowTask,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkflowEngine:
    """Execute Project0 workflow tasks sequentially.

    The initial implementation uses synchronous, in-process execution.
    Task execution stops at the first failure.
    """

    event_publisher: WorkflowEventPublisherInterface | None = None

    def execute(
        self,
        workflow_name: str,
        tasks: Sequence[WorkflowTask],
        workflow_id: str | None = None,
    ) -> WorkflowExecutionResult:
        """Execute a workflow and return a structured result."""

        if not workflow_name.strip():
            raise ValueError("Workflow name cannot be empty.")

        if not tasks:
            raise ValueError("Workflow must contain at least one task.")

        resolved_workflow_id = workflow_id or str(uuid4())
        workflow_started_at = self._utc_now()
        task_results: list[TaskExecutionResult] = []

        LOGGER.info(
            "Starting workflow '%s' with id %s.",
            workflow_name,
            resolved_workflow_id,
        )
        self._publish("WorkflowStarted", resolved_workflow_id)

        for task in tasks:
            task_result = self._execute_task(
                workflow_id=resolved_workflow_id,
                task=task,
            )
            task_results.append(task_result)

            if task_result.status == TaskStatus.FAILED:
                workflow_completed_at = self._utc_now()
                error_message = (
                    f"Task '{task.name}' failed: "
                    f"{task_result.error_message}"
                )

                LOGGER.error(
                    "Workflow '%s' failed: %s",
                    workflow_name,
                    error_message,
                )
                self._publish("WorkflowFailed", resolved_workflow_id)

                return WorkflowExecutionResult(
                    workflow_id=resolved_workflow_id,
                    workflow_name=workflow_name,
                    status=WorkflowStatus.FAILED,
                    started_at=workflow_started_at,
                    completed_at=workflow_completed_at,
                    task_results=tuple(task_results),
                    error_message=error_message,
                )

        workflow_completed_at = self._utc_now()

        LOGGER.info(
            "Workflow '%s' completed successfully.",
            workflow_name,
        )
        self._publish("WorkflowCompleted", resolved_workflow_id)

        return WorkflowExecutionResult(
            workflow_id=resolved_workflow_id,
            workflow_name=workflow_name,
            status=WorkflowStatus.COMPLETED,
            started_at=workflow_started_at,
            completed_at=workflow_completed_at,
            task_results=tuple(task_results),
        )

    def _execute_task(
        self,
        workflow_id: str,
        task: WorkflowTask,
    ) -> TaskExecutionResult:
        """Execute one workflow task and capture its result."""

        started_at = self._utc_now()

        LOGGER.info(
            "Starting task '%s' with id %s.",
            task.name,
            task.task_id,
        )
        self._publish("TaskStarted", workflow_id, task.task_id)

        try:
            output = task.action()
        except Exception as exc:
            completed_at = self._utc_now()

            LOGGER.exception(
                "Task '%s' failed.",
                task.name,
            )
            self._publish("TaskFailed", workflow_id, task.task_id)

            return TaskExecutionResult(
                task_id=task.task_id,
                task_name=task.name,
                status=TaskStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                error_message=str(exc),
            )

        completed_at = self._utc_now()

        LOGGER.info(
            "Task '%s' completed successfully.",
            task.name,
        )
        self._publish("TaskCompleted", workflow_id, task.task_id)

        return TaskExecutionResult(
            task_id=task.task_id,
            task_name=task.name,
            status=TaskStatus.COMPLETED,
            started_at=started_at,
            completed_at=completed_at,
            output=output,
        )

    def _publish(
        self,
        event_name: str,
        workflow_id: str,
        task_id: str | None = None,
    ) -> None:
        """Publish an event when an event publisher is configured."""

        if self.event_publisher is None:
            return

        self.event_publisher.publish(
            event_name=event_name,
            workflow_id=workflow_id,
            task_id=task_id,
        )

    @staticmethod
    def _utc_now() -> datetime:
        """Return the current timezone-aware UTC timestamp."""

        return datetime.now(timezone.utc)


def create_workflow_engine(
    event_publisher: WorkflowEventPublisherInterface | None = None,
) -> WorkflowEngine:
    """Create a WorkflowEngine instance."""

    return WorkflowEngine(event_publisher=event_publisher)
