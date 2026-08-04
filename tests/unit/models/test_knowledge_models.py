# ============================================================
# Project0 - Knowledge Model Tests
#
# File: test_knowledge_models.py
#
# Purpose:
#     Verify shared repository knowledge data models used by
#     Project0 platform components and AI agents.
#
# ============================================================

from datetime import datetime
from pathlib import Path

from project0.models.knowledge_models import (
    DocumentHeading,
    DocumentLink,
    DocumentRecord,
    DocumentReference,
    DocumentSelection,
    KnowledgeRequest,
    KnowledgeResult,
)


def test_document_heading_creation() -> None:
    """Verify creation of a document heading."""

    heading = DocumentHeading(
        level=2,
        title="Architecture",
        line_number=12,
        anchor="architecture",
    )

    assert heading.level == 2
    assert heading.title == "Architecture"
    assert heading.line_number == 12
    assert heading.anchor == "architecture"


def test_document_heading_default_anchor() -> None:
    """Verify the default document heading anchor."""

    heading = DocumentHeading(
        level=1,
        title="Project0",
        line_number=1,
    )

    assert heading.anchor is None


def test_document_link_creation() -> None:
    """Verify creation of a document link."""

    link = DocumentLink(
        text="Architecture",
        target="Documentation_Agent_Architecture.md",
        line_number=24,
    )

    assert link.text == "Architecture"
    assert link.target == "Documentation_Agent_Architecture.md"
    assert link.line_number == 24
    assert link.is_internal is True


def test_document_link_external_value() -> None:
    """Verify creation of an external document link."""

    link = DocumentLink(
        text="GitHub",
        target="https://github.com",
        line_number=18,
        is_internal=False,
    )

    assert link.is_internal is False


def test_document_record_creation() -> None:
    """Verify creation of a parsed document record."""

    modified_at = datetime(2026, 8, 4, 14, 30)

    heading = DocumentHeading(
        level=1,
        title="Project Charter",
        line_number=1,
        anchor="project-charter",
    )

    link = DocumentLink(
        text="Documentation Standards",
        target="Documentation_Standards.md",
        line_number=10,
    )

    record = DocumentRecord(
        path=Path("docs/Project_Charter.md"),
        title="Project Charter",
        content="# Project Charter\n\nProject0 charter content.",
        headings=(heading,),
        links=(link,),
        tags=("project", "charter"),
        modified_at=modified_at,
        content_hash="test-hash",
        metadata={"document_type": "charter"},
    )

    assert record.path == Path("docs/Project_Charter.md")
    assert record.title == "Project Charter"
    assert record.content.startswith("# Project Charter")
    assert record.headings == (heading,)
    assert record.links == (link,)
    assert record.tags == ("project", "charter")
    assert record.modified_at == modified_at
    assert record.content_hash == "test-hash"
    assert record.metadata == {"document_type": "charter"}


def test_document_record_defaults() -> None:
    """Verify default values for a document record."""

    record = DocumentRecord(
        path=Path("docs/index.md"),
        title="Project0",
        content="# Project0",
    )

    assert record.headings == ()
    assert record.links == ()
    assert record.tags == ()
    assert record.modified_at is None
    assert record.content_hash is None
    assert record.metadata == {}


def test_document_record_metadata_is_independent() -> None:
    """Verify document records receive independent metadata dictionaries."""

    first_record = DocumentRecord(
        path=Path("docs/first.md"),
        title="First",
        content="# First",
    )

    second_record = DocumentRecord(
        path=Path("docs/second.md"),
        title="Second",
        content="# Second",
    )

    assert first_record.metadata is not second_record.metadata


def test_document_reference_creation() -> None:
    """Verify creation of document selection information."""

    reference = DocumentReference(
        path=Path("docs/Documentation_Agent_Design.md"),
        title="Documentation Agent Design",
        reason="Matched the requested knowledge topic.",
        score=8.5,
        matched_terms=("documentation", "design"),
    )

    assert reference.path == Path(
        "docs/Documentation_Agent_Design.md"
    )
    assert reference.title == "Documentation Agent Design"
    assert reference.reason == "Matched the requested knowledge topic."
    assert reference.score == 8.5
    assert reference.matched_terms == ("documentation", "design")


def test_document_reference_defaults() -> None:
    """Verify default values for a document reference."""

    reference = DocumentReference(
        path=Path("docs/index.md"),
        title="Project0",
        reason="Baseline project document.",
    )

    assert reference.score == 0.0
    assert reference.matched_terms == ()


def test_knowledge_request_creation() -> None:
    """Verify creation of a repository knowledge request."""

    request = KnowledgeRequest(
        query="Find documentation related to repository communication.",
        workflow_type="documentation_update",
        requested_paths=(
            Path("docs/Component_Communication_Design.md"),
        ),
        changed_paths=(
            Path("src/project0/repository/repository_service.py"),
        ),
        required_tags=("architecture",),
        search_terms=("repository", "communication"),
        maximum_documents=5,
        include_baseline_documents=False,
    )

    assert request.query == (
        "Find documentation related to repository communication."
    )
    assert request.workflow_type == "documentation_update"
    assert request.requested_paths == (
        Path("docs/Component_Communication_Design.md"),
    )
    assert request.changed_paths == (
        Path("src/project0/repository/repository_service.py"),
    )
    assert request.required_tags == ("architecture",)
    assert request.search_terms == ("repository", "communication")
    assert request.maximum_documents == 5
    assert request.include_baseline_documents is False
    assert request.request_id


def test_knowledge_request_defaults() -> None:
    """Verify default values for a knowledge request."""

    request = KnowledgeRequest(
        query="Retrieve relevant project documentation."
    )

    assert request.workflow_type is None
    assert request.requested_paths == ()
    assert request.changed_paths == ()
    assert request.required_tags == ()
    assert request.search_terms == ()
    assert request.maximum_documents == 10
    assert request.include_baseline_documents is True
    assert request.request_id


def test_knowledge_request_ids_are_unique() -> None:
    """Verify knowledge requests receive unique identifiers."""

    first_request = KnowledgeRequest(query="First request.")
    second_request = KnowledgeRequest(query="Second request.")

    assert first_request.request_id != second_request.request_id


def test_document_selection_creation() -> None:
    """Verify creation of a document selection."""

    record = DocumentRecord(
        path=Path("docs/Documentation_Standards.md"),
        title="Documentation Standards",
        content="# Documentation Standards",
    )

    reference = DocumentReference(
        path=record.path,
        title=record.title,
        reason="Matched the documentation standards topic.",
        score=10.0,
        matched_terms=("documentation", "standards"),
    )

    selection = DocumentSelection(
        documents=(record,),
        references=(reference,),
        excluded_paths=(Path("docs/index.md"),),
        warnings=("One document was excluded.",),
    )

    assert selection.documents == (record,)
    assert selection.references == (reference,)
    assert selection.excluded_paths == (Path("docs/index.md"),)
    assert selection.warnings == ("One document was excluded.",)


def test_document_selection_defaults() -> None:
    """Verify default values for a document selection."""

    selection = DocumentSelection(
        documents=(),
        references=(),
    )

    assert selection.excluded_paths == ()
    assert selection.warnings == ()


def test_knowledge_result_creation() -> None:
    """Verify creation of a repository knowledge result."""

    created_at = datetime(2026, 8, 4, 14, 45)

    record = DocumentRecord(
        path=Path("docs/Documentation_Agent_Architecture.md"),
        title="Documentation Agent Architecture",
        content="# Documentation Agent Architecture",
    )

    reference = DocumentReference(
        path=record.path,
        title=record.title,
        reason="Matched the architecture search term.",
        score=9.0,
        matched_terms=("architecture",),
    )

    selection = DocumentSelection(
        documents=(record,),
        references=(reference,),
    )

    result = KnowledgeResult(
        request_id="request-123",
        query="Retrieve architecture documentation.",
        selection=selection,
        context="# Documentation Agent Architecture",
        created_at=created_at,
        context_metadata={"document_count": 1},
        warnings=(),
    )

    assert result.request_id == "request-123"
    assert result.query == "Retrieve architecture documentation."
    assert result.selection == selection
    assert result.context == "# Documentation Agent Architecture"
    assert result.created_at == created_at
    assert result.context_metadata == {"document_count": 1}
    assert result.warnings == ()


def test_knowledge_result_defaults() -> None:
    """Verify default values for a knowledge result."""

    selection = DocumentSelection(
        documents=(),
        references=(),
    )

    result = KnowledgeResult(
        request_id="request-456",
        query="Retrieve project documentation.",
        selection=selection,
        context="",
        created_at=datetime(2026, 8, 4, 15, 0),
    )

    assert result.context_metadata == {}
    assert result.warnings == ()


def test_knowledge_result_metadata_is_independent() -> None:
    """Verify knowledge results receive independent metadata dictionaries."""

    selection = DocumentSelection(
        documents=(),
        references=(),
    )

    first_result = KnowledgeResult(
        request_id="request-1",
        query="First result.",
        selection=selection,
        context="",
        created_at=datetime(2026, 8, 4, 15, 0),
    )

    second_result = KnowledgeResult(
        request_id="request-2",
        query="Second result.",
        selection=selection,
        context="",
        created_at=datetime(2026, 8, 4, 15, 1),
    )

    assert first_result.context_metadata is not second_result.context_metadata
    
    
