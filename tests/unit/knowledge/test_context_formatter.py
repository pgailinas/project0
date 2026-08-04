# ============================================================
# Project0 - Context Formatter Tests
#
# File: test_context_formatter.py
#
# Purpose:
#     Verify deterministic formatting of selected repository
#     documents for Project0 knowledge services.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.knowledge.context_formatter import ContextFormatter
from project0.models.knowledge_models import DocumentRecord


def create_document(
    path: str,
    title: str,
    content: str,
) -> DocumentRecord:
    """Create a document record for testing."""

    return DocumentRecord(
        path=Path(path),
        title=title,
        content=content,
    )


def test_format_documents_returns_empty_string() -> None:
    """Verify empty document input produces empty context."""

    formatter = ContextFormatter()

    context = formatter.format_documents(())

    assert context == ""


def test_format_documents_formats_single_document() -> None:
    """Verify formatting of one selected document."""

    document = create_document(
        "docs/Project_Charter.md",
        "Project Charter",
        "# Project Charter\n\nProject purpose.\n",
    )

    formatter = ContextFormatter()

    context = formatter.format_documents((document,))

    assert context == (
        "--- Document: docs/Project_Charter.md ---\n"
        "Title: Project Charter\n\n"
        "# Project Charter\n\n"
        "Project purpose."
    )


def test_format_documents_formats_multiple_documents() -> None:
    """Verify formatting and separation of multiple documents."""

    first_document = create_document(
        "docs/First.md",
        "First",
        "# First\n\nFirst content.\n",
    )

    second_document = create_document(
        "docs/Second.md",
        "Second",
        "# Second\n\nSecond content.\n",
    )

    formatter = ContextFormatter()

    context = formatter.format_documents(
        (
            first_document,
            second_document,
        )
    )

    assert context == (
        "--- Document: docs/First.md ---\n"
        "Title: First\n\n"
        "# First\n\n"
        "First content.\n\n"
        "--- Document: docs/Second.md ---\n"
        "Title: Second\n\n"
        "# Second\n\n"
        "Second content."
    )


def test_format_documents_preserves_input_order() -> None:
    """Verify documents remain in their supplied order."""

    second_document = create_document(
        "docs/Second.md",
        "Second",
        "# Second\n",
    )

    first_document = create_document(
        "docs/First.md",
        "First",
        "# First\n",
    )

    formatter = ContextFormatter()

    context = formatter.format_documents(
        (
            second_document,
            first_document,
        )
    )

    second_position = context.index(
        "--- Document: docs/Second.md ---"
    )
    first_position = context.index(
        "--- Document: docs/First.md ---"
    )

    assert second_position < first_position


def test_format_documents_strips_outer_content_whitespace() -> None:
    """Verify outer document whitespace is removed."""

    document = create_document(
        "docs/Whitespace.md",
        "Whitespace",
        "\n\n# Whitespace\n\nContent.\n\n",
    )

    formatter = ContextFormatter()

    context = formatter.format_documents((document,))

    assert context.endswith("Content.")
    assert not context.endswith("\n")
    assert (
        "Title: Whitespace\n\n# Whitespace"
        in context
    )


def test_format_documents_preserves_internal_whitespace() -> None:
    """Verify internal document spacing remains unchanged."""

    document = create_document(
        "docs/Spacing.md",
        "Spacing",
        "# Spacing\n\n"
        "First paragraph.\n\n\n"
        "Second paragraph.\n",
    )

    formatter = ContextFormatter()

    context = formatter.format_documents((document,))

    assert (
        "First paragraph.\n\n\nSecond paragraph."
        in context
    )


def test_format_documents_preserves_markdown_and_unicode() -> None:
    """Verify Markdown and Unicode content remains intact."""

    document = create_document(
        "docs/Special.md",
        "Special — Design",
        "# Special — Design\n\n"
        "- **Bold item**\n"
        "- `code_value`\n"
        "- Café\n",
    )

    formatter = ContextFormatter()

    context = formatter.format_documents((document,))

    assert "Title: Special — Design" in context
    assert "- **Bold item**" in context
    assert "- `code_value`" in context
    assert "- Café" in context


def test_format_documents_is_deterministic() -> None:
    """Verify repeated formatting produces identical output."""

    document = create_document(
        "docs/Deterministic.md",
        "Deterministic",
        "# Deterministic\n\nStable content.\n",
    )

    formatter = ContextFormatter()

    first_context = formatter.format_documents((document,))
    second_context = formatter.format_documents((document,))

    assert first_context == second_context


def test_format_documents_does_not_modify_documents() -> None:
    """Verify formatting does not mutate document records."""

    document = create_document(
        "docs/Immutable.md",
        "Immutable",
        "\n# Immutable\n",
    )

    original_content = document.content
    original_title = document.title
    original_path = document.path

    formatter = ContextFormatter()

    formatter.format_documents((document,))

    assert document.content == original_content
    assert document.title == original_title
    assert document.path == original_path
