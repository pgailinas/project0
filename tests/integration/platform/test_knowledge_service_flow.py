# ============================================================
# Project0 - Knowledge Service Flow Integration Tests
#
# File: test_knowledge_service_flow.py
#
# Purpose:
#     Verify the complete deterministic repository knowledge
#     flow using real Project0 knowledge components.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.knowledge.knowledge_service import KnowledgeService
from project0.models.knowledge_models import KnowledgeRequest


def create_markdown_file(
    repository_root: Path,
    relative_path: str,
    content: str,
) -> Path:
    """Create a repository Markdown document for testing."""

    document_path = repository_root / relative_path
    document_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    document_path.write_text(
        content,
        encoding="utf-8",
    )

    return document_path


def test_knowledge_service_flow_selects_requested_document(
    tmp_path: Path,
) -> None:
    """Verify the complete explicit document selection flow."""

    create_markdown_file(
        tmp_path,
        "docs/project/Project_Charter.md",
        "# Project Charter\n\n"
        "Defines the Project0 purpose and scope.\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Documentation_Agent_Design.md",
        "# Documentation Agent Design\n\n"
        "Defines the detailed component design.\n",
    )

    request = KnowledgeRequest(
        query="Retrieve the documentation agent design.",
        requested_paths=(
            Path("docs/Documentation_Agent_Design.md"),
        ),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert result.request_id == request.request_id
    assert result.query == request.query
    assert len(result.selection.documents) == 1

    selected_document = result.selection.documents[0]
    selected_reference = result.selection.references[0]

    assert selected_document.path == Path(
        "docs/Documentation_Agent_Design.md"
    )
    assert selected_document.title == (
        "Documentation Agent Design"
    )
    assert selected_reference.path == selected_document.path
    assert (
        selected_reference.reason
        == "Explicitly requested document."
    )
    assert selected_reference.score >= 100.0
    assert (
        "--- Document: "
        "docs/Documentation_Agent_Design.md ---"
        in result.context
    )
    assert "Title: Documentation Agent Design" in result.context
    assert "Defines the detailed component design." in result.context
    assert result.context_metadata[
        "indexed_document_count"
    ] == 2
    assert result.context_metadata[
        "selected_document_count"
    ] == 1
    assert result.warnings == ()


def test_knowledge_service_flow_selects_by_search_term(
    tmp_path: Path,
) -> None:
    """Verify search-term selection through the complete flow."""

    create_markdown_file(
        tmp_path,
        "docs/Repository_Architecture.md",
        "# Repository Architecture\n\n"
        "Defines repository access and file operations.\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Workflow_Design.md",
        "# Workflow Design\n\n"
        "Defines workflow execution behavior.\n",
    )

    request = KnowledgeRequest(
        query="Find repository information.",
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert len(result.selection.documents) == 1
    assert result.selection.documents[0].path == Path(
        "docs/Repository_Architecture.md"
    )
    assert result.selection.references[0].matched_terms == (
        "repository",
    )
    assert "Repository Architecture" in result.context
    assert "Workflow Design" not in result.context


def test_knowledge_service_flow_uses_query_terms(
    tmp_path: Path,
) -> None:
    """Verify query-derived matching through the complete flow."""

    create_markdown_file(
        tmp_path,
        "docs/Component_Communication_Design.md",
        "# Component Communication Design\n\n"
        "Defines communication between platform components.\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Development_Environment.md",
        "# Development Environment\n\n"
        "Defines local development tools.\n",
    )

    request = KnowledgeRequest(
        query="Retrieve component communication details.",
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert len(result.selection.documents) == 1
    assert result.selection.documents[0].path == Path(
        "docs/Component_Communication_Design.md"
    )
    assert "component" in (
        term.casefold()
        for term in result.selection.references[0].matched_terms
    )
    assert "communication" in (
        term.casefold()
        for term in result.selection.references[0].matched_terms
    )


def test_knowledge_service_flow_includes_baseline_documents(
    tmp_path: Path,
) -> None:
    """Verify baseline document inclusion through the complete flow."""

    charter = create_markdown_file(
        tmp_path,
        "docs/project/Project_Charter.md",
        "# Project Charter\n\n"
        "Defines the project purpose.\n",
    )

    standards = create_markdown_file(
        tmp_path,
        "docs/project/Documentation_Standards.md",
        "# Documentation Standards\n\n"
        "Defines Markdown documentation rules.\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Unrelated.md",
        "# Unrelated\n\n"
        "Contains unrelated information.\n",
    )

    request = KnowledgeRequest(
        query="No matching search topic.",
        search_terms=("term-not-present",),
        include_baseline_documents=True,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    selected_paths = tuple(
        document.path
        for document in result.selection.documents
    )

    assert selected_paths == (
        standards.relative_to(tmp_path),
        charter.relative_to(tmp_path),
    )
    assert all(
        reference.reason == "Baseline project document."
        for reference in result.selection.references
    )
    assert "Documentation Standards" in result.context
    assert "Project Charter" in result.context
    assert "Unrelated" not in result.context


def test_knowledge_service_flow_applies_document_limit(
    tmp_path: Path,
) -> None:
    """Verify maximum document enforcement through the flow."""

    create_markdown_file(
        tmp_path,
        "docs/Alpha_Repository.md",
        "# Alpha Repository\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Beta_Repository.md",
        "# Beta Repository\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Gamma_Repository.md",
        "# Gamma Repository\n",
    )

    request = KnowledgeRequest(
        query="Find repository documents.",
        search_terms=("repository",),
        maximum_documents=2,
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    selected_paths = tuple(
        document.path
        for document in result.selection.documents
    )

    assert selected_paths == (
        Path("docs/Alpha_Repository.md"),
        Path("docs/Beta_Repository.md"),
    )
    assert result.selection.excluded_paths == (
        Path("docs/Gamma_Repository.md"),
    )
    assert result.context_metadata[
        "selected_document_count"
    ] == 2


def test_knowledge_service_flow_reports_missing_requested_document(
    tmp_path: Path,
) -> None:
    """Verify missing requested documents produce warnings."""

    create_markdown_file(
        tmp_path,
        "docs/Available.md",
        "# Available\n",
    )

    request = KnowledgeRequest(
        query="Retrieve missing document.",
        requested_paths=(Path("docs/Missing.md"),),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert result.selection.documents == ()
    assert result.context == ""
    assert result.warnings == (
        "Requested document was not found: docs/Missing.md",
    )
    assert result.context_metadata[
        "indexed_document_count"
    ] == 1
    assert result.context_metadata[
        "selected_document_count"
    ] == 0


def test_knowledge_service_flow_rebuilds_after_repository_change(
    tmp_path: Path,
) -> None:
    """Verify repository changes are reflected on the next request."""

    first_document = create_markdown_file(
        tmp_path,
        "docs/First.md",
        "# First Document\n\nInitial content.\n",
    )

    service = KnowledgeService(tmp_path)

    first_result = service.build_knowledge(
        KnowledgeRequest(
            query="Retrieve first document.",
            requested_paths=(Path("docs/First.md"),),
            include_baseline_documents=False,
        )
    )

    assert first_result.context_metadata[
        "indexed_document_count"
    ] == 1
    assert "Initial content." in first_result.context

    first_document.unlink()

    create_markdown_file(
        tmp_path,
        "docs/Second.md",
        "# Second Document\n\nReplacement content.\n",
    )

    second_result = service.build_knowledge(
        KnowledgeRequest(
            query="Retrieve second document.",
            requested_paths=(Path("docs/Second.md"),),
            include_baseline_documents=False,
        )
    )

    assert second_result.context_metadata[
        "indexed_document_count"
    ] == 1
    assert second_result.selection.documents[0].path == Path(
        "docs/Second.md"
    )
    assert "Replacement content." in second_result.context
    assert "Initial content." not in second_result.context


def test_knowledge_service_flow_preserves_document_order(
    tmp_path: Path,
) -> None:
    """Verify selected documents appear in ranked context order."""

    create_markdown_file(
        tmp_path,
        "docs/Repository_Notes.md",
        "# Repository Notes\n\n"
        "General repository information.\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Repository_Architecture.md",
        "# Repository Architecture\n\n"
        "Detailed repository architecture.\n",
    )

    request = KnowledgeRequest(
        query="Retrieve repository architecture.",
        required_tags=("architecture",),
        search_terms=("repository",),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    selected_paths = tuple(
        document.path
        for document in result.selection.documents
    )

    assert selected_paths == (
        Path("docs/Repository_Architecture.md"),
        Path("docs/Repository_Notes.md"),
    )

    architecture_position = result.context.index(
        "--- Document: docs/Repository_Architecture.md ---"
    )
    notes_position = result.context.index(
        "--- Document: docs/Repository_Notes.md ---"
    )

    assert architecture_position < notes_position
