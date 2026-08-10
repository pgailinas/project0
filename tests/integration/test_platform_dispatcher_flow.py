# ============================================================
# Project0 - Integration Tests
#
# File: test_platform_dispatcher_flow.py
#
# Purpose:
#     Verify end-to-end platform dispatch using the real
#     Project0 repository, context, and workflow components.
#
# ============================================================

from __future__ import annotations

from project0.models.context_models import (
    ContextBuildStatus,
    ContextPackage,
    ContextWorkflowType,
)
from project0.models.workflow_models import (
    TaskStatus,
    WorkflowStatus,
)
from project0.platform.platform_dispatcher import (
    create_platform_dispatcher,
)


def test_platform_dispatcher_runs_general_context_workflow() -> None:
    """Run a general documentation workflow through real services."""

    dispatcher = create_platform_dispatcher()

    workflow_result = dispatcher.run_context_workflow(
        context_id="integration-platform-general",
        workflow_type=ContextWorkflowType.GENERAL_DOCUMENTATION,
        workflow_name="Platform General Context Integration",
        workflow_id="integration-platform-general-workflow",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED
    assert workflow_result.workflow_id == (
        "integration-platform-general-workflow"
    )
    assert workflow_result.workflow_name == (
        "Platform General Context Integration"
    )
    assert workflow_result.error_message is None
    assert len(workflow_result.task_results) == 1

    task_result = workflow_result.task_results[0]

    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.error_message is None
    assert isinstance(task_result.output, ContextPackage)

    context_package = task_result.output

    assert context_package.status == ContextBuildStatus.COMPLETED
    assert context_package.succeeded
    assert context_package.context_id == (
        "integration-platform-general"
    )
    assert context_package.project_id == "Project0"
    assert context_package.source_count > 0
    assert context_package.total_characters > 0
    assert context_package.warnings == ()
    assert context_package.errors == ()

    relative_paths = {
        document.relative_path
        for document in context_package.documents
    }

    assert "README.md" in relative_paths
    assert "docs/project/Project_Charter.md" in relative_paths
    assert "docs/project/Implementation_Roadmap.md" in relative_paths

    assert context_package.source_count == len(
        context_package.documents
    )
    assert context_package.total_characters == sum(
        len(document.content)
        for document in context_package.documents
    )


def test_platform_dispatcher_runs_component_context_workflow() -> None:
    """Run a component implementation workflow through real services."""

    dispatcher = create_platform_dispatcher()

    workflow_result = dispatcher.run_context_workflow(
        context_id="integration-platform-component",
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
        workflow_name="Platform Component Context Integration",
        workflow_id="integration-platform-component-workflow",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED
    assert workflow_result.error_message is None
    assert len(workflow_result.task_results) == 1

    task_result = workflow_result.task_results[0]

    assert task_result.status == TaskStatus.COMPLETED
    assert isinstance(task_result.output, ContextPackage)

    context_package = task_result.output

    assert context_package.succeeded
    assert context_package.source_count > 0

    relative_paths = {
        document.relative_path
        for document in context_package.documents
    }

    assert "README.md" in relative_paths
    assert "docs/project/Project_Charter.md" in relative_paths
    assert "docs/project/Implementation_Roadmap.md" in relative_paths
    assert "docs/platform/Component_Communication_Design.md" in relative_paths


def test_platform_dispatcher_preserves_document_metadata() -> None:
    """Verify dispatched context retains repository metadata."""

    dispatcher = create_platform_dispatcher()

    workflow_result = dispatcher.run_context_workflow(
        context_id="integration-platform-metadata",
        workflow_type=ContextWorkflowType.GENERAL_DOCUMENTATION,
        workflow_id="integration-platform-metadata-workflow",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED

    context_package = workflow_result.task_results[0].output

    assert isinstance(context_package, ContextPackage)
    assert context_package.documents

    project_charter = next(
        document
        for document in context_package.documents
        if document.relative_path == "docs/project/Project_Charter.md"
    )

    assert project_charter.content.strip()
    assert project_charter.size_bytes > 0
    assert project_charter.modified_at.tzinfo is not None
