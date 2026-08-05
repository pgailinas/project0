# ============================================================
# Project0 - Markdown Validator Tests
#
# File: test_markdown_validator.py
#
# Purpose:
#     Verify deterministic Markdown structure validation used
#     by Project0 validation components.
#
# ============================================================

from pathlib import Path

from project0.models.validation_models import (
    ValidationSeverity,
    ValidationStatus,
)
from project0.validation.markdown_validator import MarkdownValidator
from project0.models.validation_models import ValidationRequest


def test_valid_markdown_document_passes(tmp_path: Path) -> None:
    """A valid Markdown document passes validation."""

    document = tmp_path / "docs" / "valid.md"
    document.parent.mkdir()
    document.write_text(
        "# Valid Document\n\n"
        "## Purpose\n\n"
        "Content.\n\n"
        "### Details\n\n"
        "More content.\n",
        encoding="utf-8",
    )

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/valid.md",))

    result = validator.validate(request)

    assert result.validator_name == "markdown"
    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()
    assert result.error_message is None


def test_empty_markdown_document_fails(tmp_path: Path) -> None:
    """An empty Markdown document produces an error."""

    document = tmp_path / "docs" / "empty.md"
    document.parent.mkdir()
    document.write_text("", encoding="utf-8")

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/empty.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "empty-document"
    assert result.issues[0].severity is ValidationSeverity.ERROR
    assert result.issues[0].repository_path == "docs/empty.md"


def test_missing_document_title_fails(tmp_path: Path) -> None:
    """A Markdown document without a level-one heading fails."""

    document = tmp_path / "docs" / "missing_title.md"
    document.parent.mkdir()
    document.write_text(
        "## Purpose\n\n"
        "Content.\n",
        encoding="utf-8",
    )

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/missing_title.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "missing-document-title"
        and issue.severity is ValidationSeverity.ERROR
        for issue in result.issues
    )


def test_multiple_document_titles_produce_warning(tmp_path: Path) -> None:
    """Additional level-one headings produce warnings."""

    document = tmp_path / "docs" / "multiple_titles.md"
    document.parent.mkdir()
    document.write_text(
        "# First Title\n\n"
        "Content.\n\n"
        "# Second Title\n",
        encoding="utf-8",
    )

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/multiple_titles.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert len(result.issues) == 1
    assert result.issues[0].code == "multiple-document-titles"
    assert result.issues[0].line_number == 5


def test_duplicate_heading_produces_warning(tmp_path: Path) -> None:
    """Duplicate headings are reported case-insensitively."""

    document = tmp_path / "docs" / "duplicate.md"
    document.parent.mkdir()
    document.write_text(
        "# Document\n\n"
        "## Purpose\n\n"
        "Content.\n\n"
        "## purpose\n",
        encoding="utf-8",
    )

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/duplicate.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert any(
        issue.code == "duplicate-heading"
        and issue.line_number == 7
        for issue in result.issues
    )


def test_heading_level_skip_produces_warning(tmp_path: Path) -> None:
    """A skipped heading level is reported as a warning."""

    document = tmp_path / "docs" / "heading_skip.md"
    document.parent.mkdir()
    document.write_text(
        "# Document\n\n"
        "### Details\n",
        encoding="utf-8",
    )

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/heading_skip.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert any(
        issue.code == "heading-level-skip"
        and issue.line_number == 3
        for issue in result.issues
    )


def test_headings_inside_fenced_code_are_ignored(tmp_path: Path) -> None:
    """Heading-like text inside fenced code blocks is not validated."""

    document = tmp_path / "docs" / "fenced.md"
    document.parent.mkdir()
    document.write_text(
        "# Document\n\n"
        "```text\n"
        "# Example Title\n"
        "### Example Heading\n"
        "```\n",
        encoding="utf-8",
    )

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/fenced.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_missing_markdown_file_fails(tmp_path: Path) -> None:
    """A missing Markdown target produces a file-not-found error."""

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/missing.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "file-not-found"
    assert result.issues[0].severity is ValidationSeverity.ERROR


def test_path_outside_repository_fails(tmp_path: Path) -> None:
    """A target outside the repository root is rejected."""

    outside_document = tmp_path.parent / "outside.md"
    outside_document.write_text("# Outside\n", encoding="utf-8")

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("../outside.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "path-outside-repository"


def test_non_markdown_target_is_ignored(tmp_path: Path) -> None:
    """Non-Markdown targets are ignored by the Markdown validator."""

    target = tmp_path / "config.toml"
    target.write_text("[project]\n", encoding="utf-8")

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(target_paths=("config.toml",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_multiple_targets_combine_issues(tmp_path: Path) -> None:
    """Issues from multiple Markdown targets are combined."""

    valid_document = tmp_path / "docs" / "valid.md"
    invalid_document = tmp_path / "docs" / "invalid.md"
    valid_document.parent.mkdir()

    valid_document.write_text("# Valid\n", encoding="utf-8")
    invalid_document.write_text("## Missing Title\n", encoding="utf-8")

    validator = MarkdownValidator(tmp_path)
    request = ValidationRequest(
        target_paths=(
            "docs/valid.md",
            "docs/invalid.md",
        )
    )

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].repository_path == "docs/invalid.md"
    assert result.issues[0].code == "missing-document-title"
