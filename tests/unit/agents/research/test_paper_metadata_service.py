# ============================================================
# Project0 - Paper Metadata Service Tests
#
# File: test_paper_metadata_service.py
#
# Purpose:
#     Verify paper metadata request construction, response
#     normalization, field mapping, and error handling.
#
# ============================================================

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from project0.agents.research.paper_metadata_service import (
    PaperMetadataService,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchPaperEvidenceStatus,
    ResearchSourceReference,
)


def create_source_reference() -> ResearchSourceReference:
    """Create a representative research source reference."""

    return ResearchSourceReference(
        source_name="semantic_scholar",
        source_id="paper-001",
        title="Example Video Representation Paper",
        source_url=(
            "https://www.semanticscholar.org/"
            "paper/paper-001"
        ),
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
        metadata={
            "abstract": "Search-result abstract.",
            "venue": "Search Conference",
            "doi": "10.1000/search-example",
        },
    )


def create_semantic_scholar_metadata_response() -> dict[str, Any]:
    """Create a representative Semantic Scholar metadata response."""

    return {
        "paperId": "paper-001",
        "title": "Example Video Representation Paper",
        "authors": [
            {
                "authorId": "author-001",
                "name": "Author One",
            },
            {
                "authorId": "author-002",
                "name": "Author Two",
            },
        ],
        "year": 2024,
        "abstract": "Example abstract.",
        "venue": "Example Conference",
        "externalIds": {
            "DOI": "10.1000/example",
        },
        "url": (
            "https://www.semanticscholar.org/"
            "paper/paper-001"
        ),
    }


def create_http_response(
    status_code: int = 200,
    data: Any | None = None,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Create an HTTP response with request metadata attached."""

    request = httpx.Request(
        "GET",
        (
            "https://api.semanticscholar.org/graph/v1/"
            "paper/paper-001"
        ),
    )

    if content is not None:
        return httpx.Response(
            status_code,
            content=content,
            headers=headers,
            request=request,
        )

    return httpx.Response(
        status_code,
        json=(
            create_semantic_scholar_metadata_response()
            if data is None
            else data
        ),
        headers=headers,
        request=request,
    )


def test_paper_metadata_service_builds_expected_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify source references map to Semantic Scholar metadata API."""

    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    service = PaperMetadataService(
        timeout_seconds=45.0,
    )

    service.retrieve_metadata(
        (create_source_reference(),)
    )

    assert captured["url"] == (
        "https://api.semanticscholar.org/graph/v1/"
        "paper/paper-001"
    )
    assert captured["timeout"] == 45.0
    assert captured["params"] == {
        "fields": (
            "paperId,title,authors,year,abstract,"
            "venue,externalIds,url,openAccessPdf"
        ),
    }


def test_paper_metadata_service_sends_semantic_scholar_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify configured Semantic Scholar metadata API keys are sent."""

    captured_headers: dict[str, str] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured_headers.update(headers)
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    PaperMetadataService(
        semantic_scholar_api_key="test-semantic-scholar-key",
    ).retrieve_metadata(
        (create_source_reference(),)
    )

    assert captured_headers["x-api-key"] == (
        "test-semantic-scholar-key"
    )


def test_paper_metadata_service_omits_semantic_scholar_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify unconfigured Semantic Scholar metadata API keys are omitted."""

    captured_headers: dict[str, str] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured_headers.update(headers)
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    PaperMetadataService(
        semantic_scholar_api_key=None,
    ).retrieve_metadata(
        (create_source_reference(),)
    )

    assert "x-api-key" not in captured_headers


def test_paper_metadata_service_uses_configured_default_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The metadata service shares the application API key by default."""

    captured_headers: dict[str, str] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured_headers.update(headers)
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(
        "project0.agents.research.paper_metadata_service.SETTINGS",
        SimpleNamespace(
            semantic_scholar_api_key="configured-api-key",
        ),
    )

    PaperMetadataService().retrieve_metadata(
        (create_source_reference(),)
    )

    assert captured_headers["x-api-key"] == "configured-api-key"


def test_paper_metadata_service_normalizes_trailing_base_url_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify trailing base URL slash does not duplicate separators."""

    captured_url = ""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        nonlocal captured_url
        captured_url = url
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    service = PaperMetadataService(
        semantic_scholar_base_url=(
            "https://api.semanticscholar.org/graph/v1/"
        ),
    )

    service.retrieve_metadata(
        (create_source_reference(),)
    )

    assert captured_url == (
        "https://api.semanticscholar.org/graph/v1/"
        "paper/paper-001"
    )


def test_paper_metadata_service_returns_normalized_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify successful response maps to PaperMetadata."""

    response_data = create_semantic_scholar_metadata_response()

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    reference = create_source_reference()

    result = PaperMetadataService().retrieve_metadata(
        (reference,)
    )

    assert len(result) == 1

    paper = result[0]

    assert paper.source_reference == reference
    assert paper.title == (
        "Example Video Representation Paper"
    )
    assert paper.authors == (
        "Author One",
        "Author Two",
    )
    assert paper.publication_year == 2024
    assert paper.abstract == "Example abstract."
    assert paper.venue == "Example Conference"
    assert paper.doi == "10.1000/example"
    assert paper.source_url == (
        "https://www.semanticscholar.org/"
        "paper/paper-001"
    )
    assert paper.metadata == {
        "paper_id": "paper-001",
    }


def test_paper_metadata_service_returns_empty_for_no_references() -> None:
    """Verify empty source references return no paper metadata."""

    result = PaperMetadataService().retrieve_metadata(())

    assert result == ()


def test_paper_metadata_service_returns_alignment_grounded_stub_metadata(
) -> None:
    """Stub metadata remains eligible for strict alignment evaluation."""

    reference = ResearchSourceReference(
        source_name="stub",
        source_id="stub-paper-001",
        title=(
            "Self-Supervised Video Representation Alignment "
            "with Frozen CLIP for VideoQA"
        ),
        source_url="https://example.com/stub-paper-001",
        authors=("Project0 Research Stub",),
        publication_year=2026,
    )

    result = PaperMetadataService().retrieve_metadata((reference,))

    assert len(result) == 1
    assert result[0].source_reference == reference
    assert result[0].abstract == (
        "A learned video encoder aligns its representations with a frozen "
        "CLIP vision-language teacher through feature matching in the "
        "shared embedding space."
    )
    assert result[0].venue == "Project0 Research Stub"


def test_paper_metadata_service_retrieves_multiple_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify metadata is retrieved for each source reference."""

    calls: list[str] = []

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        calls.append(url)

        paper_id = url.rsplit("/", 1)[-1]

        response_data = create_semantic_scholar_metadata_response()
        response_data["paperId"] = paper_id
        response_data["title"] = f"Paper {paper_id}"

        return create_http_response(
            data=response_data
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    first_reference = create_source_reference()

    second_reference = ResearchSourceReference(
        source_name="semantic_scholar",
        source_id="paper-002",
        title="Second Paper",
    )

    result = PaperMetadataService().retrieve_metadata(
        (
            first_reference,
            second_reference,
        )
    )

    assert len(result) == 2
    assert calls == [
        (
            "https://api.semanticscholar.org/graph/v1/"
            "paper/paper-001"
        ),
        (
            "https://api.semanticscholar.org/graph/v1/"
            "paper/paper-002"
        ),
    ]
    assert result[0].source_reference == first_reference
    assert result[1].source_reference == second_reference


def test_paper_metadata_service_rejects_unsupported_source() -> None:
    """Verify unsupported metadata sources are rejected."""

    reference = ResearchSourceReference(
        source_name="unsupported_source",
        source_id="paper-001",
        title="Example Paper",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Unsupported research metadata source: "
            "unsupported_source"
        ),
    ):
        PaperMetadataService().retrieve_metadata(
            (reference,)
        )


def test_paper_metadata_service_allows_missing_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify optional metadata fields may be absent or null."""

    response_data = {
        "paperId": "paper-001",
        "title": "Example Paper",
        "authors": None,
        "year": None,
        "abstract": None,
        "venue": None,
        "externalIds": None,
        "url": None,
    }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    result = PaperMetadataService().retrieve_metadata(
        (create_source_reference(),)
    )

    paper = result[0]

    assert paper.authors == ()
    assert paper.publication_year is None
    assert paper.abstract is None
    assert paper.venue is None
    assert paper.doi is None
    assert paper.source_url is None


def test_paper_metadata_service_rejects_mismatched_paper_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify metadata response must match requested source ID."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["paperId"] = "paper-999"

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        ValueError,
        match="paperId did not match",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_falls_back_after_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify exhausted HTTP retries use source-search metadata."""

    attempts = 0

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return create_http_response(
            status_code=500,
            data={"error": "metadata failure"},
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    result = PaperMetadataService().retrieve_metadata(
        (create_source_reference(),)
    )

    assert attempts == 3
    assert result[0].abstract == "Search-result abstract."
    assert result[0].metadata["metadata_fallback"] is True


def test_paper_metadata_service_honors_bounded_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A metadata retry honors Retry-After without an unbounded wait."""

    attempts = 0
    sleep_calls: list[float] = []

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return create_http_response(
                status_code=429,
                headers={"Retry-After": "600"},
            )

        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    result = PaperMetadataService(
        maximum_attempts=2,
        maximum_retry_delay_seconds=10.0,
    ).retrieve_metadata((create_source_reference(),))

    assert attempts == 2
    assert sleep_calls == [10.0]
    assert result[0].abstract == "Example abstract."


def test_paper_metadata_service_falls_back_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify exhausted connection retries use source metadata."""

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        request = httpx.Request(
            "GET",
            (
                "https://api.semanticscholar.org/graph/v1/"
                "paper/paper-001"
            ),
        )
        raise httpx.ConnectError(
            "Connection refused.",
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    result = PaperMetadataService().retrieve_metadata(
        (create_source_reference(),)
    )

    assert result[0].abstract == "Search-result abstract."
    assert result[0].metadata["metadata_fallback"] is True


def test_paper_metadata_service_rejects_non_json_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify malformed HTTP response JSON is rejected."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            content=b"not-json"
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Semantic Scholar metadata response was not "
            "valid JSON"
        ),
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_response_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify metadata response must contain a JSON object."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=["unexpected", "list"]
        ),
    )

    with pytest.raises(
        TypeError,
        match="metadata response must be a JSON object",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_paper_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify metadata response requires a paper identifier."""

    response_data = create_semantic_scholar_metadata_response()
    response_data.pop("paperId")

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="paperId must be a string",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify metadata response requires a paper title."""

    response_data = create_semantic_scholar_metadata_response()
    response_data.pop("title")

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="title must be a string",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_author_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify metadata authors must be a list or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["authors"] = "Author One"

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="authors must be a list or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_author_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify each metadata author must be a JSON object."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["authors"] = [
        "Author One",
    ]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="author must be a JSON object",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_author_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify each metadata author requires a name."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["authors"] = [
        {
            "authorId": "author-001",
        },
    ]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="author name must be a string",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_integer_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify publication year must be an integer or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["year"] = "2024"

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="year must be an integer or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_string_abstract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify abstract must be a string or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["abstract"] = 123

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="abstract must be a string or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_string_venue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify venue must be a string or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["venue"] = 123

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="venue must be a string or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_external_ids_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify external identifiers must be an object or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["externalIds"] = "unexpected"

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="externalIds must be a JSON object or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_string_doi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify DOI must be a string or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["externalIds"] = {
        "DOI": 123,
    }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="DOI must be a string or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_requires_string_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify source URL must be a string or null."""

    response_data = create_semantic_scholar_metadata_response()
    response_data["url"] = 123

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="url must be a string or null",
    ):
        PaperMetadataService().retrieve_metadata(
            (create_source_reference(),)
        )


def test_paper_metadata_service_creates_arxiv_metadata() -> None:
    """Verify arXiv references map to normalized PaperMetadata."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="http://arxiv.org/abs/2401.12345",
        title="Example arXiv Paper",
        source_url="http://arxiv.org/abs/2401.12345",
        authors=("Author One",),
        publication_year=2024,
    )

    result = PaperMetadataService().retrieve_metadata(
        (reference,)
    )

    assert len(result) == 1

    paper = result[0]

    assert paper.source_reference == reference
    assert paper.title == "Example arXiv Paper"
    assert paper.authors == ("Author One",)
    assert paper.publication_year == 2024
    assert paper.venue == "arXiv"
    assert paper.metadata == {
        "paper_id": "http://arxiv.org/abs/2401.12345",
        "source": "arxiv",
    }

def test_paper_metadata_service_creates_openalex_metadata() -> None:
    """Verify OpenAlex references map to normalized PaperMetadata."""

    reference = ResearchSourceReference(
        source_name="openalex",
        source_id="https://openalex.org/W1234567890",
        title="Example OpenAlex Paper",
        source_url="https://doi.org/10.1234/example",
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
        metadata={
            "abstract": "Example OpenAlex abstract.",
        },
    )

    result = PaperMetadataService().retrieve_metadata(
        (reference,)
    )

    assert len(result) == 1

    paper = result[0]

    assert paper.source_reference == reference
    assert paper.title == "Example OpenAlex Paper"
    assert paper.authors == (
        "Author One",
        "Author Two",
    )
    assert paper.publication_year == 2024
    assert paper.abstract == "Example OpenAlex abstract."
    assert paper.venue == "OpenAlex"
    assert paper.source_url == (
        "https://doi.org/10.1234/example"
    )
    assert paper.metadata == {
        "paper_id": "https://openalex.org/W1234567890",
        "source": "openalex",
    }

def test_paper_metadata_service_creates_crossref_metadata() -> None:
    """Verify Crossref references map to normalized PaperMetadata."""

    reference = ResearchSourceReference(
        source_name="crossref",
        source_id="10.1234/example",
        title="Example Crossref Paper",
        source_url="https://doi.org/10.1234/example",
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
    )

    result = PaperMetadataService().retrieve_metadata(
        (reference,)
    )

    assert len(result) == 1

    paper = result[0]

    assert paper.source_reference == reference
    assert paper.title == "Example Crossref Paper"
    assert paper.authors == (
        "Author One",
        "Author Two",
    )
    assert paper.publication_year == 2024
    assert paper.abstract is None
    assert paper.venue == "Crossref"
    assert paper.doi == "10.1234/example"
    assert paper.source_url == (
        "https://doi.org/10.1234/example"
    )
    assert paper.metadata == {
        "paper_id": "10.1234/example",
        "source": "crossref",
    }

def test_paper_metadata_service_creates_openreview_metadata() -> None:
    """Verify OpenReview references map to normalized PaperMetadata."""

    reference = ResearchSourceReference(
        source_name="openreview",
        source_id="openreview-note-001",
        title="Example OpenReview Paper",
        source_url=(
            "https://openreview.net/forum?"
            "id=openreview-note-001"
        ),
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
    )

    result = PaperMetadataService().retrieve_metadata(
        (reference,)
    )

    assert len(result) == 1

    paper = result[0]

    assert paper.source_reference == reference
    assert paper.title == "Example OpenReview Paper"
    assert paper.authors == (
        "Author One",
        "Author Two",
    )
    assert paper.publication_year == 2024
    assert paper.abstract is None
    assert paper.venue == "OpenReview"
    assert paper.source_url == (
        "https://openreview.net/forum?"
        "id=openreview-note-001"
    )
    assert paper.metadata == {
        "paper_id": "openreview-note-001",
        "source": "openreview",
    }


def test_paper_metadata_service_acquires_bounded_abstract_evidence() -> None:
    """Only the bounded shortlist receives normalized evidence."""

    papers = tuple(
        PaperMetadata(
            source_reference=ResearchSourceReference(
                source_name="openalex",
                source_id=f"paper-{index}",
                title=f"Paper {index}",
            ),
            title=f"Paper {index}",
            abstract=f"Abstract evidence {index}.",
        )
        for index in range(10)
    )

    result = PaperMetadataService(
        evidence_candidate_limit=8,
    ).acquire_evidence(papers)

    assert len(result) == 8
    assert all(
        paper.evidence_status == ResearchPaperEvidenceStatus.AVAILABLE
        for paper in result
    )
    assert result[0].evidence_sections[0].section == "Abstract"
    assert result[0].evidence_sections[0].content == "Abstract evidence 0."


def test_paper_metadata_service_marks_missing_content_discovery_only() -> None:
    """Metadata without an abstract or paper URL remains discovery-only."""

    paper = PaperMetadata(
        source_reference=ResearchSourceReference(
            source_name="crossref",
            source_id="10.1000/discovery",
            title="Discovery Paper",
        ),
        title="Discovery Paper",
    )

    result = PaperMetadataService().acquire_evidence((paper,))

    assert result[0].evidence_status == (
        ResearchPaperEvidenceStatus.DISCOVERY_ONLY
    )
    assert result[0].evidence_sections == ()



def test_paper_metadata_service_retains_abstract_after_pdf_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blocked PDF retrieval falls back to available abstract evidence."""

    paper = PaperMetadata(
        source_reference=ResearchSourceReference(
            source_name="openreview",
            source_id="openreview-note-001",
            title="Evidence Paper",
            metadata={
                "pdf_url": "https://openreview.net/pdf?id=paper",
            },
        ),
        title="Evidence Paper",
        abstract="Available abstract evidence.",
    )

    request = httpx.Request(
        "GET",
        "https://openreview.net/pdf?id=paper",
    )
    response = httpx.Response(
        403,
        request=request,
    )
    error = httpx.HTTPStatusError(
        "Forbidden",
        request=request,
        response=response,
    )

    monkeypatch.setattr(
        PaperMetadataService,
        "_retrieve_pdf_evidence",
        lambda self, pdf_url: (_ for _ in ()).throw(error),
    )

    result = PaperMetadataService().acquire_evidence((paper,))

    assert result[0].evidence_status == (
        ResearchPaperEvidenceStatus.AVAILABLE
    )
    assert len(result[0].evidence_sections) == 1
    assert result[0].evidence_sections[0].section == "Abstract"
    assert result[0].evidence_sections[0].content == (
        "Available abstract evidence."
    )


def test_paper_metadata_service_extracts_page_preserving_sections() -> None:
    """Relevant PDF sections retain their source page numbers."""

    result = PaperMetadataService()._extract_evidence_sections(
        (
            (1, "Abstract\nAn abstract about alignment."),
            (4, "3 Method\nWe align video and text tokens."),
            (7, "5 Experiments\nThe method improves retrieval."),
        )
    )

    assert tuple(section.section for section in result) == (
        "Abstract",
        "Method",
        "Results",
    )
    assert tuple(section.page_number for section in result) == (1, 4, 7)


@pytest.mark.parametrize("source_name", ("arxiv", "openreview", "crossref"))
def test_paper_metadata_service_preserves_source_evidence_metadata(
    source_name: str,
) -> None:
    """Source abstracts and PDF locations survive normalization."""

    reference = ResearchSourceReference(
        source_name=source_name,
        source_id=(
            "10.1000/example"
            if source_name == "crossref"
            else "paper-001"
        ),
        title="Evidence Paper",
        source_url="https://example.test/paper",
        metadata={
            "abstract": "Source-provided abstract.",
            "pdf_url": "https://example.test/paper.pdf",
        },
    )

    paper = PaperMetadataService().retrieve_metadata((reference,))[0]

    assert paper.abstract == "Source-provided abstract."
    assert paper.metadata["pdf_url"] == "https://example.test/paper.pdf"
