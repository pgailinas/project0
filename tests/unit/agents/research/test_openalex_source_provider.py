# ============================================================
# Project0 - OpenAlex Research Source Provider Tests
#
# File: test_openalex_source_provider.py
#
# Purpose:
#     Verify OpenAlex provider query generation, request construction,
#     response normalization, and error handling behavior.
#
# ============================================================

from __future__ import annotations

from typing import Any

import httpx
import pytest

from project0.agents.research.openalex_source_provider import (
    OpenAlexSourceProvider,
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
            "openalex",
        ),
        rationale="Test OpenAlex provider behavior.",
    )


def create_openalex_response_data() -> dict[str, Any]:
    """Create a representative OpenAlex response."""

    return {
        "meta": {
            "count": 1,
            "page": 1,
            "per_page": 10,
            "cost_usd": 0.001,
        },
        "results": [
            {
                "id": "https://openalex.org/W1234567890",
                "doi": "https://doi.org/10.1234/example",
                "title": "Example Video Representation Paper",
                "display_name": "Example Video Representation Paper",
                "publication_year": 2024,
                "primary_location": {
                    "landing_page_url": (
                        "https://doi.org/10.1234/example"
                    ),
                },
                "authorships": [
                    {
                        "author": {
                            "display_name": "Author One",
                        },
                    },
                    {
                        "author": {
                            "display_name": "Author Two",
                        },
                    },
                ],
            },
        ],
        "group_by": [],
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
        "https://api.openalex.org/works",
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
            create_openalex_response_data()
            if data is None
            else data
        ),
        headers=headers,
        request=request,
    )


def test_openalex_provider_builds_query() -> None:
    """Verify deterministic query generation."""

    provider = OpenAlexSourceProvider()

    query = provider._build_query(
        create_strategy()
    )

    assert query == (
        "video representation learning "
        "multimodal alignment"
    )


def test_openalex_provider_removes_duplicate_terms() -> None:
    """Verify duplicate search terms are removed."""

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(
            "video",
            "video",
            "learning",
        ),
        constraints=(),
        source_names=("openalex",),
        rationale=None,
    )

    provider = OpenAlexSourceProvider()

    query = provider._build_query(strategy)

    assert query == "video learning"


def test_openalex_provider_returns_empty_query() -> None:
    """Verify empty strategies produce no query."""

    provider = OpenAlexSourceProvider()

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(),
        constraints=(),
        source_names=("openalex",),
        rationale=None,
    )

    assert provider._build_query(strategy) == ""


def test_openalex_provider_builds_expected_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify research strategy maps to OpenAlex works search."""

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

    OpenAlexSourceProvider(
        timeout_seconds=45.0,
        maximum_results=8,
    ).search(
        create_strategy()
    )

    assert captured["url"] == (
        "https://api.openalex.org/works"
    )
    assert captured["params"]["search"] == (
        "video representation learning "
        "multimodal alignment"
    )
    assert captured["params"]["per_page"] == 8
    assert captured["timeout"] == 45.0


def test_openalex_provider_includes_optional_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify configured OpenAlex API keys are sent with requests."""

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

    OpenAlexSourceProvider(
        api_key="test-openalex-key",
    ).search(
        create_strategy()
    )

    assert captured_params["api_key"] == (
        "test-openalex-key"
    )


def test_openalex_provider_omits_unconfigured_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify anonymous OpenAlex requests omit the API key."""

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

    OpenAlexSourceProvider().search(
        create_strategy()
    )

    assert "api_key" not in captured_params


def test_openalex_provider_normalizes_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenAlex responses map to research references."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(),
    )

    result = OpenAlexSourceProvider().search(
        create_strategy()
    )

    assert len(result) == 1
    assert result[0].source_name == "openalex"
    assert result[0].source_id == (
        "https://openalex.org/W1234567890"
    )
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


def test_openalex_provider_empty_strategy_returns_no_results() -> None:
    """Verify empty search strategies return no results."""

    provider = OpenAlexSourceProvider()

    result = provider.search(
        ResearchStrategy(
            concepts=(),
            search_terms=(),
            constraints=(),
            source_names=("openalex",),
            rationale=None,
        )
    )

    assert result == ()


def test_openalex_provider_handles_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP failures become provider errors."""

    def mock_get(*args, **kwargs):
        raise httpx.HTTPError(
            "Connection failed."
        )

    monkeypatch.setattr(
        "project0.agents.research.openalex_source_provider.httpx.get",
        mock_get,
    )

    provider = OpenAlexSourceProvider()

    with pytest.raises(
        RuntimeError,
        match="OpenAlex request failed",
    ):
        provider.search(
            create_strategy()
        )


def test_openalex_provider_rejects_invalid_response_json(
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
        OpenAlexSourceProvider().search(
            create_strategy()
        )


def test_openalex_provider_requires_response_object(
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
        OpenAlexSourceProvider().search(
            create_strategy()
        )


def test_openalex_provider_requires_results_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenAlex responses include a results list."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "meta": {},
            },
        ),
    )

    with pytest.raises(TypeError):
        OpenAlexSourceProvider().search(
            create_strategy()
        )


def test_openalex_provider_retries_transient_request_failure(
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
                "https://api.openalex.org/works",
            )
            raise httpx.ReadTimeout(
                "Read timed out.",
                request=request,
            )

        return create_http_response()

    monkeypatch.setattr(
        "project0.agents.research.openalex_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openalex_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = OpenAlexSourceProvider(
        retry_delay_seconds=0.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1


def test_openalex_provider_retries_rate_limit_response(
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
        "project0.agents.research.openalex_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openalex_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = OpenAlexSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=0.0,
    )

    with pytest.raises(
        RuntimeError,
        match="OpenAlex request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3


def test_openalex_provider_honors_retry_after_header(
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
        "project0.agents.research.openalex_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openalex_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = OpenAlexSourceProvider(
        maximum_attempts=2,
        retry_delay_seconds=1.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1
    assert sleep_calls == [5.0]


def test_openalex_provider_uses_exponential_backoff_for_rate_limit(
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
        "project0.agents.research.openalex_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.openalex_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = OpenAlexSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=2.0,
    )

    with pytest.raises(
        RuntimeError,
        match="OpenAlex request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3
    assert sleep_calls == [
        2.0,
        4.0,
    ]


def test_openalex_provider_sends_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify OpenAlex requests identify the Project0 client."""

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

    OpenAlexSourceProvider(
        user_agent="Project0-Test-Agent",
    ).search(
        create_strategy()
    )

    assert captured_headers == {
        "User-Agent": "Project0-Test-Agent",
    }
