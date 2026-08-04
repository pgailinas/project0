# ============================================================
# Project0 - Workflow Engine
#
# File: test_workflow_engine.py
#
# Purpose:
#     Verify sequential workflow execution, task results,
#     failure handling, identifiers, timestamps, and events.
#
# ============================================================

from __future__ import annotations

from datetime import timezone
from unittest.mock import Mock, call

import pytest

from project0.workflow.workflow_engine import (
    TaskStatus,
    WorkflowEngine,
    WorkflowStatus,
    WorkflowTask,
    create_workflow_engine,
)


def test_create_workflow_engine_returns_engine() -> None:
    engine = create_workflow_engine()

    assert isinstance(engine, WorkflowEngine)
    assert engine.event_publisher is None


def test_execute_rejects_empty_workflow_name() -> None:
    engine = WorkflowEngine()
    task = WorkflowTask(name="Task", action=lambda: None)

    with pytest.raises(ValueError, match="name cannot be empty"):
        engine.execute("   ", [task])


def test_execute_rejects_empty_task_list() -> None:
    engine = WorkflowEngine()

    with pytest.raises(ValueError, match="at least one task"):
        engine.execute("Empty Workflow", [])


def test_execute_completes_single_task() -> None:
    engine = WorkflowEngine()
    task = WorkflowTask(
        name="Read Repository",
        action=lambda: "complete",
    )

    result = engine.execute("Repository Workflow", [task])

    assert result.status == WorkflowStatus.COMPLETED
    assert result.workflow_name == "Repository Workflow"
    assert result.error_message is None
    assert len(result.task_results) == 1

    task_result = result.task_results[0]

    assert task_result.task_id == task.task_id
    assert task_result.task_name == task.name
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.output == "complete"
    assert task_result.error_message is None


def test_execute_runs_tasks_in_supplied_order() -> None:
    engine = WorkflowEngine()
    execution_order: list[str] = []

    tasks = [
        WorkflowTask(
            name="First",
            action=lambda: execution_order.append("first"),
        ),
        WorkflowTask(
            name="Second",
            action=lambda: execution_order.append("second"),
        ),
        WorkflowTask(
            name="Third",
            action=lambda: execution_order.append("third"),
        ),
    ]

    result = engine.execute("Ordered Workflow", tasks)

    assert result.status == WorkflowStatus.COMPLETED
    assert execution_order == ["first", "second", "third"]
    assert [
        task_result.task_name
        for task_result in result.task_results
    ] == ["First", "Second", "Third"]


def test_execute_captures_task_outputs() -> None:
    engine = WorkflowEngine()

    tasks = [
        WorkflowTask(name="Count", action=lambda: 3),
        WorkflowTask(
            name="Metadata",
            action=lambda: {"files": 12},
        ),
    ]

    result = engine.execute("Output Workflow", tasks)

    assert [
        task_result.output
        for task_result in result.task_results
    ] == [3, {"files": 12}]


def test_execute_uses_supplied_workflow_id() -> None:
    engine = WorkflowEngine()
    task = WorkflowTask(name="Task", action=lambda: None)

    result = engine.execute(
        workflow_name="Named Workflow",
        tasks=[task],
        workflow_id="workflow-123",
    )

    assert result.workflow_id == "workflow-123"


def test_execute_generates_workflow_and_task_ids() -> None:
    engine = WorkflowEngine()
    first = WorkflowTask(name="First", action=lambda: None)
    second = WorkflowTask(name="Second", action=lambda: None)

    result = engine.execute("Generated IDs", [first, second])

    assert result.workflow_id
    assert first.task_id
    assert second.task_id
    assert first.task_id != second.task_id


def test_execute_returns_timezone_aware_timestamps() -> None:
    engine = WorkflowEngine()
    task = WorkflowTask(name="Task", action=lambda: None)

    result = engine.execute("Timestamp Workflow", [task])

    assert result.started_at.tzinfo == timezone.utc
    assert result.completed_at.tzinfo == timezone.utc
    assert result.completed_at >= result.started_at

    task_result = result.task_results[0]

    assert task_result.started_at.tzinfo == timezone.utc
    assert task_result.completed_at.tzinfo == timezone.utc
    assert task_result.completed_at >= task_result.started_at


def test_execute_converts_task_exception_to_failed_result() -> None:
    engine = WorkflowEngine()

    def fail() -> None:
        raise RuntimeError("Repository unavailable")

    task = WorkflowTask(name="Failing Task", action=fail)

    result = engine.execute("Failure Workflow", [task])

    assert result.status == WorkflowStatus.FAILED
    assert result.error_message is not None
    assert "Repository unavailable" in result.error_message
    assert len(result.task_results) == 1

    task_result = result.task_results[0]

    assert task_result.status == TaskStatus.FAILED
    assert task_result.output is None
    assert task_result.error_message == "Repository unavailable"


def test_execute_stops_after_first_failure() -> None:
    engine = WorkflowEngine()
    later_action = Mock()

    def fail() -> None:
        raise ValueError("Task failed")

    tasks = [
        WorkflowTask(name="Successful", action=lambda: "done"),
        WorkflowTask(name="Failure", action=fail),
        WorkflowTask(name="Not Run", action=later_action),
    ]

    result = engine.execute("Stop Workflow", tasks)

    assert result.status == WorkflowStatus.FAILED
    assert len(result.task_results) == 2
    assert [
        item.status for item in result.task_results
    ] == [TaskStatus.COMPLETED, TaskStatus.FAILED]
    later_action.assert_not_called()


def test_execute_publishes_success_events() -> None:
    publisher = Mock()
    engine = WorkflowEngine(event_publisher=publisher)
    task = WorkflowTask(
        name="Task",
        action=lambda: "result",
        task_id="task-1",
    )

    result = engine.execute(
        workflow_name="Event Workflow",
        tasks=[task],
        workflow_id="workflow-1",
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert publisher.publish.call_args_list == [
        call(
            event_name="WorkflowStarted",
            workflow_id="workflow-1",
            task_id=None,
        ),
        call(
            event_name="TaskStarted",
            workflow_id="workflow-1",
            task_id="task-1",
        ),
        call(
            event_name="TaskCompleted",
            workflow_id="workflow-1",
            task_id="task-1",
        ),
        call(
            event_name="WorkflowCompleted",
            workflow_id="workflow-1",
            task_id=None,
        ),
    ]


def test_execute_publishes_failure_events() -> None:
    publisher = Mock()
    engine = WorkflowEngine(event_publisher=publisher)

    def fail() -> None:
        raise RuntimeError("failure")

    task = WorkflowTask(
        name="Task",
        action=fail,
        task_id="task-2",
    )

    result = engine.execute(
        workflow_name="Failure Events",
        tasks=[task],
        workflow_id="workflow-2",
    )

    assert result.status == WorkflowStatus.FAILED
    assert publisher.publish.call_args_list == [
        call(
            event_name="WorkflowStarted",
            workflow_id="workflow-2",
            task_id=None,
        ),
        call(
            event_name="TaskStarted",
            workflow_id="workflow-2",
            task_id="task-2",
        ),
        call(
            event_name="TaskFailed",
            workflow_id="workflow-2",
            task_id="task-2",
        ),
        call(
            event_name="WorkflowFailed",
            workflow_id="workflow-2",
            task_id=None,
        ),
    ]


def test_execute_without_event_publisher_succeeds() -> None:
    engine = WorkflowEngine(event_publisher=None)
    task = WorkflowTask(name="Task", action=lambda: None)

    result = engine.execute("No Events", [task])

    assert result.status == WorkflowStatus.COMPLETED
