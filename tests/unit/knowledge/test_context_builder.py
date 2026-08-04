# ============================================================
# Project0 - Knowledge Services
#
# File: test_context_builder.py
#
# Purpose:
#     Verify workflow-specific context discovery, selection,
#     packaging, warnings, failures, and factory creation.
#
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from project0.knowledge.context_builder import (
    ContextBuilder,
    create_context_builder,
)
from project0.knowledge.context_filters import ContextFilterCriteria
from project0.knowledge.context_rules import ContextRuleRegistry
from project0.models.context_models import (
    ContextBuildStatus,
    ContextPackage,
    ContextWorkflowType,
)
from project0.repository.repository_service import (
    FileBatchResult,
    FileContent,
    RepositoryError,
    RepositoryErrorCode,
    RepositoryFile,
    RepositoryListResult,
)


def _repository_file(
    relative_path: str,
    size_bytes: int,
) -> RepositoryFile:
    """Create repository metadata for a test document."""

    return RepositoryFile(
        relative_path=relative_path,
        extension=".md",
        size_bytes=size_bytes,
        modified_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
        is_documentation=True,
    )


def _file_content(
    relative_path: str,
    content: str,
) -> FileContent:
    """Create repository file content for a test document."""

    return FileContent(
        file=_repository_file(
            relative_path=relative_path,
            size_bytes=len(content.encode("utf-8")),
        ),
        content=content,
    )


def _general_criteria() -> ContextFilterCriteria:
    """Return filter criteria that include general documentation."""

    return ContextFilterCriteria(
        extensions=frozenset({".md"}),
        include_patterns=("README.md", "docs/*.md"),
        documentation_only=True,
    )


def _rule_registry(
    criteria: ContextFilterCriteria | None = None,
) -> Mock:
    """Create a mocked rule registry for builder tests."""

    registry = Mock(spec=ContextRuleRegistry)
    registry.get_filter_criteria.return_value = (
        criteria or _general_criteria()
    )
    return registry


def test_create_context_builder_returns_builder() -> None:
    repository_service = Mock()

    builder = create_context_builder(repository_service)

    assert isinstance(builder, ContextBuilder)
    assert builder.repository_service is repository_service
    assert builder.rule_registry is not None
    assert builder.project_id == "Project0"


def test_create_context_builder_uses_custom_project_id() -> None:
    repository_service = Mock()

    builder = create_context_builder(
        repository_service=repository_service,
        project_id="ProductA",
    )

    assert builder.project_id == "ProductA"


def test_create_context_builder_uses_custom_rule_registry() -> None:
    repository_service = Mock()
    rule_registry = _rule_registry()

    builder = create_context_builder(
        repository_service=repository_service,
        rule_registry=rule_registry,
    )

    assert builder.rule_registry is rule_registry


def test_build_documentation_context_rejects_empty_id() -> None:
    builder = ContextBuilder(
        repository_service=Mock(),
        rule_registry=_rule_registry(),
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        builder.build_documentation_context(
            "   ",
            ContextWorkflowType.GENERAL_DOCUMENTATION,
        )


def test_build_documentation_context_packages_selected_documents() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            files=(
                _repository_file("README.md", 11),
                _repository_file("docs/Architecture.md", 15),
            )
        )
    )
    repository_service.read_files.return_value = FileBatchResult(
        files=(
            _file_content("README.md", "# Project0\n"),
            _file_content(
                "docs/Architecture.md",
                "# Architecture\n",
            ),
        )
    )

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(),
    )

    package = builder.build_documentation_context(
        "context-1",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    assert isinstance(package, ContextPackage)
    assert package.status == ContextBuildStatus.COMPLETED
    assert package.context_id == "context-1"
    assert package.project_id == "Project0"
    assert package.source_count == 2
    assert package.total_characters == (
        len("# Project0\n") + len("# Architecture\n")
    )
    assert package.warnings == ()
    assert package.errors == ()

    assert [
        document.relative_path
        for document in package.documents
    ] == [
        "README.md",
        "docs/Architecture.md",
    ]


def test_build_documentation_context_uses_workflow_rule() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            files=(
                _repository_file("README.md", 11),
            )
        )
    )
    repository_service.read_files.return_value = FileBatchResult()

    rule_registry = _rule_registry()
    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=rule_registry,
    )

    builder.build_documentation_context(
        "context-rule",
        ContextWorkflowType.IMPLEMENT_COMPONENT,
    )

    rule_registry.get_filter_criteria.assert_called_once_with(
        ContextWorkflowType.IMPLEMENT_COMPONENT
    )


def test_build_documentation_context_reads_rule_selected_paths() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            files=(
                _repository_file("README.md", 11),
                _repository_file("docs/Architecture.md", 15),
            )
        )
    )
    repository_service.read_files.return_value = FileBatchResult()

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(),
    )

    builder.build_documentation_context(
        "context-2",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    repository_service.read_files.assert_called_once_with(
        [
            "docs/Architecture.md",
            "README.md",
        ]
    )


def test_build_documentation_context_reads_only_matching_files() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            files=(
                _repository_file("README.md", 11),
                _repository_file("docs/Architecture.md", 15),
                _repository_file("docs/archive/Old.md", 10),
            )
        )
    )
    repository_service.read_files.return_value = FileBatchResult(
        files=(
            _file_content("README.md", "# Project0\n"),
            _file_content(
                "docs/Architecture.md",
                "# Architecture\n",
            ),
        )
    )

    criteria = ContextFilterCriteria(
        extensions=frozenset({".md"}),
        include_patterns=("README.md", "docs/*.md"),
        exclude_paths=("docs/archive",),
        documentation_only=True,
    )
    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(criteria),
    )

    package = builder.build_documentation_context(
        "context-filtered",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    repository_service.read_files.assert_called_once_with(
        [
            "docs/Architecture.md",
            "README.md",
        ]
    )
    assert package.source_count == 2


def test_build_documentation_context_preserves_document_metadata() -> None:
    repository_service = Mock()
    file_content = _file_content(
        "docs/Architecture.md",
        "# Architecture\n",
    )

    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(files=(file_content.file,))
    )
    repository_service.read_files.return_value = FileBatchResult(
        files=(file_content,)
    )

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(),
    )

    package = builder.build_documentation_context(
        "context-3",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )
    document = package.documents[0]

    assert document.relative_path == "docs/Architecture.md"
    assert document.content == "# Architecture\n"
    assert document.size_bytes == file_content.file.size_bytes
    assert document.modified_at == file_content.file.modified_at


def test_build_documentation_context_returns_warning_when_no_match() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult()
    )

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(),
    )

    package = builder.build_documentation_context(
        "context-empty",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    assert package.status == (
        ContextBuildStatus.COMPLETED_WITH_WARNINGS
    )
    assert package.documents == ()
    assert package.source_count == 0
    assert package.total_characters == 0
    assert package.warnings == (
        "No Markdown documentation files matched the "
        "workflow context rules.",
    )

    repository_service.read_files.assert_not_called()


def test_build_documentation_context_fails_on_discovery_error() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            errors=(
                RepositoryError(
                    code=RepositoryErrorCode.FILE_READ_ERROR,
                    message="Unable to inspect repository file.",
                    path="docs/Architecture.md",
                ),
            )
        )
    )

    rule_registry = _rule_registry()
    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=rule_registry,
    )

    package = builder.build_documentation_context(
        "context-discovery-failure",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    assert package.status == ContextBuildStatus.FAILED
    assert package.documents == ()
    assert package.source_count == 0
    assert package.total_characters == 0
    assert package.errors == (
        "Unable to inspect repository file.",
    )

    rule_registry.get_filter_criteria.assert_not_called()
    repository_service.read_files.assert_not_called()


def test_build_documentation_context_preserves_partial_reads() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            files=(
                _repository_file("README.md", 11),
                _repository_file("docs/Missing.md", 10),
            )
        )
    )
    repository_service.read_files.return_value = FileBatchResult(
        files=(
            _file_content("README.md", "# Project0\n"),
        ),
        errors=(
            RepositoryError(
                code=RepositoryErrorCode.FILE_NOT_FOUND,
                message="Repository file was not found.",
                path="docs/Missing.md",
            ),
        ),
    )

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(),
    )

    package = builder.build_documentation_context(
        "context-partial",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    assert package.status == (
        ContextBuildStatus.COMPLETED_WITH_WARNINGS
    )
    assert package.source_count == 1
    assert len(package.documents) == 1
    assert package.documents[0].relative_path == "README.md"
    assert package.warnings == (
        "docs/Missing.md: Repository file was not found.",
    )
    assert package.errors == ()


def test_build_documentation_context_propagates_missing_rule() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult(
            files=(
                _repository_file("README.md", 11),
            )
        )
    )

    rule_registry = _rule_registry()
    rule_registry.get_filter_criteria.side_effect = ValueError(
        "No context rule is registered."
    )

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=rule_registry,
    )

    with pytest.raises(
        ValueError,
        match="No context rule is registered",
    ):
        builder.build_documentation_context(
            "context-missing-rule",
            ContextWorkflowType.IMPLEMENT_COMPONENT,
        )

    repository_service.read_files.assert_not_called()


def test_format_read_warning_with_path() -> None:
    warning = ContextBuilder._format_read_warning(
        "docs/Missing.md",
        "Repository file was not found.",
    )

    assert warning == (
        "docs/Missing.md: Repository file was not found."
    )


def test_format_read_warning_without_path() -> None:
    warning = ContextBuilder._format_read_warning(
        None,
        "Unknown repository error.",
    )

    assert warning == "Unknown repository error."


def test_build_documentation_context_uses_timezone_aware_timestamp() -> None:
    repository_service = Mock()
    repository_service.list_documentation_files.return_value = (
        RepositoryListResult()
    )

    builder = ContextBuilder(
        repository_service=repository_service,
        rule_registry=_rule_registry(),
    )

    package = builder.build_documentation_context(
        "context-timestamp",
        ContextWorkflowType.GENERAL_DOCUMENTATION,
    )

    assert package.created_at.tzinfo == timezone.utc
