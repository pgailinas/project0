# ============================================================
# Project0 - Integration Tests
#
# File: test_context_builder_flow.py
#
# Purpose:
#     Verify integration of startup validation, repository
#     access, context rules, context building, and workflows.
#
# ============================================================

from __future__ import annotations

from project0.common.startup_validation import validate_startup
from project0.config.settings import SETTINGS
from project0.knowledge.context_builder import ContextBuilder
from project0.models.context_models import (
    ContextBuildStatus,
    ContextPackage,
    ContextWorkflowType,
)
from project0.repository.repository_service import RepositoryService
from project0.workflow.workflow_engine import (
    TaskStatus,
    WorkflowEngine,
    WorkflowStatus,
    WorkflowTask,
)


def test_context_builder_flow_packages_project_documentation() -> None:
    """Build general Project0 documentation context through a workflow."""

    validate_startup(SETTINGS)

    repository_service = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    context_builder = ContextBuilder(
        repository_service=repository_service
    )
    workflow_engine = WorkflowEngine()

    context_task = WorkflowTask(
        name="Build Project0 Documentation Context",
        action=lambda: context_builder.build_documentation_context(
            "integration-context",
            ContextWorkflowType.GENERAL_DOCUMENTATION,
        ),
    )

    workflow_result = workflow_engine.execute(
        workflow_name="Context Builder Integration",
        tasks=[context_task],
        workflow_id="integration-context-builder",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED
    assert workflow_result.workflow_id == (
        "integration-context-builder"
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
    assert context_package.context_id == "integration-context"
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
    assert "docs/Project_Charter.md" in relative_paths
    assert "docs/Implementation_Roadmap.md" in relative_paths

    assert context_package.source_count == len(
        context_package.documents
    )
    assert context_package.total_characters == sum(
        len(document.content)
        for document in context_package.documents
    )


def test_context_builder_flow_preserves_document_metadata() -> None:
    """Verify context documents retain repository metadata."""

    validate_startup(SETTINGS)

    repository_service = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    context_builder = ContextBuilder(
        repository_service=repository_service
    )
    workflow_engine = WorkflowEngine()

    context_task = WorkflowTask(
        name="Build Metadata Context",
        action=lambda: context_builder.build_documentation_context(
            "integration-context-metadata",
            ContextWorkflowType.GENERAL_DOCUMENTATION,
        ),
    )

    workflow_result = workflow_engine.execute(
        workflow_name="Context Metadata Integration",
        tasks=[context_task],
        workflow_id="integration-context-metadata",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED

    context_package = workflow_result.task_results[0].output

    assert isinstance(context_package, ContextPackage)
    assert context_package.documents

    project_charter = next(
        document
        for document in context_package.documents
        if document.relative_path == "docs/Project_Charter.md"
    )

    assert project_charter.content.strip()
    assert project_charter.size_bytes > 0
    assert project_charter.modified_at.tzinfo is not None


def test_context_builder_flow_excludes_generated_directories() -> None:
    """Verify excluded repository content is absent from context."""

    validate_startup(SETTINGS)

    repository_service = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    context_builder = ContextBuilder(
        repository_service=repository_service
    )

    context_package = (
        context_builder.build_documentation_context(
            "integration-context-exclusions",
            ContextWorkflowType.GENERAL_DOCUMENTATION,
        )
    )

    excluded_parts = {
        ".git",
        ".pytest_cache",
        "__pycache__",
        "site",
    }

    assert context_package.succeeded
    assert all(
        excluded_parts.isdisjoint(
            document.relative_path.split("/")
        )
        for document in context_package.documents
    )


def test_context_builder_flow_selects_component_documents() -> None:
    """Verify component workflows select implementation context."""

    validate_startup(SETTINGS)

    repository_service = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    context_builder = ContextBuilder(
        repository_service=repository_service
    )

    context_package = (
        context_builder.build_documentation_context(
            "integration-component-context",
            ContextWorkflowType.IMPLEMENT_COMPONENT,
        )
    )

    assert context_package.succeeded
    assert context_package.source_count > 0

    relative_paths = {
        document.relative_path
        for document in context_package.documents
    }

    assert "README.md" in relative_paths
    assert "docs/Project_Charter.md" in relative_paths
    assert "docs/Implementation_Roadmap.md" in relative_paths
    assert "docs/Component_Communication_Design.md" in relative_paths
