# ============================================================
# Project0 - Document Parser Tests
#
# File: test_document_parser.py
#
# Purpose:
#     Verify deterministic parsing of repository Markdown
#     documents into shared Project0 knowledge models.
#
# ============================================================

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from project0.knowledge.document_parser import DocumentParser


def test_parse_document_creates_document_record(
    tmp_path: Path,
) -> None:
    """Verify parsing of a basic Markdown document."""

    document_path = tmp_path / "docs" / "Example.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "# Example Document\n\n"
        "This is example content.\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Example.md")
    )

    assert record.path == Path("docs/Example.md")
    assert record.title == "Example Document"
    assert record.content == (
        "# Example Document\n\n"
        "This is example content.\n"
    )
    assert record.modified_at is not None
    assert record.content_hash is not None
    assert record.metadata["suffix"] == ".md"
    assert record.metadata["size_bytes"] > 0


def test_parse_document_accepts_absolute_path(
    tmp_path: Path,
) -> None:
    """Verify parsing with an absolute repository document path."""

    document_path = tmp_path / "docs" / "Absolute.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "# Absolute Document\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(document_path)

    assert record.path == Path("docs/Absolute.md")
    assert record.title == "Absolute Document"


def test_parse_document_extracts_headings(
    tmp_path: Path,
) -> None:
    """Verify extraction of Markdown headings."""

    document_path = tmp_path / "docs" / "Headings.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "# Main Title\n\n"
        "## Architecture\n\n"
        "### Component Design\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Headings.md")
    )

    assert len(record.headings) == 3

    assert record.headings[0].level == 1
    assert record.headings[0].title == "Main Title"
    assert record.headings[0].line_number == 1
    assert record.headings[0].anchor == "main-title"

    assert record.headings[1].level == 2
    assert record.headings[1].title == "Architecture"
    assert record.headings[1].line_number == 3
    assert record.headings[1].anchor == "architecture"

    assert record.headings[2].level == 3
    assert record.headings[2].title == "Component Design"
    assert record.headings[2].line_number == 5
    assert record.headings[2].anchor == "component-design"


def test_parse_document_removes_closing_heading_markers(
    tmp_path: Path,
) -> None:
    """Verify removal of optional closing heading markers."""

    document_path = tmp_path / "docs" / "Closing_Markers.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "## Design Overview ##\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Closing_Markers.md")
    )

    assert record.headings[0].title == "Design Overview"
    assert record.headings[0].anchor == "design-overview"


def test_parse_document_extracts_internal_link(
    tmp_path: Path,
) -> None:
    """Verify extraction of a repository-local Markdown link."""

    document_path = tmp_path / "docs" / "Internal_Link.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "# Internal Link\n\n"
        "[Architecture](Documentation_Agent_Architecture.md)\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Internal_Link.md")
    )

    assert len(record.links) == 1
    assert record.links[0].text == "Architecture"
    assert (
        record.links[0].target
        == "Documentation_Agent_Architecture.md"
    )
    assert record.links[0].line_number == 3
    assert record.links[0].is_internal is True


@pytest.mark.parametrize(
    "target",
    (
        "https://example.com",
        "http://example.com",
        "mailto:test@example.com",
    ),
)
def test_parse_document_identifies_external_links(
    tmp_path: Path,
    target: str,
) -> None:
    """Verify identification of supported external link types."""

    document_path = tmp_path / "docs" / "External_Link.md"
    document_path.parent.mkdir()
    document_path.write_text(
        f"# External Link\n\n[External]({target})\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/External_Link.md")
    )

    assert len(record.links) == 1
    assert record.links[0].target == target
    assert record.links[0].is_internal is False


def test_parse_document_extracts_multiple_links_on_one_line(
    tmp_path: Path,
) -> None:
    """Verify extraction of multiple links from one line."""

    document_path = tmp_path / "docs" / "Multiple_Links.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "# Links\n\n"
        "[First](First.md) and [Second](Second.md)\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Multiple_Links.md")
    )

    assert len(record.links) == 2
    assert record.links[0].text == "First"
    assert record.links[0].target == "First.md"
    assert record.links[1].text == "Second"
    assert record.links[1].target == "Second.md"


def test_parse_document_uses_first_level_one_heading_as_title(
    tmp_path: Path,
) -> None:
    """Verify title selection from the first level-one heading."""

    document_path = tmp_path / "docs" / "Title.md"
    document_path.parent.mkdir()
    document_path.write_text(
        "## Preliminary Section\n\n"
        "# Authoritative Title\n\n"
        "# Later Title\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Title.md")
    )

    assert record.title == "Authoritative Title"


def test_parse_document_uses_filename_when_heading_missing(
    tmp_path: Path,
) -> None:
    """Verify title generation from a filename without headings."""

    document_path = (
        tmp_path
        / "docs"
        / "Component_Communication-Design.md"
    )
    document_path.parent.mkdir()
    document_path.write_text(
        "Document content without headings.\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Component_Communication-Design.md")
    )

    assert record.title == "Component Communication Design"


def test_parse_document_generates_content_hash(
    tmp_path: Path,
) -> None:
    """Verify generation of the SHA-256 content hash."""

    content = "# Hash Test\n\nContent used for hashing.\n"

    document_path = tmp_path / "docs" / "Hash_Test.md"
    document_path.parent.mkdir()
    document_path.write_text(
        content,
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Hash_Test.md")
    )

    expected_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    assert record.content_hash == expected_hash


def test_parse_document_records_file_size(
    tmp_path: Path,
) -> None:
    """Verify inclusion of the source file size."""

    content = "# Size Test\n"

    document_path = tmp_path / "docs" / "Size_Test.md"
    document_path.parent.mkdir()
    document_path.write_text(
        content,
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    record = parser.parse_document(
        Path("docs/Size_Test.md")
    )

    assert record.metadata["size_bytes"] == len(
        content.encode("utf-8")
    )


def test_parse_document_raises_for_missing_file(
    tmp_path: Path,
) -> None:
    """Verify rejection of a missing document."""

    parser = DocumentParser(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match="Document does not exist",
    ):
        parser.parse_document(
            Path("docs/Missing.md")
        )


def test_parse_document_raises_for_directory(
    tmp_path: Path,
) -> None:
    """Verify rejection of a directory path."""

    directory_path = tmp_path / "docs"
    directory_path.mkdir()

    parser = DocumentParser(tmp_path)

    with pytest.raises(
        ValueError,
        match="Document path is not a file",
    ):
        parser.parse_document(Path("docs"))


def test_parse_document_raises_for_non_markdown_file(
    tmp_path: Path,
) -> None:
    """Verify rejection of unsupported file types."""

    document_path = tmp_path / "docs" / "Example.txt"
    document_path.parent.mkdir()
    document_path.write_text(
        "Unsupported document.",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    with pytest.raises(
        ValueError,
        match="supports Markdown files only",
    ):
        parser.parse_document(
            Path("docs/Example.txt")
        )


def test_parse_document_raises_for_relative_path_escape(
    tmp_path: Path,
) -> None:
    """Verify rejection of a relative path outside the repository."""

    external_path = tmp_path.parent / "Outside.md"
    external_path.write_text(
        "# Outside Repository\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    with pytest.raises(
        ValueError,
        match="outside the repository root",
    ):
        parser.parse_document(
            Path("../Outside.md")
        )


def test_parse_document_raises_for_external_absolute_path(
    tmp_path: Path,
) -> None:
    """Verify rejection of an absolute path outside the repository."""

    external_directory = tmp_path.parent / "external"
    external_directory.mkdir(exist_ok=True)

    external_path = external_directory / "External.md"
    external_path.write_text(
        "# External Document\n",
        encoding="utf-8",
    )

    parser = DocumentParser(tmp_path)

    with pytest.raises(
        ValueError,
        match="outside the repository root",
    ):
        parser.parse_document(external_path)


