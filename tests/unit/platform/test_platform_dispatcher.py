# ============================================================
# Project0 - Platform Dispatcher
#
# File: test_platform_dispatcher.py
#
# Purpose:
#     Verify platform dependency wiring, context workflow
#     construction, validation, identifiers, and results.
#
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from project0.models.context_models import ContextWorkflowType
from project0.models.workflow_models import (
    WorkflowExecutionResult,
    WorkflowStatus,
)
from project0.platform.platform_dispatcher import (
    PlatformDispatcher,
)


STARTED_AT = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)
COMPLETED_AT = datetime(2026, 8, 4, 18, 1, tzinfo=timezone.utc)


def _workflow_result(
    workflow_id: str = "workflow-1",
    workflow_name: str = "Build Project0 Context",
) -> WorkflowExecutionResult:
    """Create a completed workflow result for dispatcher tests."""

    return WorkflowExecutionResult(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        status=WorkflowStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        task_results=(),
    )


def _dispatcher() -> tuple[
    PlatformDispatcher,
    Mock,
    Mock,
    Mock,
]:
    """Create a dispatcher with mocked dependencies."""

    repository = Mock()
    context_builder = Mock()
    workflow_engine = Mock()

    dispatcher = PlatformDispatcher(
        repository=repository,
        context_builder=context_builder,
        workflow_engine=workflow_engine,
    )

    return (
        dispatcher,
        repository,
        context_builder,
        workflow_engine,
    )


def test_platform_dispatcher_stores_dependencies() -> None:
    (
        dispatcher,
        repository,
        context_builder,
        workflow_engine,
    ) = _dispatcher()

    assert dispatcher.repository is repository
    assert dispatcher.context_builder is context_builder
    assert dispatcher.workflow_engine is workflow_engine


def test_run_context_workflow_rejects_empty_context_id() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()

    with pytest.raises(ValueError, match="cannot be empty"):
        dispatcher.run_context_workflow(
            context_id="   ",
            workflow_type=(
                ContextWorkflowType.GENERAL_DOCUMENTATION
            ),
        )

    workflow_engine.execute.assert_not_called()


def test_run_context_workflow_rejects_empty_workflow_name() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()

    with pytest.raises(ValueError, match="Workflow name cannot be empty"):
        dispatcher.run_context_workflow(
            context_id="context-1",
            workflow_type=(
                ContextWorkflowType.GENERAL_DOCUMENTATION
            ),
            workflow_name="   ",
        )

    workflow_engine.execute.assert_not_called()


def test_run_context_workflow_uses_supplied_workflow_id() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    expected = _workflow_result(workflow_id="workflow-custom")
    workflow_engine.execute.return_value = expected

    result = dispatcher.run_context_workflow(
        context_id="context-2",
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
        workflow_id="workflow-custom",
    )

    assert result is expected
    assert (
        workflow_engine.execute.call_args.kwargs["workflow_id"]
        == "workflow-custom"
    )


def test_run_context_workflow_generates_workflow_id() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-3",
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
    )

    workflow_id = (
        workflow_engine.execute.call_args.kwargs["workflow_id"]
    )

    assert workflow_id
    assert isinstance(workflow_id, str)


def test_run_context_workflow_uses_default_workflow_name() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-4",
        workflow_type=(
            ContextWorkflowType.GENERAL_DOCUMENTATION
        ),
    )

    assert (
        workflow_engine.execute.call_args.kwargs["workflow_name"]
        == "Build Project0 Context"
    )


def test_run_context_workflow_uses_custom_workflow_name() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    expected = _workflow_result(
        workflow_name="Custom Context Workflow"
    )
    workflow_engine.execute.return_value = expected

    result = dispatcher.run_context_workflow(
        context_id="context-5",
        workflow_type=ContextWorkflowType.VALIDATE_DOCUMENTATION,
        workflow_name="Custom Context Workflow",
    )

    assert result is expected
    assert (
        workflow_engine.execute.call_args.kwargs["workflow_name"]
        == "Custom Context Workflow"
    )


def test_run_context_workflow_creates_one_context_task() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-6",
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
    )

    tasks = workflow_engine.execute.call_args.kwargs["tasks"]

    assert len(tasks) == 1
    assert tasks[0].name == "Build Documentation Context"
    assert callable(tasks[0].action)


def test_context_task_calls_context_builder_with_request() -> None:
    (
        dispatcher,
        _,
        context_builder,
        workflow_engine,
    ) = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()
    context_builder.build_documentation_context.return_value = (
        "context-package"
    )

    dispatcher.run_context_workflow(
        context_id="context-7",
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
    )

    task = workflow_engine.execute.call_args.kwargs["tasks"][0]
    output = task.action()

    assert output == "context-package"
    context_builder.build_documentation_context.assert_called_once_with(
        context_id="context-7",
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
    )


def test_run_context_workflow_returns_engine_result() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    expected = _workflow_result(
        workflow_id="workflow-return",
        workflow_name="Returned Workflow",
    )
    workflow_engine.execute.return_value = expected

    result = dispatcher.run_context_workflow(
        context_id="context-8",
        workflow_type=(
            ContextWorkflowType.GENERAL_DOCUMENTATION
        ),
        workflow_name="Returned Workflow",
        workflow_id="workflow-return",
    )

    assert result is expected


def test_repository_is_not_used_directly_during_context_workflow() -> None:
    (
        dispatcher,
        repository,
        _,
        workflow_engine,
    ) = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-9",
        workflow_type=(
            ContextWorkflowType.GENERAL_DOCUMENTATION
        ),
    )

    assert repository.method_calls == []


def test_run_context_workflow_calls_engine_once() -> None:
    dispatcher, _, _, workflow_engine = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-10",
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
    )

    workflow_engine.execute.assert_called_once()
