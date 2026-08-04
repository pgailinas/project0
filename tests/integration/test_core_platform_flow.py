# ============================================================
# Project0 - Integration Tests
#
# File: test_core_platform_flow.py
#
# Purpose:
#     Verify integration of settings, logging, startup
#     validation, workflow execution, and repository access.
#
# ============================================================

from __future__ import annotations

from project0.common.logging_config import configure_logging
from project0.common.startup_validation import validate_startup
from project0.config.settings import SETTINGS
from project0.repository.repository_service import (
    RepositoryListResult,
    RepositoryService,
)
from project0.workflow.workflow_engine import (
    TaskStatus,
    WorkflowEngine,
    WorkflowStatus,
    WorkflowTask,
)


def test_core_platform_repository_discovery_flow() -> None:
    """Run the current Project0 core platform flow end to end."""

    configure_logging()
    validate_startup(SETTINGS)

    repository_service = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    workflow_engine = WorkflowEngine()

    discovery_task = WorkflowTask(
        name="Discover Project0 Documentation",
        action=repository_service.list_documentation_files,
    )

    workflow_result = workflow_engine.execute(
        workflow_name="Core Platform Repository Discovery",
        tasks=[discovery_task],
        workflow_id="integration-core-platform",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED
    assert workflow_result.workflow_id == "integration-core-platform"
    assert workflow_result.error_message is None
    assert len(workflow_result.task_results) == 1

    task_result = workflow_result.task_results[0]

    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.error_message is None
    assert isinstance(task_result.output, RepositoryListResult)

    repository_result = task_result.output

    assert repository_result.succeeded
    assert repository_result.files
    assert repository_result.errors == ()

    relative_paths = {
        repository_file.relative_path
        for repository_file in repository_result.files
    }

    assert "README.md" in relative_paths
    assert "docs/Project_Charter.md" in relative_paths
    assert "docs/Implementation_Roadmap.md" in relative_paths

    assert all(
        repository_file.extension == ".md"
        for repository_file in repository_result.files
    )
    assert all(
        repository_file.is_documentation
        for repository_file in repository_result.files
    )

    excluded_parts = {
        ".git",
        ".pytest_cache",
        "__pycache__",
        "site",
    }

    assert all(
        excluded_parts.isdisjoint(
            repository_file.relative_path.split("/")
        )
        for repository_file in repository_result.files
    )


def test_core_platform_reads_discovered_document() -> None:
    """Verify that a workflow can discover and read documentation."""

    validate_startup(SETTINGS)

    repository_service = RepositoryService(
        repository_root=SETTINGS.project_root
    )
    workflow_engine = WorkflowEngine()

    read_task = WorkflowTask(
        name="Read Project Charter",
        action=lambda: repository_service.read_file(
            "docs/Project_Charter.md"
        ),
    )

    workflow_result = workflow_engine.execute(
        workflow_name="Core Platform Document Read",
        tasks=[read_task],
        workflow_id="integration-document-read",
    )

    assert workflow_result.status == WorkflowStatus.COMPLETED

    task_result = workflow_result.task_results[0]

    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.error_message is None
    assert task_result.output is not None
    assert task_result.output.succeeded
    assert task_result.output.file_content is not None
    assert (
        task_result.output.file_content.file.relative_path
        == "docs/Project_Charter.md"
    )
    assert task_result.output.file_content.content.strip()
