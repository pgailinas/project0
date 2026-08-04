# ============================================================
# Project0 - Workflow Models
#
# File: test_workflow_models.py
#
# Purpose:
#     Verify shared workflow model values, identifiers,
#     defaults, field preservation, and immutability.
#
# ============================================================

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from project0.models.workflow_models import (
    TaskExecutionResult,
    TaskStatus,
    WorkflowExecutionResult,
    WorkflowStatus,
    WorkflowTask,
)


STARTED_AT = datetime(2026, 8, 4, 17, 0, tzinfo=timezone.utc)
COMPLETED_AT = datetime(2026, 8, 4, 17, 1, tzinfo=timezone.utc)


def test_workflow_status_values() -> None:
    assert WorkflowStatus.PENDING == "pending"
    assert WorkflowStatus.RUNNING == "running"
    assert WorkflowStatus.COMPLETED == "completed"
    assert WorkflowStatus.FAILED == "failed"


def test_task_status_values() -> None:
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.RUNNING == "running"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"


def test_workflow_task_stores_supplied_values() -> None:
    action = lambda: "complete"

    task = WorkflowTask(
        name="Read Repository",
        action=action,
        task_id="task-1",
    )

    assert task.name == "Read Repository"
    assert task.action is action
    assert task.task_id == "task-1"


def test_workflow_task_generates_nonempty_id() -> None:
    task = WorkflowTask(
        name="Generated ID",
        action=lambda: None,
    )

    assert task.task_id
    assert isinstance(task.task_id, str)


def test_workflow_tasks_generate_unique_ids() -> None:
    first = WorkflowTask(
        name="First",
        action=lambda: None,
    )
    second = WorkflowTask(
        name="Second",
        action=lambda: None,
    )

    assert first.task_id != second.task_id


def test_workflow_task_action_is_callable() -> None:
    task = WorkflowTask(
        name="Return Value",
        action=lambda: 42,
    )

    assert task.action() == 42


def test_workflow_task_is_immutable() -> None:
    task = WorkflowTask(
        name="Immutable Task",
        action=lambda: None,
    )

    with pytest.raises(FrozenInstanceError):
        task.name = "Changed"  # type: ignore[misc]


def test_completed_task_result_preserves_output() -> None:
    result = TaskExecutionResult(
        task_id="task-2",
        task_name="Build Context",
        status=TaskStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        output={"documents": 8},
    )

    assert result.task_id == "task-2"
    assert result.task_name == "Build Context"
    assert result.status == TaskStatus.COMPLETED
    assert result.started_at == STARTED_AT
    assert result.completed_at == COMPLETED_AT
    assert result.output == {"documents": 8}
    assert result.error_message is None


def test_failed_task_result_preserves_error() -> None:
    result = TaskExecutionResult(
        task_id="task-3",
        task_name="Read Missing File",
        status=TaskStatus.FAILED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        error_message="Repository file was not found.",
    )

    assert result.status == TaskStatus.FAILED
    assert result.output is None
    assert result.error_message == (
        "Repository file was not found."
    )


def test_task_result_uses_empty_optional_defaults() -> None:
    result = TaskExecutionResult(
        task_id="task-4",
        task_name="Pending Result",
        status=TaskStatus.PENDING,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
    )

    assert result.output is None
    assert result.error_message is None


def test_task_result_is_immutable() -> None:
    result = TaskExecutionResult(
        task_id="task-5",
        task_name="Immutable Result",
        status=TaskStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        result.status = TaskStatus.FAILED  # type: ignore[misc]


def test_completed_workflow_result_preserves_task_results() -> None:
    task_result = TaskExecutionResult(
        task_id="task-6",
        task_name="Task",
        status=TaskStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        output="done",
    )

    result = WorkflowExecutionResult(
        workflow_id="workflow-1",
        workflow_name="Documentation Workflow",
        status=WorkflowStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        task_results=(task_result,),
    )

    assert result.workflow_id == "workflow-1"
    assert result.workflow_name == "Documentation Workflow"
    assert result.status == WorkflowStatus.COMPLETED
    assert result.started_at == STARTED_AT
    assert result.completed_at == COMPLETED_AT
    assert result.task_results == (task_result,)
    assert result.error_message is None


def test_failed_workflow_result_preserves_error() -> None:
    task_result = TaskExecutionResult(
        task_id="task-7",
        task_name="Failure",
        status=TaskStatus.FAILED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        error_message="Task failed.",
    )

    result = WorkflowExecutionResult(
        workflow_id="workflow-2",
        workflow_name="Failure Workflow",
        status=WorkflowStatus.FAILED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        task_results=(task_result,),
        error_message="Task 'Failure' failed: Task failed.",
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.error_message == (
        "Task 'Failure' failed: Task failed."
    )
    assert result.task_results == (task_result,)


def test_workflow_result_supports_empty_task_results() -> None:
    result = WorkflowExecutionResult(
        workflow_id="workflow-3",
        workflow_name="Pending Workflow",
        status=WorkflowStatus.PENDING,
        started_at=STARTED_AT,
        completed_at=STARTED_AT,
        task_results=(),
    )

    assert result.task_results == ()
    assert result.error_message is None


def test_workflow_result_is_immutable() -> None:
    result = WorkflowExecutionResult(
        workflow_id="workflow-4",
        workflow_name="Immutable Workflow",
        status=WorkflowStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        task_results=(),
    )

    with pytest.raises(FrozenInstanceError):
        result.status = WorkflowStatus.FAILED  # type: ignore[misc]


def test_model_timestamps_preserve_timezone_information() -> None:
    task_result = TaskExecutionResult(
        task_id="task-8",
        task_name="Timestamp Task",
        status=TaskStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
    )
    workflow_result = WorkflowExecutionResult(
        workflow_id="workflow-5",
        workflow_name="Timestamp Workflow",
        status=WorkflowStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        task_results=(task_result,),
    )

    assert task_result.started_at.tzinfo == timezone.utc
    assert task_result.completed_at.tzinfo == timezone.utc
    assert workflow_result.started_at.tzinfo == timezone.utc
    assert workflow_result.completed_at.tzinfo == timezone.utc
