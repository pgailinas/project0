# ============================================================
# Project0 - Research Paper Acquisition Service Tests
#
# File: test_research_paper_acquisition_service.py
#
# Purpose:
#     Verify retained research paper full-text URL selection,
#     PDF acquisition, validation, fallback, and error handling.
#
# ============================================================

from __future__ import annotations

from typing import Any

import httpx
import pytest

from project0.agents.research.research_paper_acquisition_service import (
    ResearchPaperAcquisitionService,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchPaperAcquisitionStatus,
    ResearchSourceReference,
)


def create_paper(
    *,
    document_url: str | None = "https://example.test/paper.pdf",
    doi: str | None = None,
    source_url: str | None = "https://example.test/paper",
) -> PaperMetadata:
    """Create retained paper metadata for acquisition tests."""

    reference_metadata = {}

    if document_url is not None:
        reference_metadata["document_url"] = document_url

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="paper-001",
        title="Example Paper",
        source_url=source_url,
        metadata=reference_metadata,
    )

    return PaperMetadata(
        source_reference=reference,
        title="Example Paper",
        doi=doi,
        source_url=source_url,
    )


def create_response(
    *,
    url: str = "https://example.test/paper.pdf",
    status_code: int = 200,
    content: bytes = b"%PDF-example",
    content_type: str = "application/pdf",
) -> httpx.Response:
    """Create an HTTP response for acquisition tests."""

    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={
            "Content-Type": content_type,
        },
        request=httpx.Request(
            "GET",
            url,
        ),
    )


def test_document_url_is_acquired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify normalized document URL is preferred for acquisition."""

    requested_urls = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)
        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    paper = create_paper()

    result = ResearchPaperAcquisitionService().acquire(
        paper
    )

    assert requested_urls == [
        "https://example.test/paper.pdf",
    ]
    assert result.paper is paper
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )
    assert result.source_url == "https://example.test/paper.pdf"
    assert result.content == b"%PDF-example"
    assert result.content_type == "application/pdf"
    assert result.warnings == ()


def test_paper_metadata_document_url_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify PaperMetadata may directly provide a document URL."""

    reference = ResearchSourceReference(
        source_name="openalex",
        source_id="paper-001",
        title="Example Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
        metadata={
            "document_url": "https://example.test/direct.pdf",
        },
    )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: create_response(
            url=url,
        ),
    )

    result = ResearchPaperAcquisitionService().acquire(
        paper
    )

    assert result.source_url == "https://example.test/direct.pdf"
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )


def test_redirected_document_url_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify acquisition records the final retrieved document URL."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_response(
            url="https://cdn.example.test/paper.pdf",
        ),
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper()
    )

    assert result.source_url == "https://cdn.example.test/paper.pdf"


def test_doi_is_used_when_document_url_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify DOI resolution is attempted before the source URL."""

    requested_urls = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)
        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper(
            document_url=None,
            doi="10.1234/example",
        )
    )

    assert requested_urls == [
        "https://doi.org/10.1234/example",
    ]
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )


def test_source_url_is_used_as_final_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify source URL is attempted when no document URL or DOI exists."""

    requested_urls = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)
        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper(
            document_url=None,
        )
    )

    assert requested_urls == [
        "https://example.test/paper",
    ]
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )


def test_missing_acquisition_urls_returns_unavailable() -> None:
    """Verify papers without acquisition URLs are explicitly unavailable."""

    paper = create_paper(
        document_url=None,
        source_url=None,
    )

    result = ResearchPaperAcquisitionService().acquire(
        paper
    )

    assert result.paper is paper
    assert result.source_url is None
    assert result.content is None
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.UNAVAILABLE
    )
    assert result.content_type is None
    assert result.warnings == (
        "No full-text acquisition URL was available.",
    )


def test_non_pdf_content_type_uses_next_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTML landing pages are rejected before fallback."""

    requested_urls = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)

        if url.endswith(
            "paper.pdf"
        ):
            return create_response(
                url=url,
                content=b"<html></html>",
                content_type="text/html",
            )

        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper(
            doi="10.1234/example",
        )
    )

    assert requested_urls == [
        "https://example.test/paper.pdf",
        "https://doi.org/10.1234/example",
    ]
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )
    assert result.warnings == (
        "Full-text candidate did not return PDF content: "
        "https://example.test/paper.pdf.",
    )


def test_invalid_pdf_signature_uses_next_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify PDF content must include the expected PDF signature."""

    requested_urls = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)

        if url.endswith(
            "paper.pdf"
        ):
            return create_response(
                url=url,
                content=b"not-a-pdf",
            )

        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper(
            doi="10.1234/example",
        )
    )

    assert requested_urls == [
        "https://example.test/paper.pdf",
        "https://doi.org/10.1234/example",
    ]
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )
    assert result.warnings == (
        "Full-text candidate did not contain a valid PDF signature: "
        "https://example.test/paper.pdf.",
    )


def test_inaccessible_candidate_uses_next_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify inaccessible document URLs permit deterministic fallback."""

    requested_urls = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)

        if url.endswith(
            "paper.pdf"
        ):
            return create_response(
                url=url,
                status_code=404,
            )

        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper(
            doi="10.1234/example",
        )
    )

    assert requested_urls == [
        "https://example.test/paper.pdf",
        "https://doi.org/10.1234/example",
    ]
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.ACQUIRED
    )


def test_all_non_pdf_candidates_return_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify absence of usable PDF content returns unavailable."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: create_response(
            url=url,
            content=b"<html></html>",
            content_type="text/html",
        ),
    )

    result = ResearchPaperAcquisitionService().acquire(
        create_paper(
            doi="10.1234/example",
        )
    )

    assert result.source_url is None
    assert result.content is None
    assert (
        result.acquisition_status
        == ResearchPaperAcquisitionStatus.UNAVAILABLE
    )
    assert len(result.warnings) == 3


def test_request_error_is_retried_then_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify operational request failures use bounded retries and propagate."""

    attempts = []

    def fail_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        attempts.append(url)
        request = httpx.Request(
            "GET",
            url,
        )
        raise httpx.ConnectError(
            "Connection refused.",
            request=request,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fail_get,
    )

    monkeypatch.setattr(
        "project0.agents.research."
        "research_paper_acquisition_service.time.sleep",
        lambda seconds: None,
    )

    with pytest.raises(
        RuntimeError,
        match="Research paper acquisition request failed",
    ):
        ResearchPaperAcquisitionService().acquire(
            create_paper()
        )

    assert len(attempts) == 3


def test_server_error_is_retried_then_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify server failures use bounded retries and propagate."""

    attempts = []

    def fail_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        attempts.append(url)
        return create_response(
            url=url,
            status_code=503,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fail_get,
    )

    monkeypatch.setattr(
        "project0.agents.research."
        "research_paper_acquisition_service.time.sleep",
        lambda seconds: None,
    )

    with pytest.raises(
        RuntimeError,
        match="Research paper acquisition request failed",
    ):
        ResearchPaperAcquisitionService().acquire(
            create_paper()
        )

    assert len(attempts) == 3


def test_duplicate_candidate_urls_are_not_retried_as_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify duplicate normalized acquisition URLs are removed."""

    requested_urls = []

    document_url = "https://example.test/paper.pdf"

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="paper-001",
        title="Example Paper",
        source_url=document_url,
        metadata={
            "document_url": document_url,
        },
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
        source_url=document_url,
        metadata={
            "document_url": document_url,
        },
    )

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        requested_urls.append(url)
        return create_response(
            url=url,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    ResearchPaperAcquisitionService().acquire(
        paper
    )

    assert requested_urls == [
        document_url,
    ]
