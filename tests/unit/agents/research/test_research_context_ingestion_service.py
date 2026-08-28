# ============================================================
# Project0 - Research Context Ingestion Service Tests
#
# File: test_research_context_ingestion_service.py
#
# Purpose:
#     Verify existing research context document type detection,
#     text extraction, normalization, and error handling.
#
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

import pytest

from project0.agents.research import research_context_ingestion_service
from project0.agents.research.research_context_ingestion_service import (
    ResearchContextIngestionService,
)
from project0.models.research_models import (
    ResearchContextDocumentType,
    ResearchContextExtractionStatus,
)


def test_markdown_document_is_ingested() -> None:
    """Verify Markdown research context is decoded and preserved."""

    content = b"# Prior Research\n\nExisting findings.\n"

    result = ResearchContextIngestionService().ingest(
        "prior_research.md",
        content,
    )

    assert result.source_name == "prior_research.md"
    assert result.document_type == ResearchContextDocumentType.MARKDOWN
    assert result.extraction_method == "utf-8"
    assert result.extracted_text == content.decode("utf-8")
    assert (
        result.extraction_status
        == ResearchContextExtractionStatus.COMPLETED
    )
    assert result.warnings == ()
    assert result.page_count is None
    assert result.document_id


def test_markdown_extension_is_supported() -> None:
    """Verify the .markdown extension is accepted."""

    result = ResearchContextIngestionService().ingest(
        "prior_research.markdown",
        b"# Prior Research\n",
    )

    assert result.document_type == ResearchContextDocumentType.MARKDOWN


def test_text_document_preserves_unicode() -> None:
    """Verify plain-text research context preserves Unicode content."""

    content = "Video–language alignment: café.\n".encode("utf-8")

    result = ResearchContextIngestionService().ingest(
        "prior_research.txt",
        content,
    )

    assert result.document_type == ResearchContextDocumentType.TEXT
    assert result.extracted_text == content.decode("utf-8")
    assert result.page_count is None


def test_pdf_document_is_ingested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify PDF text is extracted and normalized."""

    pages = (
        SimpleNamespace(extract_text=lambda: "First page."),
        SimpleNamespace(extract_text=lambda: "Second page."),
    )

    monkeypatch.setattr(
        research_context_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    result = ResearchContextIngestionService().ingest(
        "prior_research.pdf",
        b"%PDF-test",
    )

    assert result.document_type == ResearchContextDocumentType.PDF
    assert result.extraction_method == "pypdf"
    assert result.extracted_text == "First page.\n\nSecond page."
    assert result.page_count == 2
    assert (
        result.extraction_status
        == ResearchContextExtractionStatus.COMPLETED
    )


def test_pdf_document_ignores_empty_page_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify empty PDF pages do not add empty text blocks."""

    pages = (
        SimpleNamespace(extract_text=lambda: "First page."),
        SimpleNamespace(extract_text=lambda: None),
        SimpleNamespace(extract_text=lambda: "Third page."),
    )

    monkeypatch.setattr(
        research_context_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    result = ResearchContextIngestionService().ingest(
        "prior_research.pdf",
        b"%PDF-test",
    )

    assert result.extracted_text == "First page.\n\nThird page."
    assert result.page_count == 3


def test_empty_content_fails() -> None:
    """Verify empty research context content is rejected."""

    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research.txt",
            b"",
        )


def test_whitespace_only_text_fails() -> None:
    """Verify text without meaningful content is rejected."""

    with pytest.raises(
        ValueError,
        match="contains no meaningful text",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research.txt",
            b"  \n\t",
        )


def test_invalid_utf8_text_fails() -> None:
    """Verify invalid UTF-8 text research context is rejected."""

    with pytest.raises(
        ValueError,
        match="must be valid UTF-8",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research.md",
            b"\xff\xfe",
        )


def test_unsupported_document_type_fails() -> None:
    """Verify unsupported research context document types are rejected."""

    with pytest.raises(
        ValueError,
        match="Unsupported research context document type",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research.docx",
            b"document",
        )


def test_missing_document_extension_fails() -> None:
    """Verify research context documents require a supported extension."""

    with pytest.raises(
        ValueError,
        match="Unsupported research context document type: <none>",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research",
            b"document",
        )


def test_malformed_pdf_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify malformed PDF research context is rejected."""

    def fail_reader(stream: object) -> object:
        raise RuntimeError("Malformed PDF.")

    monkeypatch.setattr(
        research_context_ingestion_service,
        "PdfReader",
        fail_reader,
    )

    with pytest.raises(
        ValueError,
        match="PDF could not be parsed",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research.pdf",
            b"%PDF-invalid",
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
        research_context_ingestion_service,
        "PdfReader",
        lambda stream: SimpleNamespace(pages=pages),
    )

    with pytest.raises(
        ValueError,
        match="contains no meaningful extractable text",
    ):
        ResearchContextIngestionService().ingest(
            "prior_research.pdf",
            b"%PDF-test",
        )


def test_context_documents_receive_unique_ids() -> None:
    """Verify separate context documents receive unique identifiers."""

    service = ResearchContextIngestionService()

    first = service.ingest(
        "first.txt",
        b"First document.",
    )
    second = service.ingest(
        "second.txt",
        b"Second document.",
    )

    assert first.document_id != second.document_id
