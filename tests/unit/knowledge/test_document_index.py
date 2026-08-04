# ============================================================
# Project0 - Document Index Tests
#
# File: test_document_index.py
#
# Purpose:
#     Verify deterministic storage and retrieval of parsed
#     repository documents in the Project0 document index.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

import pytest

from project0.knowledge.document_index import DocumentIndex
from project0.models.knowledge_models import DocumentRecord


def create_document(
    path: str,
    title: str,
) -> DocumentRecord:
    """Create a document record for testing."""

    return DocumentRecord(
        path=Path(path),
        title=title,
        content=f"# {title}\n",
    )


def test_document_index_starts_empty() -> None:
    """Verify initialization of an empty document index."""

    index = DocumentIndex()

    assert index.document_count() == 0
    assert index.list_documents() == ()


def test_build_index_stores_documents() -> None:
    """Verify storage of parsed documents."""

    first_document = create_document(
        "docs/Project_Charter.md",
        "Project Charter",
    )

    second_document = create_document(
        "docs/Documentation_Standards.md",
        "Documentation Standards",
    )

    index = DocumentIndex()

    index.build_index(
        (
            first_document,
            second_document,
        )
    )

    assert index.document_count() == 2
    assert index.contains_document(first_document.path)
    assert index.contains_document(second_document.path)


def test_build_index_replaces_existing_documents() -> None:
    """Verify rebuilding replaces the existing index."""

    original_document = create_document(
        "docs/Original.md",
        "Original",
    )

    replacement_document = create_document(
        "docs/Replacement.md",
        "Replacement",
    )

    index = DocumentIndex()

    index.build_index((original_document,))
    index.build_index((replacement_document,))

    assert index.document_count() == 1
    assert index.contains_document(original_document.path) is False
    assert index.contains_document(replacement_document.path) is True


def test_build_index_accepts_empty_sequence() -> None:
    """Verify rebuilding with no documents clears the index."""

    document = create_document(
        "docs/Example.md",
        "Example",
    )

    index = DocumentIndex()

    index.build_index((document,))
    index.build_index(())

    assert index.document_count() == 0
    assert index.list_documents() == ()


def test_build_index_rejects_duplicate_paths() -> None:
    """Verify rejection of duplicate document paths."""

    first_document = create_document(
        "docs/Example.md",
        "First Example",
    )

    second_document = create_document(
        "docs/Example.md",
        "Second Example",
    )

    index = DocumentIndex()

    with pytest.raises(
        ValueError,
        match="Duplicate document path encountered",
    ):
        index.build_index(
            (
                first_document,
                second_document,
            )
        )


def test_failed_build_does_not_replace_existing_index() -> None:
    """Verify a failed rebuild preserves the current index."""

    existing_document = create_document(
        "docs/Existing.md",
        "Existing",
    )

    duplicate_one = create_document(
        "docs/Duplicate.md",
        "Duplicate One",
    )

    duplicate_two = create_document(
        "docs/Duplicate.md",
        "Duplicate Two",
    )

    index = DocumentIndex()
    index.build_index((existing_document,))

    with pytest.raises(ValueError):
        index.build_index(
            (
                duplicate_one,
                duplicate_two,
            )
        )

    assert index.document_count() == 1
    assert index.get_document(existing_document.path) == existing_document


def test_get_document_returns_matching_document() -> None:
    """Verify retrieval of a document by path."""

    document = create_document(
        "docs/Documentation_Agent_Design.md",
        "Documentation Agent Design",
    )

    index = DocumentIndex()
    index.build_index((document,))

    result = index.get_document(document.path)

    assert result == document


def test_get_document_returns_none_for_unknown_path() -> None:
    """Verify retrieval of an unknown document path."""

    index = DocumentIndex()

    result = index.get_document(
        Path("docs/Missing.md")
    )

    assert result is None


def test_list_documents_returns_path_order() -> None:
    """Verify documents are returned in deterministic path order."""

    third_document = create_document(
        "docs/Zulu.md",
        "Zulu",
    )

    first_document = create_document(
        "docs/Alpha.md",
        "Alpha",
    )

    second_document = create_document(
        "docs/Middle.md",
        "Middle",
    )

    index = DocumentIndex()

    index.build_index(
        (
            third_document,
            first_document,
            second_document,
        )
    )

    documents = index.list_documents()

    assert documents == (
        first_document,
        second_document,
        third_document,
    )


def test_list_documents_returns_tuple() -> None:
    """Verify indexed documents are returned as a tuple."""

    document = create_document(
        "docs/Example.md",
        "Example",
    )

    index = DocumentIndex()
    index.build_index((document,))

    documents = index.list_documents()

    assert isinstance(documents, tuple)


def test_contains_document_returns_true_for_known_path() -> None:
    """Verify detection of an indexed document."""

    document = create_document(
        "docs/Project_Charter.md",
        "Project Charter",
    )

    index = DocumentIndex()
    index.build_index((document,))

    assert index.contains_document(document.path) is True


def test_contains_document_returns_false_for_unknown_path() -> None:
    """Verify detection of an unknown document."""

    index = DocumentIndex()

    assert (
        index.contains_document(
            Path("docs/Unknown.md")
        )
        is False
    )


def test_document_count_returns_number_of_documents() -> None:
    """Verify the indexed document count."""

    first_document = create_document(
        "docs/First.md",
        "First",
    )

    second_document = create_document(
        "docs/Second.md",
        "Second",
    )

    index = DocumentIndex()

    index.build_index(
        (
            first_document,
            second_document,
        )
    )

    assert index.document_count() == 2


def test_clear_removes_all_documents() -> None:
    """Verify removal of all indexed documents."""

    first_document = create_document(
        "docs/First.md",
        "First",
    )

    second_document = create_document(
        "docs/Second.md",
        "Second",
    )

    index = DocumentIndex()

    index.build_index(
        (
            first_document,
            second_document,
        )
    )

    index.clear()

    assert index.document_count() == 0
    assert index.list_documents() == ()
    assert index.contains_document(first_document.path) is False
    assert index.contains_document(second_document.path) is False


def test_clear_empty_index_is_safe() -> None:
    """Verify clearing an empty index does not fail."""

    index = DocumentIndex()

    index.clear()

    assert index.document_count() == 0
    assert index.list_documents() == ()
