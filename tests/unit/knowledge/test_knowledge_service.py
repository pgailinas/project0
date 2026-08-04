# ============================================================
# Project0 - Knowledge Service Tests
#
# File: test_knowledge_service.py
#
# Purpose:
#     Verify deterministic repository knowledge orchestration
#     for Project0 knowledge requests.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

import pytest

from project0.knowledge.document_index import DocumentIndex
from project0.knowledge.knowledge_service import KnowledgeService
from project0.models.knowledge_models import (
    DocumentRecord,
    DocumentReference,
    DocumentSelection,
    KnowledgeRequest,
)


class StubParser:
    """Provide deterministic parser behavior for testing."""

    def __init__(
        self,
        records: dict[Path, DocumentRecord],
        errors: dict[Path, Exception] | None = None,
    ) -> None:
        """Initialize parser results and errors."""

        self.records = records
        self.errors = errors or {}
        self.parsed_paths: list[Path] = []

    def parse_document(
        self,
        path: Path,
    ) -> DocumentRecord:
        """Return a configured document record or error."""

        self.parsed_paths.append(path)

        if path in self.errors:
            raise self.errors[path]

        return self.records[path]


class StubSelector:
    """Provide deterministic selector behavior for testing."""

    def __init__(
        self,
        selection: DocumentSelection,
    ) -> None:
        """Initialize the configured selection result."""

        self.selection = selection
        self.requests: list[KnowledgeRequest] = []
        self.document_sets: list[
            tuple[DocumentRecord, ...]
        ] = []

    def select_documents(
        self,
        request: KnowledgeRequest,
        documents: tuple[DocumentRecord, ...],
    ) -> DocumentSelection:
        """Return the configured selection result."""

        self.requests.append(request)
        self.document_sets.append(tuple(documents))

        return self.selection


class StubFormatter:
    """Provide deterministic context formatting for testing."""

    def __init__(
        self,
        context: str,
    ) -> None:
        """Initialize the configured context result."""

        self.context = context
        self.document_sets: list[
            tuple[DocumentRecord, ...]
        ] = []

    def format_documents(
        self,
        documents: tuple[DocumentRecord, ...],
    ) -> str:
        """Return the configured formatted context."""

        self.document_sets.append(tuple(documents))

        return self.context


def create_document(
    path: str,
    title: str,
    content: str | None = None,
) -> DocumentRecord:
    """Create a document record for testing."""

    return DocumentRecord(
        path=Path(path),
        title=title,
        content=content or f"# {title}\n",
    )


def create_markdown_file(
    repository_root: Path,
    relative_path: str,
    content: str,
) -> Path:
    """Create a repository Markdown file for testing."""

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


def test_build_knowledge_with_real_dependencies(
    tmp_path: Path,
) -> None:
    """Verify complete knowledge construction."""

    create_markdown_file(
        tmp_path,
        "docs/Project_Charter.md",
        "# Project Charter\n\nProject purpose.\n",
    )

    create_markdown_file(
        tmp_path,
        "docs/Documentation_Standards.md",
        "# Documentation Standards\n\nMarkdown rules.\n",
    )

    request = KnowledgeRequest(
        query="Retrieve the project charter.",
        requested_paths=(
            Path("docs/Project_Charter.md"),
        ),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert result.request_id == request.request_id
    assert result.query == request.query
    assert result.selection.documents[0].path == Path(
        "docs/Project_Charter.md"
    )
    assert (
        "--- Document: docs/Project_Charter.md ---"
        in result.context
    )
    assert "Title: Project Charter" in result.context
    assert "# Project Charter" in result.context
    assert result.context_metadata[
        "indexed_document_count"
    ] == 2
    assert result.context_metadata[
        "selected_document_count"
    ] == 1
    assert result.context_metadata[
        "repository_root"
    ] == str(tmp_path.resolve())
    assert result.created_at is not None
    assert result.warnings == ()


def test_build_knowledge_discovers_nested_documents(
    tmp_path: Path,
) -> None:
    """Verify recursive discovery of Markdown documents."""

    create_markdown_file(
        tmp_path,
        "docs/architecture/Nested.md",
        "# Nested Architecture\n",
    )

    request = KnowledgeRequest(
        query="Find nested architecture.",
        requested_paths=(
            Path("docs/architecture/Nested.md"),
        ),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert result.context_metadata[
        "indexed_document_count"
    ] == 1
    assert result.selection.documents[0].path == Path(
        "docs/architecture/Nested.md"
    )


def test_build_knowledge_ignores_non_markdown_files(
    tmp_path: Path,
) -> None:
    """Verify discovery excludes unsupported file types."""

    create_markdown_file(
        tmp_path,
        "docs/Included.md",
        "# Included\n",
    )

    text_path = tmp_path / "docs" / "Excluded.txt"
    text_path.write_text(
        "Excluded content.",
        encoding="utf-8",
    )

    request = KnowledgeRequest(
        query="Retrieve included document.",
        requested_paths=(Path("docs/Included.md"),),
        include_baseline_documents=False,
    )

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(request)

    assert result.context_metadata[
        "indexed_document_count"
    ] == 1
    assert result.selection.documents[0].path == Path(
        "docs/Included.md"
    )


def test_build_knowledge_discovers_documents_in_path_order(
    tmp_path: Path,
) -> None:
    """Verify deterministic parser discovery order."""

    first_path = Path("docs/Alpha.md")
    second_path = Path("docs/Zulu.md")

    create_markdown_file(
        tmp_path,
        second_path.as_posix(),
        "# Zulu\n",
    )

    create_markdown_file(
        tmp_path,
        first_path.as_posix(),
        "# Alpha\n",
    )

    first_record = create_document(
        first_path.as_posix(),
        "Alpha",
    )

    second_record = create_document(
        second_path.as_posix(),
        "Zulu",
    )

    parser = StubParser(
        {
            first_path: first_record,
            second_path: second_record,
        }
    )

    selector = StubSelector(
        DocumentSelection(
            documents=(),
            references=(),
        )
    )

    service = KnowledgeService(
        repository_root=tmp_path,
        parser=parser,
        selector=selector,
    )

    service.build_knowledge(
        KnowledgeRequest(
            query="Build repository knowledge.",
            include_baseline_documents=False,
        )
    )

    assert parser.parsed_paths == [
        first_path,
        second_path,
    ]


def test_build_knowledge_uses_injected_dependencies(
    tmp_path: Path,
) -> None:
    """Verify orchestration through injected components."""

    document_path = Path("docs/Injected.md")

    create_markdown_file(
        tmp_path,
        document_path.as_posix(),
        "# Placeholder\n",
    )

    document = create_document(
        document_path.as_posix(),
        "Injected Document",
        "# Injected Document\n\nInjected content.\n",
    )

    parser = StubParser(
        {
            document_path: document,
        }
    )

    reference = DocumentReference(
        path=document.path,
        title=document.title,
        reason="Injected selection.",
        score=10.0,
    )

    selection = DocumentSelection(
        documents=(document,),
        references=(reference,),
        warnings=("Selector warning.",),
    )

    selector = StubSelector(selection)
    formatter = StubFormatter("Formatted context.")
    index = DocumentIndex()

    request = KnowledgeRequest(
        query="Use injected components.",
        include_baseline_documents=False,
    )

    service = KnowledgeService(
        repository_root=tmp_path,
        parser=parser,
        index=index,
        selector=selector,
        formatter=formatter,
    )

    result = service.build_knowledge(request)

    assert parser.parsed_paths == ([
        document_path,
    ])
    assert selector.requests == [request]
    assert selector.document_sets == [
        (document,)
    ]
    assert formatter.document_sets == [
        (document,)
    ]
    assert index.get_document(document_path) == document
    assert result.selection == selection
    assert result.context == "Formatted context."
    assert result.warnings == (
        "Selector warning.",
    )


def test_build_knowledge_collects_parser_warning(
    tmp_path: Path,
) -> None:
    """Verify parser failures become non-fatal warnings."""

    failed_path = Path("docs/Failed.md")
    valid_path = Path("docs/Valid.md")

    create_markdown_file(
        tmp_path,
        failed_path.as_posix(),
        "# Failed\n",
    )

    create_markdown_file(
        tmp_path,
        valid_path.as_posix(),
        "# Valid\n",
    )

    valid_document = create_document(
        valid_path.as_posix(),
        "Valid",
    )

    parser = StubParser(
        records={
            valid_path: valid_document,
        },
        errors={
            failed_path: ValueError("Invalid Markdown."),
        },
    )

    reference = DocumentReference(
        path=valid_document.path,
        title=valid_document.title,
        reason="Selected valid document.",
        score=10.0,
    )

    selector = StubSelector(
        DocumentSelection(
            documents=(valid_document,),
            references=(reference,),
        )
    )

    service = KnowledgeService(
        repository_root=tmp_path,
        parser=parser,
        selector=selector,
    )

    result = service.build_knowledge(
        KnowledgeRequest(
            query="Build knowledge with one failure.",
            include_baseline_documents=False,
        )
    )

    assert result.context_metadata[
        "indexed_document_count"
    ] == 1
    assert result.warnings == (
        "Document could not be parsed: "
        "docs/Failed.md: Invalid Markdown.",
    )


def test_build_knowledge_combines_warning_order(
    tmp_path: Path,
) -> None:
    """Verify parser warnings precede selector warnings."""

    failed_path = Path("docs/Failed.md")

    create_markdown_file(
        tmp_path,
        failed_path.as_posix(),
        "# Failed\n",
    )

    parser = StubParser(
        records={},
        errors={
            failed_path: OSError("Read failure."),
        },
    )

    selector = StubSelector(
        DocumentSelection(
            documents=(),
            references=(),
            warnings=("Selector warning.",),
        )
    )

    service = KnowledgeService(
        repository_root=tmp_path,
        parser=parser,
        selector=selector,
    )

    result = service.build_knowledge(
        KnowledgeRequest(
            query="Build knowledge.",
            include_baseline_documents=False,
        )
    )

    assert result.warnings == (
        "Document could not be parsed: "
        "docs/Failed.md: Read failure.",
        "Selector warning.",
    )


def test_build_knowledge_returns_empty_context_for_empty_selection(
    tmp_path: Path,
) -> None:
    """Verify empty selection produces empty context."""

    create_markdown_file(
        tmp_path,
        "docs/Available.md",
        "# Available\n",
    )

    document = create_document(
        "docs/Available.md",
        "Available",
    )

    parser = StubParser(
        {
            document.path: document,
        }
    )

    selector = StubSelector(
        DocumentSelection(
            documents=(),
            references=(),
            excluded_paths=(document.path,),
        )
    )

    service = KnowledgeService(
        repository_root=tmp_path,
        parser=parser,
        selector=selector,
    )

    result = service.build_knowledge(
        KnowledgeRequest(
            query="Select nothing.",
            include_baseline_documents=False,
        )
    )

    assert result.context == ""
    assert result.context_metadata[
        "selected_document_count"
    ] == 0


def test_build_knowledge_rebuilds_index_each_time(
    tmp_path: Path,
) -> None:
    """Verify each request rebuilds the document index."""

    first_path = Path("docs/First.md")

    create_markdown_file(
        tmp_path,
        first_path.as_posix(),
        "# First\n",
    )

    first_document = create_document(
        first_path.as_posix(),
        "First",
    )

    parser = StubParser(
        {
            first_path: first_document,
        }
    )

    selector = StubSelector(
        DocumentSelection(
            documents=(),
            references=(),
        )
    )

    index = DocumentIndex()

    service = KnowledgeService(
        repository_root=tmp_path,
        parser=parser,
        index=index,
        selector=selector,
    )

    request = KnowledgeRequest(
        query="First build.",
        include_baseline_documents=False,
    )

    service.build_knowledge(request)

    assert index.document_count() == 1

    first_file = tmp_path / first_path
    first_file.unlink()

    second_path = Path("docs/Second.md")

    create_markdown_file(
        tmp_path,
        second_path.as_posix(),
        "# Second\n",
    )

    second_document = create_document(
        second_path.as_posix(),
        "Second",
    )

    parser.records = {
        second_path: second_document,
    }

    service.build_knowledge(
        KnowledgeRequest(
            query="Second build.",
            include_baseline_documents=False,
        )
    )

    assert index.document_count() == 1
    assert index.get_document(first_path) is None
    assert index.get_document(second_path) == second_document


def test_build_knowledge_raises_when_docs_directory_missing(
    tmp_path: Path,
) -> None:
    """Verify rejection when the docs directory is absent."""

    service = KnowledgeService(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match="Documentation directory does not exist",
    ):
        service.build_knowledge(
            KnowledgeRequest(
                query="Build knowledge.",
            )
        )


def test_build_knowledge_raises_when_docs_path_is_file(
    tmp_path: Path,
) -> None:
    """Verify rejection when docs is not a directory."""

    docs_path = tmp_path / "docs"
    docs_path.write_text(
        "Not a directory.",
        encoding="utf-8",
    )

    service = KnowledgeService(tmp_path)

    with pytest.raises(
        ValueError,
        match="Documentation path is not a directory",
    ):
        service.build_knowledge(
            KnowledgeRequest(
                query="Build knowledge.",
            )
        )


def test_build_knowledge_allows_empty_docs_directory(
    tmp_path: Path,
) -> None:
    """Verify empty documentation repositories are supported."""

    (tmp_path / "docs").mkdir()

    service = KnowledgeService(tmp_path)

    result = service.build_knowledge(
        KnowledgeRequest(
            query="Build empty knowledge.",
            include_baseline_documents=False,
        )
    )

    assert result.selection.documents == ()
    assert result.context == ""
    assert result.context_metadata[
        "indexed_document_count"
    ] == 0
    assert result.context_metadata[
        "selected_document_count"
    ] == 0
    assert result.warnings == ()
