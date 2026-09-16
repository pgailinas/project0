# ============================================================
# Project0 - Validation Service Flow Tests
#
# File: test_validation_service_flow.py
#
# Purpose:
#     Verify the complete Project0 validation flow using the
#     real validation service and validator implementations.
#
# ============================================================

from collections.abc import Sequence
from pathlib import Path
import subprocess

from project0.models.validation_models import (
    ValidationRequest,
    ValidationStatus,
)
from project0.validation.documentation_consistency_validator import (
    DocumentationConsistencyValidator,
)
from project0.validation.link_validator import LinkValidator
from project0.validation.markdown_validator import MarkdownValidator
from project0.validation.mkdocs_validator import MkDocsValidator
from project0.validation.validation_service import ValidationService


def _write_repository_documents(repository_root: Path) -> None:
    """Create a complete, consistent Project0 documentation set."""

    documents = {
        "docs/index.md": (
            "# Project0\n\n"
            "[Architecture](documentation-agent/Documentation_Agent_Architecture.md)\n"
        ),
        "docs/platform/Project_Charter.md": "# Project Charter\n",
        "docs/platform/Documentation_Standards.md": "# Documentation Standards\n",
        "docs/documentation-agent/Documentation_Agent_Functional_Spec.md": (
            "# Documentation Agent Functional Specification\n"
        ),
        "docs/documentation-agent/Documentation_Agent_Architecture.md": (
            "# Documentation Agent Architecture\n\n"
            "## Architectural Components\n"
        ),
        "docs/documentation-agent/Documentation_Agent_Design.md": (
            "# Documentation Agent Component Design\n"
        ),
        "docs/platform/Component_Communication_Design.md": (
            "# Component Communication Design\n"
        ),
        "docs/platform/Shared_Data_Models_and_Error_Contracts.md": (
            "# Shared Data Models and Error Contracts\n"
        ),
        "docs/platform/Implementation_Roadmap.md": (
            "# Implementation Roadmap\n\n"
            "## Phase 1 — Foundation\n\n"
            "## Phase 2 — Core Platform Services\n\n"
            "## Phase 3 — Repository Knowledge Services\n\n"
            "## Phase 4 — AI Reasoning Integration\n\n"
            "## Phase 5 — Validation Services\n"
        ),
        "docs/platform/Implementation_Status.md": (
            "# Implementation Status\n\n"
            "## Current Phase\n\n"
            "Phase 5 – Validation Services (In Progress)\n\n"
            "## Overall Status\n\n"
            "- ✅ Phase 1 – Foundation: Completed\n"
            "- ✅ Phase 2 – Core Platform Services: Completed\n"
            "- ✅ Phase 3 – Repository Knowledge Services: Completed\n"
            "- ✅ Phase 4 – AI Reasoning Integration: Completed\n"
        ),
        "docs/platform/Project_Directory_Structure.md": (
            "# Project Directory Structure\n"
        ),
    }

    for repository_path, document_content in documents.items():
        file_path = repository_root / repository_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(document_content, encoding="utf-8")

    (repository_root / "mkdocs.yml").write_text(
        "site_name: Project0\n"
        "nav:\n"
        "  - Home: index.md\n",
        encoding="utf-8",
    )


def _successful_command_runner(
    command: Sequence[str],
    working_directory: Path,
) -> subprocess.CompletedProcess[str]:
    """Return a successful deterministic MkDocs command result."""

    del working_directory

    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout="INFO - Documentation built successfully.\n",
        stderr="",
    )


def _failed_command_runner(
    command: Sequence[str],
    working_directory: Path,
) -> subprocess.CompletedProcess[str]:
    """Return a failed deterministic MkDocs command result."""

    del working_directory

    return subprocess.CompletedProcess(
        args=command,
        returncode=1,
        stdout="",
        stderr="ERROR - MkDocs build failed.\n",
    )


def _create_validation_service(
    repository_root: Path,
    *,
    command_runner=_successful_command_runner,
) -> ValidationService:
    """Create the real validation pipeline for integration tests."""

    return ValidationService(
        validators=(
            MarkdownValidator(repository_root),
            LinkValidator(repository_root),
            MkDocsValidator(
                repository_root=repository_root,
                command_runner=command_runner,
            ),
            DocumentationConsistencyValidator(repository_root),
        )
    )


def test_complete_validation_flow_passes(tmp_path: Path) -> None:
    """A valid repository passes the complete validation flow."""

    _write_repository_documents(tmp_path)
    service = _create_validation_service(tmp_path)

    request = ValidationRequest(
        target_paths=(
            "docs/index.md",
            "docs/documentation-agent/Documentation_Agent_Architecture.md",
            "docs/platform/Implementation_Roadmap.md",
            "docs/platform/Implementation_Status.md",
        ),
        validation_id="validation-integration-001",
    )

    result = service.validate(request)

    assert result.validation_id == "validation-integration-001"
    assert result.status is ValidationStatus.PASSED
    assert len(result.validator_results) == 4
    assert tuple(
        validator_result.validator_name
        for validator_result in result.validator_results
    ) == (
        "markdown",
        "link",
        "mkdocs",
        "documentation_consistency",
    )
    assert result.error_message is None


def test_markdown_failure_is_propagated_through_service(
    tmp_path: Path,
) -> None:
    """A real Markdown validation failure fails the combined flow."""

    _write_repository_documents(tmp_path)
    invalid_document = tmp_path / "docs/index.md"
    invalid_document.write_text(
        "## Missing Document Title\n",
        encoding="utf-8",
    )

    service = _create_validation_service(tmp_path)

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "missing-document-title"
        for issue in result.issues
    )
    assert result.validator_results[0].status is ValidationStatus.FAILED


def test_link_failure_is_propagated_through_service(
    tmp_path: Path,
) -> None:
    """A real link validation failure fails the combined flow."""

    _write_repository_documents(tmp_path)
    index_path = tmp_path / "docs/index.md"
    index_path.write_text(
        "# Project0\n\n"
        "[Missing](Missing_Document.md)\n",
        encoding="utf-8",
    )

    service = _create_validation_service(tmp_path)

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "missing-link-target"
        for issue in result.issues
    )
    assert result.validator_results[1].status is ValidationStatus.FAILED


def test_consistency_failure_is_propagated_through_service(
    tmp_path: Path,
) -> None:
    """A missing required document fails the combined flow."""

    _write_repository_documents(tmp_path)
    (
        tmp_path / "docs/platform/Component_Communication_Design.md"
    ).unlink()

    service = _create_validation_service(tmp_path)

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "required-document-missing"
        and issue.repository_path
        == "docs/platform/Component_Communication_Design.md"
        for issue in result.issues
    )
    assert result.validator_results[3].status is ValidationStatus.FAILED


def test_mkdocs_failure_is_propagated_through_service(
    tmp_path: Path,
) -> None:
    """A failed MkDocs build fails the combined flow."""

    _write_repository_documents(tmp_path)
    service = _create_validation_service(
        tmp_path,
        command_runner=_failed_command_runner,
    )

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "mkdocs-build-failed"
        for issue in result.issues
    )
    assert result.validator_results[2].status is ValidationStatus.FAILED


def test_warning_is_preserved_without_failing_flow(
    tmp_path: Path,
) -> None:
    """A real validator warning produces a warning combined status."""

    _write_repository_documents(tmp_path)
    architecture_path = (
        tmp_path / "docs/documentation-agent/Documentation_Agent_Architecture.md"
    )
    architecture_path.write_text(
        "# Documentation Agent Architecture\n\n"
        "## Components\n\n"
        "## Components\n",
        encoding="utf-8",
    )

    service = _create_validation_service(tmp_path)

    result = service.validate(
        ValidationRequest(
            target_paths=(
                "docs/documentation-agent/Documentation_Agent_Architecture.md",
            )
        )
    )

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert any(
        issue.code == "duplicate-heading"
        for issue in result.issues
    )
    assert result.error_message is None
