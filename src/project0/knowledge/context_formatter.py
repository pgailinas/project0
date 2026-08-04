# ============================================================
# Project0 - Context Formatter
#
# File: context_formatter.py
#
# Purpose:
#     Format selected repository documents into deterministic
#     context text for Project0 knowledge services.
#
# ============================================================

from __future__ import annotations

from typing import Sequence

from project0.models.knowledge_models import DocumentRecord


class ContextFormatter:
    """Format selected repository documents as context text."""

    def format_documents(
        self,
        documents: Sequence[DocumentRecord],
    ) -> str:
        """Format selected documents in their supplied order."""

        context_sections = tuple(
            self._format_document(document)
            for document in documents
        )

        return "\n\n".join(context_sections)

    def _format_document(
        self,
        document: DocumentRecord,
    ) -> str:
        """Format one selected document."""

        return (
            f"--- Document: {document.path.as_posix()} ---\n"
            f"Title: {document.title}\n\n"
            f"{document.content.strip()}"
        )
