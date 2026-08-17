# ============================================================
# Project0 - Markdown Locator Tests
#
# File: test_markdown_locator.py
#
# Purpose:
#     Validate Markdown artifact location discovery behavior
#     used by Project0 artifact understanding capabilities.
#
# ============================================================

from pathlib import Path

from project0.artifacts.markdown_locator import MarkdownLocator
from project0.models.artifact_models import ArtifactLocationType


def _create_markdown_document(
    tmp_path: Path,
) -> Path:
    """Create a sample Markdown artifact for testing."""

    document = tmp_path / "sample.md"

    document.write_text(
        """# Document Title

Introduction content.

## Workflow

Step one.

Step two.

## Validation

Validation content.
""",
        encoding="utf-8",
    )

    return document


def test_markdown_locator_finds_sections(
    tmp_path: Path,
) -> None:
    """Markdown sections are discovered from headings."""

    document = _create_markdown_document(tmp_path)

    locator = MarkdownLocator()

    locations = locator.locate_sections(document)

    assert len(locations) == 3

    assert locations[0].locator == "Document Title"
    assert locations[1].locator == "Workflow"
    assert locations[2].locator == "Validation"


def test_markdown_locator_generates_line_ranges(
    tmp_path: Path,
) -> None:
    """Discovered sections include valid line ranges."""

    document = _create_markdown_document(tmp_path)

    locator = MarkdownLocator()

    locations = locator.locate_sections(document)

    workflow_location = locations[1]

    assert workflow_location.start_line is not None
    assert workflow_location.end_line is not None
    assert (
        workflow_location.start_line
        <= workflow_location.end_line
    )


def test_markdown_locator_generates_content_hash(
    tmp_path: Path,
) -> None:
    """Discovered locations include content hashes."""

    document = _create_markdown_document(tmp_path)

    locator = MarkdownLocator()

    locations = locator.locate_sections(document)

    workflow_location = locations[1]

    assert workflow_location.content_hash is not None
    assert len(workflow_location.content_hash) > 0


def test_markdown_locator_identifies_section_locations(
    tmp_path: Path,
) -> None:
    """Discovered Markdown locations are section locations."""

    document = _create_markdown_document(tmp_path)

    locator = MarkdownLocator()

    locations = locator.locate_sections(document)

    assert all(
        location.location_type
        == ArtifactLocationType.SECTION
        for location in locations
    )


def test_markdown_locator_handles_empty_document(
    tmp_path: Path,
) -> None:
    """Empty Markdown artifacts produce no locations."""

    document = tmp_path / "empty.md"
    document.write_text(
        "",
        encoding="utf-8",
    )

    locator = MarkdownLocator()

    locations = locator.locate_sections(document)

    assert locations == ()
