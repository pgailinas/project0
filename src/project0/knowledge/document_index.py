# ============================================================
# Project0 - Document Index
#
# File: document_index.py
#
# Purpose:
#     Store and retrieve parsed repository documents for
#     deterministic Project0 knowledge services.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from project0.models.knowledge_models import DocumentRecord


class DocumentIndex:
    """Store parsed repository documents by repository-relative path."""

    def __init__(self) -> None:
        """Initialize an empty document index."""

        self._documents: dict[Path, DocumentRecord] = {}

    def build_index(
        self,
        documents: Sequence[DocumentRecord],
    ) -> None:
        """Build or replace the document index."""

        indexed_documents: dict[Path, DocumentRecord] = {}

        for document in documents:
            if document.path in indexed_documents:
                raise ValueError(
                    "Duplicate document path encountered: "
                    f"{document.path}"
                )

            indexed_documents[document.path] = document

        self._documents = indexed_documents

    def get_document(
        self,
        path: Path,
    ) -> DocumentRecord | None:
        """Return an indexed document by repository-relative path."""

        return self._documents.get(path)

    def list_documents(self) -> tuple[DocumentRecord, ...]:
        """Return all indexed documents in path order."""

        return tuple(
            self._documents[path]
            for path in sorted(
                self._documents,
                key=lambda document_path: document_path.as_posix(),
            )
        )

    def contains_document(
        self,
        path: Path,
    ) -> bool:
        """Return whether a document path exists in the index."""

        return path in self._documents

    def document_count(self) -> int:
        """Return the number of indexed documents."""

        return len(self._documents)

    def clear(self) -> None:
        """Remove all documents from the index."""

        self._documents.clear()
