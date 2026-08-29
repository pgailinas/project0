# ============================================================
# Project0 - Research Paper Ingestion Service
#
# File: research_paper_ingestion_service.py
#
# Purpose:
#     Extract and normalize page-preserving full-text PDF
#     content for retained Research Agent papers.
#
# ============================================================

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from project0.models.research_models import (
    ResearchPaperAcquisition,
    ResearchPaperAcquisitionStatus,
    ResearchPaperDocument,
    ResearchPaperDocumentType,
    ResearchPaperExtractionStatus,
    ResearchPaperPage,
)


class ResearchPaperIngestionService:
    """Extract and normalize acquired full-text research papers."""

    def ingest(
        self,
        acquisition: ResearchPaperAcquisition,
    ) -> ResearchPaperDocument:
        """Extract and normalize one acquired research paper."""

        if (
            acquisition.acquisition_status
            != ResearchPaperAcquisitionStatus.ACQUIRED
        ):
            raise ValueError(
                "Research paper content must be acquired before ingestion."
            )

        if acquisition.content is None:
            raise ValueError(
                "Acquired research paper content must not be empty."
            )

        if not acquisition.content:
            raise ValueError(
                "Acquired research paper content must not be empty."
            )

        if acquisition.source_url is None:
            raise ValueError(
                "Acquired research paper source URL must be provided."
            )

        try:
            reader = PdfReader(
                BytesIO(acquisition.content)
            )

            pages = tuple(
                ResearchPaperPage(
                    page_number=page_number,
                    text=page.extract_text() or "",
                )
                for page_number, page in enumerate(
                    reader.pages,
                    start=1,
                )
            )
        except Exception as error:
            raise ValueError(
                "Research paper PDF could not be parsed."
            ) from error

        if not any(
            page.text.strip()
            for page in pages
        ):
            raise ValueError(
                "Research paper PDF contains no meaningful "
                "extractable text."
            )

        empty_page_numbers = tuple(
            page.page_number
            for page in pages
            if not page.text.strip()
        )

        warnings = list(
            acquisition.warnings
        )

        extraction_status = (
            ResearchPaperExtractionStatus.COMPLETED
        )

        if empty_page_numbers:
            warnings.append(
                "Research paper PDF contained pages without "
                "extractable text: "
                + ", ".join(
                    str(page_number)
                    for page_number in empty_page_numbers
                )
                + "."
            )

            extraction_status = (
                ResearchPaperExtractionStatus.COMPLETED_WITH_WARNINGS
            )

        return ResearchPaperDocument(
            paper=acquisition.paper,
            source_url=acquisition.source_url,
            document_type=ResearchPaperDocumentType.PDF,
            extraction_method="pypdf",
            pages=pages,
            extraction_status=extraction_status,
            warnings=tuple(warnings),
        )
