# ============================================================
# Project0 - Knowledge Service
#
# File: knowledge_service.py
#
# Purpose:
#     Coordinate repository document discovery, parsing,
#     indexing, selection, and context assembly.
#
# ============================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

from project0.knowledge.context_formatter import ContextFormatter
from project0.knowledge.document_index import DocumentIndex
from project0.knowledge.document_parser import DocumentParser
from project0.knowledge.document_selector import DocumentSelector
from project0.models.knowledge_models import (
    DocumentRecord,
    KnowledgeRequest,
    KnowledgeResult,
)


class KnowledgeService:
    """Build deterministic repository knowledge results."""

    def __init__(
        self,
        repository_root: Path,
        parser: DocumentParser | None = None,
        index: DocumentIndex | None = None,
        selector: DocumentSelector | None = None,
        formatter: ContextFormatter | None = None,
    ) -> None:
        """Initialize the knowledge service and its dependencies."""

        self._repository_root = repository_root.resolve()
        self._parser = parser or DocumentParser(
            self._repository_root
        )
        self._index = index or DocumentIndex()
        self._selector = selector or DocumentSelector()
        self._formatter = formatter or ContextFormatter()

    def build_knowledge(
        self,
        request: KnowledgeRequest,
    ) -> KnowledgeResult:
        """Build repository knowledge for a request."""

        document_paths = self._discover_document_paths()
        documents, parsing_warnings = self._parse_documents(
            document_paths
        )

        self._index.build_index(documents)

        selection = self._selector.select_documents(
            request=request,
            documents=self._index.list_documents(),
        )

        context = self._formatter.format_documents(
            selection.documents
        )

        warnings = (
            *parsing_warnings,
            *selection.warnings,
        )

        return KnowledgeResult(
            request_id=request.request_id,
            query=request.query,
            selection=selection,
            context=context,
            created_at=datetime.now(),
            context_metadata={
                "indexed_document_count": (
                    self._index.document_count()
                ),
                "selected_document_count": len(
                    selection.documents
                ),
                "repository_root": str(
                    self._repository_root
                ),
            },
            warnings=warnings,
        )

    def _discover_document_paths(
        self,
    ) -> tuple[Path, ...]:
        """Discover repository Markdown documents."""

        docs_directory = self._repository_root / "docs"

        if not docs_directory.exists():
            raise FileNotFoundError(
                f"Documentation directory does not exist: "
                f"{docs_directory}"
            )

        if not docs_directory.is_dir():
            raise ValueError(
                f"Documentation path is not a directory: "
                f"{docs_directory}"
            )

        return tuple(
            path.relative_to(self._repository_root)
            for path in sorted(
                docs_directory.rglob("*.md"),
                key=lambda item: item.as_posix(),
            )
            if path.is_file()
        )

    def _parse_documents(
        self,
        document_paths: Sequence[Path],
    ) -> tuple[
        tuple[DocumentRecord, ...],
        tuple[str, ...],
    ]:
        """Parse discovered documents and collect warnings."""

        documents: list[DocumentRecord] = []
        warnings: list[str] = []

        for path in document_paths:
            try:
                document = self._parser.parse_document(path)
            except (OSError, UnicodeError, ValueError) as error:
                warnings.append(
                    f"Document could not be parsed: "
                    f"{path}: {error}"
                )
                continue

            documents.append(document)

        return (
            tuple(documents),
            tuple(warnings),
        )
