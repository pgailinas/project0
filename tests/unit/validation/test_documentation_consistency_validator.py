# ============================================================
# Project0 - Documentation Consistency Validator Tests
#
# File: test_documentation_consistency_validator.py
#
# Purpose:
#     Verify deterministic cross-document consistency checks
#     used by Project0 validation components.
#
# ============================================================

from pathlib import Path

from project0.models.validation_models import (
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
)
from project0.validation.documentation_consistency_validator import (
    DocumentationConsistencyValidator,
)


def _write_required_documents(
    repository_root: Path,
    *,
    roadmap_content: str,
    status_content: str,
) -> None:
    """Create the default required documentation set."""

    documents = {
        "docs/platform/Project_Charter.md": "# Project Charter\n",
        "docs/platform/Documentation_Standards.md": "# Documentation Standards\n",
        "docs/documentation-agent/Documentation_Agent_Functional_Spec.md": (
            "# Documentation Agent Functional Specification\n"
        ),
        "docs/documentation-agent/Documentation_Agent_Architecture.md": (
            "# Documentation Agent Architecture\n"
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
        "docs/platform/Implementation_Roadmap.md": roadmap_content,
        "docs/platform/Implementation_Status.md": status_content,
        "docs/platform/Project_Directory_Structure.md": (
            "# Project Directory Structure\n"
        ),
    }

    for repository_path, content in documents.items():
        file_path = repository_root / repository_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")


def test_consistent_documentation_passes(tmp_path: Path) -> None:
    """A complete and consistent documentation set passes validation."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 1 — Foundation\n\n"
            "## Phase 2 — Core Platform Services\n\n"
            "## Phase 3 — Repository Knowledge Services\n\n"
            "## Phase 4 — AI Reasoning Integration\n\n"
            "## Phase 5 — Validation Services\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "## Current Phase\n\n"
            "Phase 5 – Validation Services (Ready to Begin)\n\n"
            "## Overall Status\n\n"
            "- ✅ Phase 1 – Foundation: Completed\n"
            "- ✅ Phase 2 – Core Platform Services: Completed\n"
            "- ✅ Phase 3 – Repository Knowledge Services: Completed\n"
            "- ✅ Phase 4 – AI Reasoning Integration: Completed\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.validator_name == "documentation_consistency"
    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()
    assert result.error_message is None


def test_missing_required_document_fails(tmp_path: Path) -> None:
    """A missing required project document produces an error."""

    validator = DocumentationConsistencyValidator(
        repository_root=tmp_path,
        required_document_paths=("docs/Missing.md",),
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "required-document-missing"
    assert result.issues[0].severity is ValidationSeverity.ERROR
    assert result.issues[0].repository_path == "docs/Missing.md"


def test_required_document_outside_repository_fails(
    tmp_path: Path,
) -> None:
    """A configured required document outside the root is rejected."""

    validator = DocumentationConsistencyValidator(
        repository_root=tmp_path,
        required_document_paths=("../outside.md",),
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == (
        "required-document-outside-repository"
    )


def test_multiple_missing_required_documents_are_combined(
    tmp_path: Path,
) -> None:
    """All missing required documents are reported."""

    validator = DocumentationConsistencyValidator(
        repository_root=tmp_path,
        required_document_paths=(
            "docs/First.md",
            "docs/Second.md",
        ),
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 2
    assert {
        issue.repository_path
        for issue in result.issues
    } == {
        "docs/First.md",
        "docs/Second.md",
    }


def test_missing_roadmap_phase_reference_fails(tmp_path: Path) -> None:
    """A status phase not defined in the roadmap produces an error."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 1 — Foundation\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "Phase 2 – Core Platform Services (Ready to Begin)\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "status-phase-not-in-roadmap"
        and issue.severity is ValidationSeverity.ERROR
        and issue.line_number == 3
        for issue in result.issues
    )


def test_phase_name_mismatch_produces_warning(tmp_path: Path) -> None:
    """Different phase names for the same phase produce a warning."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 5 — Validation Services\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "Phase 5 – Semantic Knowledge Services (Ready to Begin)\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert len(result.issues) == 1
    assert result.issues[0].code == "phase-name-mismatch"
    assert result.issues[0].severity is ValidationSeverity.WARNING


def test_missing_roadmap_phase_headings_fails(tmp_path: Path) -> None:
    """A roadmap without phase headings produces an error."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "No implementation phase headings are defined.\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "Phase 1 – Foundation: Completed\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "roadmap-phases-not-found"
    assert result.issues[0].repository_path == (
        "docs/platform/Implementation_Roadmap.md"
    )


def test_missing_status_phase_references_produces_warning(
    tmp_path: Path,
) -> None:
    """A status document without phase references produces a warning."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 1 — Foundation\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "No phase has started.\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert len(result.issues) == 1
    assert result.issues[0].code == "status-phases-not-found"
    assert result.issues[0].repository_path == (
        "docs/platform/Implementation_Status.md"
    )


def test_duplicate_status_phase_reference_is_not_repeated(
    tmp_path: Path,
) -> None:
    """Duplicate identical status phase references are checked once."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 1 — Foundation\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "Phase 1 – Foundation (Completed)\n"
            "- ✅ Phase 1 – Foundation: Completed\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_hyphen_variants_are_supported(tmp_path: Path) -> None:
    """Em dash, en dash, and hyphen phase separators are accepted."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 1 - Foundation\n\n"
            "## Phase 2 – Core Platform Services\n\n"
            "## Phase 3 — Repository Knowledge Services\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "Phase 1 — Foundation: Completed\n"
            "Phase 2 - Core Platform Services: Completed\n"
            "Phase 3 – Repository Knowledge Services (Ready to Begin)\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_phase_name_comparison_is_case_insensitive(
    tmp_path: Path,
) -> None:
    """Phase names are compared without regard to letter case."""

    _write_required_documents(
        tmp_path,
        roadmap_content=(
            "# Implementation Roadmap\n\n"
            "## Phase 5 — Validation Services\n"
        ),
        status_content=(
            "# Implementation Status\n\n"
            "Phase 5 – VALIDATION SERVICES (Ready to Begin)\n"
        ),
    )

    validator = DocumentationConsistencyValidator(tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_missing_roadmap_or_status_skips_cross_document_check(
    tmp_path: Path,
) -> None:
    """Missing implementation documents are handled by required checks."""

    validator = DocumentationConsistencyValidator(
        repository_root=tmp_path,
        required_document_paths=(
            "docs/platform/Implementation_Roadmap.md",
            "docs/platform/Implementation_Status.md",
        ),
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 2
    assert all(
        issue.code == "required-document-missing"
        for issue in result.issues
    )
