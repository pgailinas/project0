# ============================================================
# Project0 - Link Validator Tests
#
# File: test_link_validator.py
#
# Purpose:
#     Verify deterministic repository-relative link validation
#     used by Project0 validation components.
#
# ============================================================

from pathlib import Path

from project0.models.validation_models import (
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
)
from project0.validation.link_validator import LinkValidator


def test_valid_relative_file_link_passes(tmp_path: Path) -> None:
    """A valid repository-relative file link passes validation."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = docs_dir / "Architecture.md"

    source.write_text(
        "# Home\n\n"
        "[Architecture](Architecture.md)\n",
        encoding="utf-8",
    )
    target.write_text("# Architecture\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.validator_name == "link"
    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()
    assert result.error_message is None


def test_valid_repository_root_link_passes(tmp_path: Path) -> None:
    """A valid root-relative repository link passes validation."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = tmp_path / "README.md"

    source.write_text(
        "# Home\n\n"
        "[README](/README.md)\n",
        encoding="utf-8",
    )
    target.write_text("# Project0\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_valid_same_document_fragment_passes(tmp_path: Path) -> None:
    """A valid fragment in the current document passes validation."""

    document = tmp_path / "docs" / "index.md"
    document.parent.mkdir()

    document.write_text(
        "# Home\n\n"
        "[Purpose](#purpose)\n\n"
        "## Purpose\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_valid_linked_document_fragment_passes(tmp_path: Path) -> None:
    """A valid fragment in another Markdown document passes validation."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = docs_dir / "Architecture.md"

    source.write_text(
        "# Home\n\n"
        "[Components](Architecture.md#architectural-components)\n",
        encoding="utf-8",
    )
    target.write_text(
        "# Architecture\n\n"
        "## Architectural Components\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_missing_link_target_fails(tmp_path: Path) -> None:
    """A missing local link target produces an error."""

    document = tmp_path / "docs" / "index.md"
    document.parent.mkdir()

    document.write_text(
        "# Home\n\n"
        "[Missing](Missing.md)\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "missing-link-target"
    assert result.issues[0].severity is ValidationSeverity.ERROR
    assert result.issues[0].repository_path == "docs/index.md"
    assert result.issues[0].line_number == 3


def test_missing_fragment_produces_warning(tmp_path: Path) -> None:
    """A missing Markdown heading fragment produces a warning."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = docs_dir / "Architecture.md"

    source.write_text(
        "# Home\n\n"
        "[Missing Section](Architecture.md#missing-section)\n",
        encoding="utf-8",
    )
    target.write_text("# Architecture\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert len(result.issues) == 1
    assert result.issues[0].code == "missing-link-fragment"
    assert result.issues[0].severity is ValidationSeverity.WARNING


def test_external_links_are_ignored(tmp_path: Path) -> None:
    """Supported external link schemes are not validated locally."""

    document = tmp_path / "docs" / "index.md"
    document.parent.mkdir()

    document.write_text(
        "# Home\n\n"
        "[Website](https://example.com)\n"
        "[Email](mailto:test@example.com)\n"
        "[Phone](tel:+15555555555)\n"
        "[FTP](ftp://example.com/file.txt)\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_image_target_is_validated(tmp_path: Path) -> None:
    """A local Markdown image target is validated."""

    docs_dir = tmp_path / "docs"
    images_dir = docs_dir / "images"
    images_dir.mkdir(parents=True)

    document = docs_dir / "index.md"
    image = images_dir / "diagram.png"

    document.write_text(
        "# Home\n\n"
        "![Diagram](images/diagram.png)\n",
        encoding="utf-8",
    )
    image.write_bytes(b"image")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_encoded_link_path_passes(tmp_path: Path) -> None:
    """A URL-encoded local path is decoded before validation."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = docs_dir / "Project Notes.md"

    source.write_text(
        "# Home\n\n"
        "[Notes](Project%20Notes.md)\n",
        encoding="utf-8",
    )
    target.write_text("# Project Notes\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_link_title_is_ignored(tmp_path: Path) -> None:
    """An optional Markdown link title is not treated as part of the path."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = docs_dir / "Architecture.md"

    source.write_text(
        "# Home\n\n"
        '[Architecture](Architecture.md "Architecture document")\n',
        encoding="utf-8",
    )
    target.write_text("# Architecture\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_links_inside_fenced_code_are_ignored(tmp_path: Path) -> None:
    """Link-like text inside fenced code blocks is ignored."""

    document = tmp_path / "docs" / "index.md"
    document.parent.mkdir()

    document.write_text(
        "# Home\n\n"
        "```markdown\n"
        "[Missing](Missing.md)\n"
        "```\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_link_outside_repository_fails(tmp_path: Path) -> None:
    """A local link resolving outside the repository is rejected."""

    outside_file = tmp_path.parent / "outside.md"
    outside_file.write_text("# Outside\n", encoding="utf-8")

    document = tmp_path / "docs" / "index.md"
    document.parent.mkdir()

    document.write_text(
        "# Home\n\n"
        "[Outside](../../outside.md)\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "link-outside-repository"


def test_missing_source_markdown_file_fails(tmp_path: Path) -> None:
    """A missing source Markdown target produces an error."""

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/missing.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "file-not-found"


def test_source_path_outside_repository_fails(tmp_path: Path) -> None:
    """A source target outside the repository root is rejected."""

    outside_document = tmp_path.parent / "outside.md"
    outside_document.write_text("# Outside\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("../outside.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "path-outside-repository"


def test_non_markdown_target_is_ignored(tmp_path: Path) -> None:
    """Non-Markdown validation targets are ignored."""

    target = tmp_path / "config.toml"
    target.write_text("[project]\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("config.toml",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_multiple_source_documents_combine_issues(tmp_path: Path) -> None:
    """Issues from multiple source documents are combined."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    first = docs_dir / "first.md"
    second = docs_dir / "second.md"

    first.write_text(
        "# First\n\n"
        "[Missing One](missing-one.md)\n",
        encoding="utf-8",
    )
    second.write_text(
        "# Second\n\n"
        "[Missing Two](missing-two.md)\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(
        target_paths=(
            "docs/first.md",
            "docs/second.md",
        )
    )

    result = validator.validate(request)

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 2
    assert {
        issue.repository_path
        for issue in result.issues
    } == {
        "docs/first.md",
        "docs/second.md",
    }


def test_duplicate_heading_fragments_are_numbered(tmp_path: Path) -> None:
    """Duplicate Markdown headings use numbered fragments."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    source = docs_dir / "index.md"
    target = docs_dir / "target.md"

    source.write_text(
        "# Home\n\n"
        "[Second Purpose](target.md#purpose-1)\n",
        encoding="utf-8",
    )
    target.write_text(
        "# Target\n\n"
        "## Purpose\n\n"
        "## Purpose\n",
        encoding="utf-8",
    )

    validator = LinkValidator(tmp_path)
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()
