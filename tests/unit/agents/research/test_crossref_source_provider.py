# ============================================================
# Project0 - Crossref Research Source Provider Tests
#
# File: test_crossref_source_provider.py
#
# Purpose:
#     Verify Crossref provider query generation, request construction,
#     response normalization, and error handling behavior.
#
# ============================================================

from __future__ import annotations

import time
from typing import Any

import httpx
import pytest

from project0.agents.research.crossref_source_provider import (
    CrossrefSourceProvider,
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
            "crossref",
        ),
        rationale="Test Crossref provider behavior.",
    )


def create_crossref_response_data() -> dict[str, Any]:
    """Create a representative Crossref response."""

    return {
        "status": "ok",
        "message-type": "work-list",
        "message-version": "1.0.0",
        "message": {
            "items-per-page": 10,
            "items": [
                {
                    "DOI": "10.1234/example",
                    "title": [
                        "Example Video Representation Paper",
                    ],
                    "URL": "https://doi.org/10.1234/example",
                    "author": [
                        {
                            "given": "Author",
                            "family": "One",
                        },
                        {
                            "given": "Author",
                            "family": "Two",
                        },
                    ],
                    "published-print": {
                        "date-parts": [
                            [
                                2024,
                                1,
                                1,
                            ],
                        ],
                    },
                },
            ],
        },
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
        "https://api.crossref.org/works",
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
            create_crossref_response_data()
            if data is None
            else data
        ),
        headers=headers,
        request=request,
    )


def test_crossref_provider_builds_query() -> None:
    """Verify deterministic query generation."""

    provider = CrossrefSourceProvider()

    query = provider._build_query(
        create_strategy()
    )

    assert query == (
        "video representation learning "
        "multimodal alignment"
    )


def test_crossref_provider_removes_duplicate_terms() -> None:
    """Verify duplicate search terms are removed."""

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(
            "video",
            "video",
            "learning",
        ),
        constraints=(),
        source_names=("crossref",),
        rationale=None,
    )

    provider = CrossrefSourceProvider()

    query = provider._build_query(strategy)

    assert query == "video learning"


def test_crossref_provider_returns_empty_query() -> None:
    """Verify empty strategies produce no query."""

    provider = CrossrefSourceProvider()

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(),
        constraints=(),
        source_names=("crossref",),
        rationale=None,
    )

    assert provider._build_query(strategy) == ""


def test_crossref_provider_builds_expected_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify research strategy maps to Crossref works search."""

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

    CrossrefSourceProvider(
        timeout_seconds=45.0,
        maximum_results=8,
    ).search(
        create_strategy()
    )

    assert captured["url"] == (
        "https://api.crossref.org/works"
    )
    assert captured["params"]["query"] == (
        "video representation learning "
        "multimodal alignment"
    )
    assert captured["params"]["rows"] == 8
    assert captured["timeout"] == 45.0


def test_crossref_provider_includes_optional_mailto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify configured Crossref mailto values are sent."""

    captured_params: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured_params.update(params)
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    CrossrefSourceProvider(
        mailto="project0@example.com",
    ).search(
        create_strategy()
    )

    assert captured_params["mailto"] == (
        "project0@example.com"
    )


def test_crossref_provider_omits_unconfigured_mailto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Crossref requests omit unconfigured mailto values."""

    captured_params: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured_params.update(params)
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    CrossrefSourceProvider().search(
        create_strategy()
    )

    assert "mailto" not in captured_params


def test_crossref_provider_normalizes_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Crossref responses map to research references."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].source_name == "crossref"
    assert result[0].source_id == "10.1234/example"
    assert result[0].title == (
        "Example Video Representation Paper"
    )
    assert result[0].source_url == (
        "https://doi.org/10.1234/example"
    )
    assert result[0].publication_year == 2024
    assert result[0].authors == (
        "Author One",
        "Author Two",
    )


def test_crossref_provider_accepts_scalar_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify scalar Crossref titles are normalized."""

    response_data = create_crossref_response_data()
    response_data["message"]["items"][0]["title"] = (
        "Example Video Representation Paper"
    )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].title == (
        "Example Video Representation Paper"
    )


def test_crossref_provider_reports_invalid_title_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify titleless Crossref records are skipped without failing search."""

    response_data = create_crossref_response_data()
    response_data["message"]["items"][0]["title"] = None

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert result == ()


def test_crossref_provider_uses_subtitle_when_title_is_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify alternate Crossref title metadata is used when available."""

    response_data = create_crossref_response_data()
    item = response_data["message"]["items"][0]
    item["title"] = None
    item["subtitle"] = ["Fallback Crossref Subtitle"]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(create_strategy())

    assert result[0].title == "Fallback Crossref Subtitle"


def test_crossref_provider_uses_doi_url_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing Crossref URLs fall back to the DOI URL."""

    response_data = create_crossref_response_data()
    response_data["message"]["items"][0].pop("URL")

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert result[0].source_url == (
        "https://doi.org/10.1234/example"
    )


def test_crossref_provider_empty_strategy_returns_no_results() -> None:
    """Verify empty search strategies return no results."""

    provider = CrossrefSourceProvider()

    result = provider.search(
        ResearchStrategy(
            concepts=(),
            search_terms=(),
            constraints=(),
            source_names=("crossref",),
            rationale=None,
        )
    )

    assert result == ()


def test_crossref_provider_handles_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP failures become provider errors."""

    def mock_get(*args, **kwargs):
        raise httpx.HTTPError(
            "Connection failed."
        )

    monkeypatch.setattr(
        "project0.agents.research.crossref_source_provider.httpx.get",
        mock_get,
    )

    provider = CrossrefSourceProvider()

    with pytest.raises(
        RuntimeError,
        match="Crossref request failed",
    ):
        provider.search(
            create_strategy()
        )


def test_crossref_provider_rejects_invalid_response_json(
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
        CrossrefSourceProvider().search(
            create_strategy()
        )


def test_crossref_provider_requires_response_object(
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
        CrossrefSourceProvider().search(
            create_strategy()
        )


def test_crossref_provider_requires_message_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Crossref responses include a message object."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "status": "ok",
            },
        ),
    )

    with pytest.raises(TypeError):
        CrossrefSourceProvider().search(
            create_strategy()
        )


def test_crossref_provider_requires_items_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Crossref responses include an items list."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "message": {},
            },
        ),
    )

    with pytest.raises(TypeError):
        CrossrefSourceProvider().search(
            create_strategy()
        )


def test_crossref_provider_retries_transient_request_failure(
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
                "https://api.crossref.org/works",
            )
            raise httpx.ReadTimeout(
                "Read timed out.",
                request=request,
            )

        return create_http_response()

    monkeypatch.setattr(
        "project0.agents.research.crossref_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.crossref_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = CrossrefSourceProvider(
        retry_delay_seconds=0.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1


def test_crossref_provider_retries_rate_limit_response(
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
        "project0.agents.research.crossref_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.crossref_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = CrossrefSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=0.0,
    )

    with pytest.raises(
        RuntimeError,
        match="Crossref request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3


def test_crossref_provider_honors_retry_after_header(
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
        "project0.agents.research.crossref_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.crossref_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = CrossrefSourceProvider(
        maximum_attempts=2,
        retry_delay_seconds=1.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1
    assert sleep_calls == [5.0]


def test_crossref_provider_uses_exponential_backoff_for_rate_limit(
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
        "project0.agents.research.crossref_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.crossref_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = CrossrefSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=2.0,
    )

    with pytest.raises(
        RuntimeError,
        match="Crossref request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3
    assert sleep_calls == [
        2.0,
        4.0,
    ]


def test_crossref_provider_sends_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Crossref requests identify the Project0 client."""

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

    CrossrefSourceProvider(
        user_agent="Project0-Test-Agent",
    ).search(
        create_strategy()
    )

    assert captured_headers == {
        "User-Agent": "Project0-Test-Agent",
    }


def test_crossref_provider_prefers_print_publication_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify print publication year is preferred when available."""

    response_data = create_crossref_response_data()
    item = response_data["message"]["items"][0]
    item["published-online"] = {
        "date-parts": [
            [
                2023,
            ],
        ],
    }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert result[0].publication_year == 2024


def test_crossref_provider_uses_online_publication_year_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify online publication year is used when print year is absent."""

    response_data = create_crossref_response_data()
    item = response_data["message"]["items"][0]
    item.pop("published-print")
    item["published-online"] = {
        "date-parts": [
            [
                2023,
            ],
        ],
    }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert result[0].publication_year == 2023


def test_crossref_provider_retains_result_without_publication_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing publication year does not invalidate a paper."""

    response_data = create_crossref_response_data()
    item = response_data["message"]["items"][0]
    item.pop("published-print")

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(create_strategy())

    assert len(result) == 1
    assert result[0].publication_year is None


def test_crossref_provider_ignores_malformed_publication_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed optional dates do not invalidate a paper."""

    response_data = create_crossref_response_data()
    item = response_data["message"]["items"][0]
    item["published-print"] = {"date-parts": [["unknown"]]}

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(create_strategy())

    assert len(result) == 1
    assert result[0].publication_year is None


def test_crossref_provider_bounds_retry_after_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Crossref Retry-After cannot exceed the configured bound."""

    attempts = 0
    sleep_calls: list[float] = []

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return create_http_response(
                status_code=429,
                headers={"Retry-After": "600"},
            )

        return create_http_response()

    monkeypatch.setattr(httpx, "get", mock_get)
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    result = CrossrefSourceProvider(
        maximum_attempts=2,
        maximum_retry_delay_seconds=10.0,
    ).search(create_strategy())

    assert len(result) == 1
    assert sleep_calls == [10.0]

def test_crossref_provider_skips_invalid_search_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify malformed Crossref items do not fail the full search."""

    response_data = create_crossref_response_data()
    valid_item = response_data["message"]["items"][0]

    response_data["message"]["items"] = [
        {
            "DOI": "10.1234/invalid",
            "title": None,
        },
        valid_item,
    ]

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data,
        ),
    )

    result = CrossrefSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].source_id == "10.1234/example"
    assert result[0].title == (
        "Example Video Representation Paper"
    )
