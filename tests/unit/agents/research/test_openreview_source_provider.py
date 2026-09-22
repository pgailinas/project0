# ============================================================
# Project0 - OpenReview Research Source Provider Tests
#
# File: test_openreview_source_provider.py
#
# Purpose:
#     Verify OpenReview provider query generation, request construction,
#     response normalization, and error handling behavior.
#
# ============================================================

from __future__ import annotations

from typing import Any

import httpx
import pytest

from project0.agents.research.openreview_source_provider import (
    OpenReviewSourceProvider,
)
from project0.models.research_models import (
    ResearchStrategy,
)


def create_strategy() -> ResearchStrategy:
    """Create a representative research strategy."""

    return ResearchStrategy(
        concepts=(
            "video representation learning",
            "multimodal alignment",
        ),
        search_terms=(
            "video representation learning",
            "multimodal alignment",
        ),
        constraints=(),
        source_names=(
            "openreview",
        ),
        rationale="Test OpenReview provider behavior.",
    )


def create_openreview_response_data() -> dict[str, Any]:
    """Create a representative OpenReview response."""

    return {
        "count": 1,
        "notes": [
            {
                "id": "openreview-note-001",
                "forum": "openreview-note-001",
                "replyto": None,
                "invitations": [
                    (
                        "NeurIPS.cc/2024/Workshop/"
                        "Video-Language_Models/-/Submission"
                    ),
                ],
                "cdate": 1704067200000,
                "pdate": 1704067200000,
                "content": {
                    "title": {
                        "value": (
                            "Example Video Representation Paper"
                        ),
                    },
                    "authors": {
                        "value": [
                            "Author One",
                            "Author Two",
                        ],
                    },
                    "abstract": {
                        "value": "Example abstract.",
                    },
                    "venue": {
                        "value": "Example Conference",
                    },
                    "pdf": {
                        "value": "/pdf?id=openreview-note-001",
                    },
                },
            },
        ],
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
        "https://api2.openreview.net/notes/search",
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
            create_openreview_response_data()
            if data is None
            else data
        ),
        headers=headers,
        request=request,
    )


def test_openreview_provider_builds_query() -> None:
    """Verify deterministic query generation."""

    provider = OpenReviewSourceProvider()

    query = provider._build_query(
        create_strategy()
    )

    assert query == (
        "video representation learning "
        "multimodal alignment"
    )


def test_openreview_provider_removes_duplicate_terms() -> None:
    """Verify duplicate search terms are removed."""

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(
            "video",
            "video",
            "learning",
        ),
        constraints=(),
        source_names=("openreview",),
        rationale=None,
    )

    provider = OpenReviewSourceProvider()

    query = provider._build_query(strategy)

    assert query == "video learning"


def test_openreview_provider_returns_empty_query() -> None:
    """Verify empty strategies produce no query."""

    provider = OpenReviewSourceProvider()

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(),
        constraints=(),
        source_names=("openreview",),
        rationale=None,
    )

    assert provider._build_query(strategy) == ""


def test_openreview_provider_builds_expected_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify research strategy maps to OpenReview notes search."""

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
        captured["headers"] = headers
        captured["timeout"] = timeout
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    OpenReviewSourceProvider(
        timeout_seconds=45.0,
        maximum_results=8,
    ).search(
        create_strategy()
    )

    assert captured["url"] == (
        "https://api2.openreview.net/notes/search"
    )
    assert captured["params"]["query"] == (
        "video representation learning "
        "multimodal alignment"
    )
    assert captured["params"]["content"] == "title"
    assert captured["params"]["source"] == "forum"
    assert captured["params"]["limit"] == 40
    assert captured["timeout"] == 45.0


def test_openreview_provider_normalizes_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenReview responses map to research references."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(),
    )

    result = OpenReviewSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].source_name == "openreview"
    assert result[0].source_id == "openreview-note-001"
    assert result[0].title == (
        "Example Video Representation Paper"
    )
    assert result[0].source_url == (
        "https://openreview.net/forum?id=openreview-note-001"
    )
    assert result[0].publication_year == 2024
    assert result[0].authors == (
        "Author One",
        "Author Two",
    )
    assert result[0].metadata == {
        "abstract": "Example abstract.",
        "pdf_url": (
            "https://openreview.net/pdf?id=openreview-note-001"
        ),
    }


def test_openreview_provider_uses_api_pdf_endpoint_for_attachment_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Attachment paths use the API endpoint and stable note identifier."""

    response_data = create_openreview_response_data()
    response_data["notes"][0]["content"]["pdf"]["value"] = (
        "/pdf/attachment-hash.pdf"
    )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = OpenReviewSourceProvider().search(create_strategy())

    assert result[0].metadata["pdf_url"] == (
        "https://openreview.net/pdf?id=openreview-note-001"
    )


def test_openreview_provider_uses_creation_year_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify creation date supplies year when publication date is absent."""

    response_data = create_openreview_response_data()
    response_data["notes"][0].pop("pdate")

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = OpenReviewSourceProvider().search(
        create_strategy()
    )

    assert result[0].publication_year == 2024


def test_openreview_provider_empty_strategy_returns_no_results() -> None:
    """Verify empty search strategies return no results."""

    provider = OpenReviewSourceProvider()

    result = provider.search(
        ResearchStrategy(
            concepts=(),
            search_terms=(),
            constraints=(),
            source_names=("openreview",),
            rationale=None,
        )
    )

    assert result == ()


def test_openreview_provider_handles_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP failures become provider errors."""

    def mock_get(*args, **kwargs):
        raise httpx.HTTPError(
            "Connection failed."
        )

    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.httpx.get",
        mock_get,
    )

    provider = OpenReviewSourceProvider()

    with pytest.raises(
        RuntimeError,
        match="OpenReview request failed",
    ):
        provider.search(
            create_strategy()
        )


def test_openreview_provider_rejects_invalid_response_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify malformed response JSON is rejected."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            content=b"not-json",
        ),
    )

    with pytest.raises(ValueError):
        OpenReviewSourceProvider().search(
            create_strategy()
        )


def test_openreview_provider_requires_response_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify responses must contain JSON objects."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=[],
        ),
    )

    with pytest.raises(TypeError):
        OpenReviewSourceProvider().search(
            create_strategy()
        )


def test_openreview_provider_requires_notes_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenReview responses include a notes list."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "count": 0,
            },
        ),
    )

    with pytest.raises(TypeError):
        OpenReviewSourceProvider().search(
            create_strategy()
        )


def test_openreview_provider_requires_content_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenReview notes include a content object."""

    response_data = create_openreview_response_data()
    response_data["notes"][0]["content"] = None

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    with pytest.raises(TypeError):
        OpenReviewSourceProvider().search(
            create_strategy()
        )


def test_openreview_provider_requires_title_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenReview notes require a title value."""

    response_data = create_openreview_response_data()
    response_data["notes"][0]["content"]["title"] = {
        "value": None,
    }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    with pytest.raises(TypeError):
        OpenReviewSourceProvider().search(
            create_strategy()
        )


def test_openreview_provider_retries_transient_request_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify transient request failures are retried."""

    attempts = 0

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            request = httpx.Request(
                "GET",
                "https://api2.openreview.net/notes/search",
            )
            raise httpx.ReadTimeout(
                "Read timed out.",
                request=request,
            )

        return create_http_response()

    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = OpenReviewSourceProvider(
        retry_delay_seconds=0.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1


def test_openreview_provider_retries_rate_limit_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP 429 responses are retried before failing."""

    attempts = 0

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        return create_http_response(
            status_code=429,
        )

    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = OpenReviewSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=0.0,
    )

    with pytest.raises(
        RuntimeError,
        match="OpenReview request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3


def test_openreview_provider_honors_retry_after_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP 429 Retry-After values control retry delay."""

    attempts = 0
    sleep_calls: list[float] = []

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return create_http_response(
                status_code=429,
                headers={
                    "Retry-After": "5",
                },
            )

        return create_http_response()

    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = OpenReviewSourceProvider(
        maximum_attempts=2,
        retry_delay_seconds=1.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1
    assert sleep_calls == [5.0]


def test_openreview_provider_uses_exponential_backoff_for_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP 429 retries use exponential backoff."""

    attempts = 0
    sleep_calls: list[float] = []

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        return create_http_response(
            status_code=429,
        )

    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openreview_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = OpenReviewSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=2.0,
    )

    with pytest.raises(
        RuntimeError,
        match="OpenReview request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3
    assert sleep_calls == [
        2.0,
        4.0,
    ]


def test_openreview_provider_sends_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenReview requests identify the Project0 client."""

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

    OpenReviewSourceProvider(
        user_agent="Project0-Test-Agent",
    ).search(
        create_strategy()
    )

    assert captured_headers == {
        "User-Agent": "Project0-Test-Agent",
    }

def test_openreview_provider_skips_official_review_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Official Review notes are excluded from paper results."""

    response_data = create_openreview_response_data()
    valid_note = response_data["notes"][0]

    response_data["notes"] = [
        {
            "id": "review-note-001",
            "forum": "paper-note-001",
            "replyto": "paper-note-001",
            "invitations": [
                (
                    "ICLR.cc/2026/Conference/"
                    "Submission6947/-/Official_Review"
                ),
            ],
            "cdate": 1761930982951,
            "content": {
                "summary": {
                    "value": "Example review.",
                },
            },
        },
        valid_note,
    ]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = OpenReviewSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].source_id == "openreview-note-001"


def test_openreview_provider_skips_dblp_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify imported DBLP records are excluded from OpenReview results."""

    response_data = create_openreview_response_data()
    valid_note = response_data["notes"][0]

    response_data["notes"] = [
        {
            "id": "dblp-note-001",
            "forum": "dblp-note-001",
            "replyto": None,
            "invitations": [
                "DBLP.org/-/Record",
                "DBLP.org/-/Edit",
            ],
            "cdate": 1704067200000,
            "content": {
                "title": {
                    "value": "Imported DBLP Paper",
                },
                "authors": {
                    "value": [
                        "Author One",
                    ],
                },
            },
        },
        valid_note,
    ]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = OpenReviewSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].source_id == "openreview-note-001"


def test_openreview_provider_limits_filtered_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify filtered submission results honor maximum_results."""

    response_data = create_openreview_response_data()
    template = response_data["notes"][0]

    response_data["notes"] = [
        {
            **template,
            "id": f"openreview-note-{index:03d}",
            "forum": f"openreview-note-{index:03d}",
        }
        for index in range(1, 5)
    ]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = OpenReviewSourceProvider(
        maximum_results=2,
    ).search(
        create_strategy()
    )

    assert len(result) == 2
    assert tuple(
        reference.source_id
        for reference in result
    ) == (
        "openreview-note-001",
        "openreview-note-002",
    )
