# ============================================================
# Project0 - Research Context Ingestion Service
#
# File: research_context_ingestion_service.py
#
# Purpose:
#     Ingest and normalize existing research context documents
#     for Research Agent workflows.
#
# ============================================================

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from project0.models.research_models import (
    ResearchContextDocument,
    ResearchContextDocumentType,
    ResearchContextExtractionStatus,
)


class ResearchContextIngestionService:
    """Ingest and normalize existing research context documents."""

    def ingest(
        self,
        source_name: str,
        content: bytes,
    ) -> ResearchContextDocument:
        """Ingest and normalize an existing research document."""

        if not content:
            raise ValueError(
                "Research context document content must not be empty."
            )

        suffix = Path(source_name).suffix.lower()

        if suffix in {".md", ".markdown"}:
            return self._ingest_text_document(
                source_name=source_name,
                content=content,
                document_type=ResearchContextDocumentType.MARKDOWN,
            )

        if suffix == ".txt":
            return self._ingest_text_document(
                source_name=source_name,
                content=content,
                document_type=ResearchContextDocumentType.TEXT,
            )

        if suffix == ".pdf":
            return self._ingest_pdf_document(
                source_name=source_name,
                content=content,
            )

        raise ValueError(
            "Unsupported research context document type: "
            f"{suffix or '<none>'}"
        )

    def _ingest_text_document(
        self,
        *,
        source_name: str,
        content: bytes,
        document_type: ResearchContextDocumentType,
    ) -> ResearchContextDocument:
        """Decode and normalize a text-based research context document."""

        try:
            extracted_text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                "Research context text must be valid UTF-8."
            ) from error

        if not extracted_text.strip():
            raise ValueError(
                "Research context document contains no meaningful text."
            )

        return ResearchContextDocument(
            source_name=source_name,
            document_type=document_type,
            extraction_method="utf-8",
            extracted_text=extracted_text,
            extraction_status=ResearchContextExtractionStatus.COMPLETED,
        )

    def _ingest_pdf_document(
        self,
        *,
        source_name: str,
        content: bytes,
    ) -> ResearchContextDocument:
        """Extract and normalize text from a PDF research context document."""

        try:
            reader = PdfReader(BytesIO(content))
            page_text = [
                page.extract_text() or ""
                for page in reader.pages
            ]
        except Exception as error:
            raise ValueError(
                "Research context PDF could not be parsed."
            ) from error

        extracted_text = "\n\n".join(
            text
            for text in page_text
            if text.strip()
        )

        if not extracted_text.strip():
            raise ValueError(
                "Research context PDF contains no meaningful "
                "extractable text."
            )

        return ResearchContextDocument(
            source_name=source_name,
            document_type=ResearchContextDocumentType.PDF,
            extraction_method="pypdf",
            extracted_text=extracted_text,
            extraction_status=ResearchContextExtractionStatus.COMPLETED,
            page_count=len(reader.pages),
        )
