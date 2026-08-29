# ============================================================
# Project0 - Research Paper Ingestion Service Tests
#
# File: test_research_paper_ingestion_service.py
#
# Purpose:
#     Verify retained research paper PDF extraction,
#     page preservation, normalization, and error handling.
#
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

import pytest

from project0.agents.research import research_paper_ingestion_service
from project0.agents.research.research_paper_ingestion_service import (
    ResearchPaperIngestionService,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchPaperAcquisition,
    ResearchPaperAcquisitionStatus,
    ResearchPaperDocumentType,
    ResearchPaperExtractionStatus,
    ResearchSourceReference,
)


def create_paper() -> PaperMetadata:
    """Create retained paper metadata for ingestion tests."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="paper-001",
        title="Example Paper",
        source_url="https://example.test/paper",
    )

    return PaperMetadata(
        source_reference=reference,
        title="Example Paper",
        source_url="https://example.test/paper",
    )


def create_acquisition(
    *,
    status: ResearchPaperAcquisitionStatus = (
        ResearchPaperAcquisitionStatus.ACQUIRED
    ),
    source_url: str | None = "https://example.test/paper.pdf",
    content: bytes | None = b"%PDF-example",
    warnings: tuple[str, ...] = (),
) -> ResearchPaperAcquisition:
    """Create retained research paper acquisition data."""

    return ResearchPaperAcquisition(
        paper=create_paper(),
        source_url=source_url,
        content=content,
        acquisition_status=status,
        content_type="application/pdf",
        warnings=warnings,
    )


def test_pdf_document_is_ingested_with_page_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify PDF text is extracted while preserving page boundaries."""

    pages = (
        SimpleNamespace(extract_text=lambda: "First page."),
        SimpleNamespace(extract_text=lambda: "Second page."),
    )

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    acquisition = create_acquisition()

    result = ResearchPaperIngestionService().ingest(
        acquisition
    )

    assert result.paper is acquisition.paper
    assert result.source_url == "https://example.test/paper.pdf"
    assert result.document_type == ResearchPaperDocumentType.PDF
    assert result.extraction_method == "pypdf"
    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == "First page."
    assert result.pages[1].page_number == 2
    assert result.pages[1].text == "Second page."
    assert (
        result.extraction_status
        == ResearchPaperExtractionStatus.COMPLETED
    )
    assert result.warnings == ()
    assert result.document_id


def test_pdf_page_numbers_preserve_empty_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify empty PDF pages retain their original page numbers."""

    pages = (
        SimpleNamespace(extract_text=lambda: "First page."),
        SimpleNamespace(extract_text=lambda: None),
        SimpleNamespace(extract_text=lambda: "Third page."),
    )

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    result = ResearchPaperIngestionService().ingest(
        create_acquisition()
    )

    assert len(result.pages) == 3
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert result.pages[1].text == ""
    assert result.pages[2].page_number == 3
    assert result.pages[2].text == "Third page."
    assert (
        result.extraction_status
        == ResearchPaperExtractionStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.warnings == (
        "Research paper PDF contained pages without extractable text: 2.",
    )


def test_acquisition_warnings_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify acquisition warnings remain attached to the document."""

    pages = (
        SimpleNamespace(extract_text=lambda: "Paper text."),
    )

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    result = ResearchPaperIngestionService().ingest(
        create_acquisition(
            warnings=(
                "Acquisition fallback was used.",
            ),
        )
    )

    assert result.warnings == (
        "Acquisition fallback was used.",
    )
    assert (
        result.extraction_status
        == ResearchPaperExtractionStatus.COMPLETED
    )


def test_acquisition_and_extraction_warnings_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify acquisition and extraction warnings are both retained."""

    pages = (
        SimpleNamespace(extract_text=lambda: None),
        SimpleNamespace(extract_text=lambda: "Second page."),
    )

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    result = ResearchPaperIngestionService().ingest(
        create_acquisition(
            warnings=(
                "Acquisition fallback was used.",
            ),
        )
    )

    assert result.warnings == (
        "Acquisition fallback was used.",
        "Research paper PDF contained pages without extractable text: 1.",
    )
    assert (
        result.extraction_status
        == ResearchPaperExtractionStatus.COMPLETED_WITH_WARNINGS
    )


def test_unavailable_acquisition_fails() -> None:
    """Verify unavailable papers cannot be ingested."""

    with pytest.raises(
        ValueError,
        match="must be acquired before ingestion",
    ):
        ResearchPaperIngestionService().ingest(
            create_acquisition(
                status=ResearchPaperAcquisitionStatus.UNAVAILABLE,
                source_url=None,
                content=None,
            )
        )


def test_missing_acquired_content_fails() -> None:
    """Verify acquired papers require document content."""

    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        ResearchPaperIngestionService().ingest(
            create_acquisition(
                content=None,
            )
        )


def test_empty_acquired_content_fails() -> None:
    """Verify empty acquired paper content is rejected."""

    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        ResearchPaperIngestionService().ingest(
            create_acquisition(
                content=b"",
            )
        )


def test_missing_acquired_source_url_fails() -> None:
    """Verify acquired papers require the actual document URL."""

    with pytest.raises(
        ValueError,
        match="source URL must be provided",
    ):
        ResearchPaperIngestionService().ingest(
            create_acquisition(
                source_url=None,
            )
        )


def test_malformed_pdf_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify malformed acquired PDFs are rejected."""

    def fail_reader(stream: object) -> object:
        raise RuntimeError("Malformed PDF.")

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        fail_reader,
    )

    with pytest.raises(
        ValueError,
        match="PDF could not be parsed",
    ):
        ResearchPaperIngestionService().ingest(
            create_acquisition()
        )


def test_pdf_without_extractable_text_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify PDFs without meaningful extractable text are rejected."""

    pages = (
        SimpleNamespace(extract_text=lambda: None),
        SimpleNamespace(extract_text=lambda: "   "),
    )

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    with pytest.raises(
        ValueError,
        match="contains no meaningful extractable text",
    ):
        ResearchPaperIngestionService().ingest(
            create_acquisition()
        )


def test_paper_documents_receive_unique_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify separate paper documents receive unique identifiers."""

    pages = (
        SimpleNamespace(extract_text=lambda: "Paper text."),
    )

    monkeypatch.setattr(
        research_paper_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    service = ResearchPaperIngestionService()

    first = service.ingest(
        create_acquisition()
    )
    second = service.ingest(
        create_acquisition()
    )

    assert first.document_id != second.document_id
