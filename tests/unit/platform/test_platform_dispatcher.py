# ============================================================
# Project0 - Platform Dispatcher
#
# File: test_platform_dispatcher.py
#
# Purpose:
#     Verify platform dependency wiring, context workflow and
#     documentation workflow dispatch, validation, identifiers,
#     and results.
#
# ============================================================

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

import pytest

from project0.models.context_models import ContextWorkflowType
from project0.models.documentation_workflow_models import (
    DocumentationChangeProposal,
    DocumentationReview,
    DocumentationWorkflowResult,
    DocumentationWorkflowState,
    DocumentationWorkflowStatus,
    DocumentationWorkflowSummary,
    ReviewDecision,
)
from project0.models.workflow_models import (
    WorkflowExecutionResult,
    WorkflowStatus,
)
from project0.platform.platform_dispatcher import (
    PlatformDispatcher,
    _create_documentation_workflow,
)


STARTED_AT = datetime(2026, 8, 4, 18, 0, tzinfo=UTC)
COMPLETED_AT = datetime(2026, 8, 4, 18, 1, tzinfo=UTC)


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


def _documentation_workflow_result(
    workflow_id: str = "documentation-workflow-1",
) -> DocumentationWorkflowResult:
    """Create a completed documentation workflow result."""

    return DocumentationWorkflowResult(
        workflow_id=workflow_id,
        status=DocumentationWorkflowStatus.COMPLETED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        reasoning_result=None,
        proposals=(),
        reviews=(),
        applied_changes=(),
        preliminary_validation=None,
        final_validation=None,
        git_diff="",
        summary=DocumentationWorkflowSummary(
            proposed_count=0,
            approved_count=0,
            revised_count=0,
            rejected_count=0,
            skipped_count=0,
            applied_count=0,
            failed_count=0,
        ),
    )


def _documentation_workflow_state(
    workflow_id: str = "documentation-workflow-1",
) -> DocumentationWorkflowState:
    """Create documentation workflow state awaiting user review."""

    proposal = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the documentation.",
        proposal_id="proposal-001",
    )

    return DocumentationWorkflowState(
        workflow_id=workflow_id,
        status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
        started_at=STARTED_AT,
        reasoning_result=None,
        proposals=(proposal,),
    )


def _documentation_review(
    proposal_id: str = "proposal-001",
) -> DocumentationReview:
    """Create a user-supplied documentation review."""

    return DocumentationReview(
        proposal_id=proposal_id,
        decision=ReviewDecision.APPROVE,
        reviewed_at=COMPLETED_AT,
    )


def _dispatcher(
    *,
    include_documentation_workflow: bool = False,
) -> tuple[
    PlatformDispatcher,
    Mock,
    Mock,
    Mock,
    Mock | None,
]:
    """Create a dispatcher with mocked dependencies."""

    repository = Mock()
    context_builder = Mock()
    workflow_engine = Mock()
    documentation_workflow = (
        Mock() if include_documentation_workflow else None
    )

    dispatcher = PlatformDispatcher(
        repository=repository,
        context_builder=context_builder,
        workflow_engine=workflow_engine,
        documentation_workflow=documentation_workflow,
    )

    return (
        dispatcher,
        repository,
        context_builder,
        workflow_engine,
        documentation_workflow,
    )


def test_platform_dispatcher_stores_dependencies() -> None:
    (
        dispatcher,
        repository,
        context_builder,
        workflow_engine,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)

    assert dispatcher.repository is repository
    assert dispatcher.context_builder is context_builder
    assert dispatcher.workflow_engine is workflow_engine
    assert dispatcher.documentation_workflow is documentation_workflow


def test_documentation_workflow_defaults_to_none() -> None:
    """Documentation workflow configuration is optional."""

    dispatcher, _, _, _, documentation_workflow = _dispatcher()

    assert documentation_workflow is None
    assert dispatcher.documentation_workflow is None


def test_run_context_workflow_rejects_empty_context_id() -> None:
    dispatcher, _, _, workflow_engine, _ = _dispatcher()

    with pytest.raises(ValueError, match="cannot be empty"):
        dispatcher.run_context_workflow(
            context_id="   ",
            workflow_type=(
                ContextWorkflowType.GENERAL_DOCUMENTATION
            ),
        )

    workflow_engine.execute.assert_not_called()


def test_run_context_workflow_rejects_empty_workflow_name() -> None:
    dispatcher, _, _, workflow_engine, _ = _dispatcher()

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
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
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
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-3",
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
    )

    workflow_id = (
        workflow_engine.execute.call_args.kwargs["workflow_id"]
    )

    UUID(workflow_id)
    assert isinstance(workflow_id, str)


def test_run_context_workflow_uses_default_workflow_name() -> None:
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
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
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
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
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
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
        _,
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
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
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
        _,
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
    dispatcher, _, _, workflow_engine, _ = _dispatcher()
    workflow_engine.execute.return_value = _workflow_result()

    dispatcher.run_context_workflow(
        context_id="context-10",
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
    )

    workflow_engine.execute.assert_called_once()


def test_run_documentation_workflow_requires_configuration() -> None:
    """Documentation dispatch fails when no workflow is configured."""

    dispatcher, _, _, _, _ = _dispatcher()

    with pytest.raises(
        RuntimeError,
        match="The documentation workflow is not configured.",
    ):
        dispatcher.run_documentation_workflow(
            user_request="Update the documentation.",
        )


def test_run_documentation_workflow_rejects_empty_request() -> None:
    """Documentation dispatch rejects an empty user request."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)

    with pytest.raises(ValueError, match="User request cannot be empty"):
        dispatcher.run_documentation_workflow(
            user_request="   ",
        )

    assert documentation_workflow is not None
    documentation_workflow.execute.assert_not_called()


def test_run_documentation_workflow_uses_supplied_workflow_id() -> None:
    """Documentation dispatch preserves a supplied workflow ID."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    expected = _documentation_workflow_result(
        workflow_id="documentation-custom"
    )
    assert documentation_workflow is not None
    documentation_workflow.execute.return_value = expected

    result = dispatcher.run_documentation_workflow(
        user_request="Update the architecture documentation.",
        target_paths=("docs/Documentation_Agent_Architecture.md",),
        workflow_id="documentation-custom",
    )

    assert result is expected

    request = documentation_workflow.execute.call_args.args[0]

    assert request.workflow_id == "documentation-custom"
    assert request.user_request == (
        "Update the architecture documentation."
    )
    assert request.target_paths == (
        "docs/Documentation_Agent_Architecture.md",
    )


def test_run_documentation_workflow_generates_workflow_id() -> None:
    """Documentation dispatch generates a UUID when none is supplied."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    assert documentation_workflow is not None
    documentation_workflow.execute.return_value = (
        _documentation_workflow_result()
    )

    dispatcher.run_documentation_workflow(
        user_request="Review project documentation.",
    )

    request = documentation_workflow.execute.call_args.args[0]

    UUID(request.workflow_id)
    assert isinstance(request.workflow_id, str)


def test_run_documentation_workflow_defaults_target_paths() -> None:
    """Documentation dispatch defaults to no explicit target paths."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    assert documentation_workflow is not None
    documentation_workflow.execute.return_value = (
        _documentation_workflow_result()
    )

    dispatcher.run_documentation_workflow(
        user_request="Review project documentation.",
    )

    request = documentation_workflow.execute.call_args.args[0]

    assert request.target_paths == ()


def test_run_documentation_workflow_returns_workflow_state() -> None:
    """Documentation dispatch returns intermediate review state."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    expected = _documentation_workflow_state(
        workflow_id="documentation-review"
    )
    assert documentation_workflow is not None
    documentation_workflow.execute.return_value = expected

    result = dispatcher.run_documentation_workflow(
        user_request="Update documentation.",
        workflow_id="documentation-review",
    )

    assert result is expected
    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    documentation_workflow.execute.assert_called_once()


def test_run_documentation_workflow_returns_workflow_result() -> None:
    """Documentation dispatch also returns a completed workflow result."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    expected = _documentation_workflow_result(
        workflow_id="documentation-return"
    )
    assert documentation_workflow is not None
    documentation_workflow.execute.return_value = expected

    result = dispatcher.run_documentation_workflow(
        user_request="Update documentation.",
        workflow_id="documentation-return",
    )

    assert result is expected
    documentation_workflow.execute.assert_called_once()


def test_submit_documentation_review_requires_configuration() -> None:
    """Review dispatch fails when no documentation workflow exists."""

    dispatcher, _, _, _, _ = _dispatcher()

    with pytest.raises(
        RuntimeError,
        match="The documentation workflow is not configured.",
    ):
        dispatcher.submit_documentation_review(
            workflow_id="documentation-review",
            review=_documentation_review(),
        )


def test_submit_documentation_review_rejects_empty_workflow_id() -> None:
    """Review dispatch rejects an empty workflow identifier."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)

    with pytest.raises(
        ValueError,
        match="Workflow identifier cannot be empty",
    ):
        dispatcher.submit_documentation_review(
            workflow_id="   ",
            review=_documentation_review(),
        )

    assert documentation_workflow is not None
    documentation_workflow.submit_review.assert_not_called()


def test_submit_documentation_review_forwards_review() -> None:
    """Review dispatch forwards workflow ID and user decision."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    expected = _documentation_workflow_result(
        workflow_id="documentation-review"
    )
    review = _documentation_review()
    assert documentation_workflow is not None
    documentation_workflow.submit_review.return_value = expected

    result = dispatcher.submit_documentation_review(
        workflow_id="documentation-review",
        review=review,
    )

    assert result is expected
    documentation_workflow.submit_review.assert_called_once_with(
        "documentation-review",
        review,
    )


def test_submit_documentation_review_returns_intermediate_state() -> None:
    """Review dispatch can return state when more reviews remain."""

    (
        dispatcher,
        _,
        _,
        _,
        documentation_workflow,
    ) = _dispatcher(include_documentation_workflow=True)
    expected = _documentation_workflow_state(
        workflow_id="documentation-review"
    )
    review = _documentation_review()
    assert documentation_workflow is not None
    documentation_workflow.submit_review.return_value = expected

    result = dispatcher.submit_documentation_review(
        workflow_id="documentation-review",
        review=review,
    )

    assert result is expected
    assert result.status is DocumentationWorkflowStatus.REVIEW_REQUIRED


def test_create_documentation_workflow_uses_reasoning_model_name(
    tmp_path,
) -> None:
    """Documentation workflow propagates the configured reasoning model."""

    reasoning_provider = Mock()

    workflow = _create_documentation_workflow(
        repository_root=tmp_path,
        reasoning_provider=reasoning_provider,
        reasoning_model_name="qwen2.5:7b",
        review_decision_provider=None,
    )

    assert workflow is not None
    assert workflow._reasoning_service._prompt_builder.model_name == (
        "qwen2.5:7b"
    )



def test_create_documentation_workflow_uses_generic_validators(
    tmp_path,
) -> None:
    """Default documentation validation excludes Project0 policy rules."""

    reasoning_provider = Mock()

    workflow = _create_documentation_workflow(
        repository_root=tmp_path,
        reasoning_provider=reasoning_provider,
        reasoning_model_name="qwen2.5:7b",
        review_decision_provider=None,
    )

    assert workflow is not None

    validator_names = tuple(
        validator.validator_name
        for validator in workflow._validation_service._validators
    )

    assert validator_names == (
        "markdown",
        "link",
        "mkdocs",
    )
    assert "documentation_consistency" not in validator_names
