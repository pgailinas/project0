# ============================================================
# Project0 - Document Selector Tests
#
# File: test_document_selector.py
#
# Purpose:
#     Verify deterministic selection and ranking of repository
#     documents for Project0 knowledge requests.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.knowledge.document_selector import DocumentSelector
from project0.models.knowledge_models import (
    DocumentHeading,
    DocumentRecord,
    KnowledgeRequest,
)


def create_document(
    path: str,
    title: str,
    content: str | None = None,
    tags: tuple[str, ...] = (),
    headings: tuple[DocumentHeading, ...] = (),
) -> DocumentRecord:
    """Create a document record for testing."""

    return DocumentRecord(
        path=Path(path),
        title=title,
        content=content or f"# {title}\n",
        tags=tags,
        headings=headings,
    )


def test_select_documents_returns_empty_selection() -> None:
    """Verify an empty selection when no documents match."""

    selector = DocumentSelector()

    request = KnowledgeRequest(
        query="unmatched topic",
        include_baseline_documents=False,
    )

    selection = selector.select_documents(
        request=request,
        documents=(),
    )

    assert selection.documents == ()
    assert selection.references == ()
    assert selection.excluded_paths == ()
    assert selection.warnings == ()


def test_select_documents_selects_requested_path() -> None:
    """Verify selection of an explicitly requested document."""

    document = create_document(
        "docs/Documentation_Agent_Design.md",
        "Documentation Agent Design",
    )

    request = KnowledgeRequest(
        query="Retrieve the design document.",
        requested_paths=(document.path,),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.documents == (document,)
    assert selection.references[0].path == document.path
    assert selection.references[0].score == 120.0
    assert selection.references[0].matched_terms == (
        "design",
        "document",
    )
    assert (
        selection.references[0].reason
        == "Explicitly requested document."
    )


def test_select_documents_warns_for_missing_requested_path() -> None:
    """Verify warning creation for a missing requested document."""

    request = KnowledgeRequest(
        query="Retrieve a missing document.",
        requested_paths=(Path("docs/Missing.md"),),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(),
    )

    assert selection.documents == ()
    assert selection.references == ()
    assert selection.warnings == (
        "Requested document was not found: docs/Missing.md",
    )


def test_select_documents_matches_required_tag() -> None:
    """Verify selection using a required document tag."""

    matching_document = create_document(
        "docs/Architecture.md",
        "Architecture",
        tags=("architecture", "design"),
    )

    other_document = create_document(
        "docs/Charter.md",
        "Charter",
        tags=("project",),
    )

    request = KnowledgeRequest(
        query="Find architecture information.",
        required_tags=("architecture",),
        search_terms=("term-not-present",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(
            other_document,
            matching_document,
        ),
    )

    assert selection.documents == (matching_document,)
    assert selection.references[0].score == 20.0
    assert selection.references[0].matched_terms == (
        "architecture",
    )


def test_select_documents_matches_tags_case_insensitively() -> None:
    """Verify case-insensitive tag matching."""

    document = create_document(
        "docs/Architecture.md",
        "Architecture",
        tags=("Architecture",),
    )

    request = KnowledgeRequest(
        query="Find architecture information.",
        required_tags=("architecture",),
        search_terms=("term-not-present",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.documents == (document,)


def test_select_documents_matches_explicit_search_term() -> None:
    """Verify selection using an explicit search term."""

    document = create_document(
        "docs/Repository_Service.md",
        "Repository Service",
        content="# Repository Service\n\nProvides file access.",
    )

    request = KnowledgeRequest(
        query="Retrieve service information.",
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.documents == (document,)
    assert selection.references[0].score == 10.0
    assert selection.references[0].matched_terms == (
        "repository",
    )


def test_select_documents_matches_term_in_heading() -> None:
    """Verify matching against extracted heading titles."""

    heading = DocumentHeading(
        level=2,
        title="Component Communication",
        line_number=5,
        anchor="component-communication",
    )

    document = create_document(
        "docs/Design.md",
        "Design",
        content="# Design\n",
        headings=(heading,),
    )

    request = KnowledgeRequest(
        query="Find communication details.",
        search_terms=("communication",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.documents == (document,)


def test_select_documents_uses_query_terms_when_search_terms_empty() -> None:
    """Verify deterministic term extraction from the request query."""

    document = create_document(
        "docs/Workflow_Engine.md",
        "Workflow Engine",
    )

    request = KnowledgeRequest(
        query="Retrieve workflow details.",
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.documents == (document,)
    assert "workflow" in selection.references[0].matched_terms


def test_select_documents_matches_changed_path_terms() -> None:
    """Verify matching using terms derived from changed paths."""

    document = create_document(
        "docs/Repository_Design.md",
        "Repository Design",
        content="# Repository Design\n",
    )

    request = KnowledgeRequest(
        query="Update affected documentation.",
        search_terms=("term-not-present",),
        changed_paths=(
            Path(
                "src/project0/repository/"
                "repository_service.py"
            ),
        ),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.documents == (document,)
    assert selection.references[0].score == 5.0
    assert selection.references[0].matched_terms == (
        "src/project0/repository/repository_service.py",
    )


def test_select_documents_adds_matching_scores() -> None:
    """Verify accumulation of multiple deterministic scores."""

    document = create_document(
        "docs/Repository_Architecture.md",
        "Repository Architecture",
        content="# Repository Architecture\n",
        tags=("architecture",),
    )

    request = KnowledgeRequest(
        query="Find repository architecture.",
        required_tags=("architecture",),
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.references[0].score == 30.0
    assert selection.references[0].matched_terms == (
        "architecture",
        "repository",
    )


def test_select_documents_preserves_explicit_reason() -> None:
    """Verify explicit selection reason remains authoritative."""

    document = create_document(
        "docs/Architecture.md",
        "Architecture",
        tags=("architecture",),
    )

    request = KnowledgeRequest(
        query="Find architecture.",
        requested_paths=(document.path,),
        required_tags=("architecture",),
        search_terms=("architecture",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    reference = selection.references[0]

    assert reference.reason == "Explicitly requested document."
    assert reference.score == 130.0
    assert reference.matched_terms == (
        "architecture",
    )


def test_select_documents_includes_baseline_documents() -> None:
    """Verify selection of standard baseline project documents."""

    charter = create_document(
        "docs/Project_Charter.md",
        "Project Charter",
    )

    standards = create_document(
        "docs/Documentation_Standards.md",
        "Documentation Standards",
    )

    unrelated = create_document(
        "docs/Unrelated.md",
        "Unrelated",
    )

    request = KnowledgeRequest(
        query="term not present anywhere",
        search_terms=("term-not-present",),
        include_baseline_documents=True,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(
            unrelated,
            standards,
            charter,
        ),
    )

    assert selection.documents == (
        standards,
        charter,
    )

    assert all(
        reference.reason == "Baseline project document."
        for reference in selection.references
    )


def test_select_documents_does_not_duplicate_baseline_match() -> None:
    """Verify a matched baseline document is selected only once."""

    charter = create_document(
        "docs/Project_Charter.md",
        "Project Charter",
        tags=("project",),
    )

    request = KnowledgeRequest(
        query="Find project information.",
        required_tags=("project",),
        search_terms=("term-not-present",),
        include_baseline_documents=True,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(charter,),
    )

    assert selection.documents == (charter,)
    assert len(selection.references) == 1
    assert selection.references[0].score == 20.0


def test_select_documents_orders_by_score() -> None:
    """Verify documents are ordered by descending relevance score."""

    low_score_document = create_document(
        "docs/Low.md",
        "Repository Notes",
        content="# Repository Notes\n",
    )

    high_score_document = create_document(
        "docs/High.md",
        "Repository Architecture",
        content="# Repository Architecture\n",
        tags=("architecture",),
    )

    request = KnowledgeRequest(
        query="Find repository architecture.",
        required_tags=("architecture",),
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(
            low_score_document,
            high_score_document,
        ),
    )

    assert selection.documents == (
        high_score_document,
        low_score_document,
    )


def test_select_documents_uses_path_order_for_equal_scores() -> None:
    """Verify path ordering when relevance scores are equal."""

    second_document = create_document(
        "docs/Zulu.md",
        "Repository Zulu",
    )

    first_document = create_document(
        "docs/Alpha.md",
        "Repository Alpha",
    )

    request = KnowledgeRequest(
        query="Find repository information.",
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(
            second_document,
            first_document,
        ),
    )

    assert selection.documents == (
        first_document,
        second_document,
    )


def test_select_documents_applies_maximum_documents() -> None:
    """Verify enforcement of the maximum document limit."""

    first_document = create_document(
        "docs/First.md",
        "Repository First",
    )

    second_document = create_document(
        "docs/Second.md",
        "Repository Second",
    )

    request = KnowledgeRequest(
        query="Find repository information.",
        search_terms=("repository",),
        maximum_documents=1,
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(
            second_document,
            first_document,
        ),
    )

    assert selection.documents == (first_document,)
    assert len(selection.references) == 1
    assert selection.excluded_paths == (
        second_document.path,
    )


def test_select_documents_lists_unselected_paths() -> None:
    """Verify deterministic reporting of excluded document paths."""

    selected_document = create_document(
        "docs/Selected.md",
        "Repository Selected",
    )

    second_excluded = create_document(
        "docs/Zulu.md",
        "Zulu",
    )

    first_excluded = create_document(
        "docs/Alpha.md",
        "Alpha",
    )

    request = KnowledgeRequest(
        query="Find repository information.",
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(
            second_excluded,
            selected_document,
            first_excluded,
        ),
    )

    assert selection.documents == (selected_document,)
    assert selection.excluded_paths == (
        first_excluded.path,
        second_excluded.path,
    )


def test_select_documents_deduplicates_matched_terms() -> None:
    """Verify duplicate matched terms are reported only once."""

    document = create_document(
        "docs/Architecture.md",
        "Architecture",
        content="# Architecture\n",
        tags=("architecture",),
    )

    request = KnowledgeRequest(
        query="Find architecture.",
        required_tags=("architecture",),
        search_terms=("architecture",),
        include_baseline_documents=False,
    )

    selector = DocumentSelector()

    selection = selector.select_documents(
        request=request,
        documents=(document,),
    )

    assert selection.references[0].matched_terms == (
        "architecture",
    )
