# ============================================================
# Project0 - Research Source Service Tests
#
# File: test_research_source_service.py
#
# Purpose:
#     Verify external research source request construction,
#     response normalization, deduplication, and error handling.
#
# ============================================================

from __future__ import annotations

from typing import Any

import httpx
import pytest

from project0.agents.research.research_source_service import (
    ResearchSourceService,
)
from project0.models.research_models import ResearchStrategy


def create_research_strategy() -> ResearchStrategy:
    """Create a representative research strategy."""

    return ResearchStrategy(
        concepts=(
            "self-supervised learning",
            "video representation learning",
        ),
        search_terms=(
            "self-supervised video representation",
            "VideoQA vision-language alignment",
        ),
        constraints=(
            "Prefer recent research.",
        ),
        source_names=(
            "semantic_scholar",
        ),
        rationale="Search for relevant research.",
    )


def create_semantic_scholar_response_data() -> dict[str, Any]:
    """Create a representative Semantic Scholar response."""

    return {
        "total": 2,
        "offset": 0,
        "next": 2,
        "data": [
            {
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
                "url": (
                    "https://www.semanticscholar.org/"
                    "paper/paper-001"
                ),
            },
            {
                "paperId": "paper-002",
                "title": "Example Vision-Language Paper",
                "authors": [
                    {
                        "authorId": "author-003",
                        "name": "Author Three",
                    },
                ],
                "year": 2025,
                "url": (
                    "https://www.semanticscholar.org/"
                    "paper/paper-002"
                ),
            },
        ],
    }


def create_http_response(
    status_code: int = 200,
    data: Any | None = None,
    content: bytes | None = None,
) -> httpx.Response:
    """Create an HTTP response with request metadata attached."""

    request = httpx.Request(
        "GET",
        (
            "https://api.semanticscholar.org/graph/v1/"
            "paper/search"
        ),
    )

    if content is not None:
        return httpx.Response(
            status_code,
            content=content,
            request=request,
        )

    return httpx.Response(
        status_code,
        json=(
            create_semantic_scholar_response_data()
            if data is None
            else data
        ),
        request=request,
    )


def test_research_source_service_builds_expected_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify research strategy maps to Semantic Scholar search."""

    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    strategy = create_research_strategy()
    service = ResearchSourceService(
        timeout_seconds=45.0,
        maximum_results=8,
    )

    service.search(strategy)

    assert captured["url"] == (
        "https://api.semanticscholar.org/graph/v1/"
        "paper/search"
    )
    assert captured["timeout"] == 45.0
    assert captured["params"] == {
        "query": (
            "self-supervised video representation "
            "VideoQA vision-language alignment"
        ),
        "limit": 8,
        "fields": "paperId,title,authors,year,url",
    }


def test_research_source_service_normalizes_trailing_base_url_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify trailing base URL slash does not duplicate separators."""

    captured_url = ""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        nonlocal captured_url
        captured_url = url
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    service = ResearchSourceService(
        semantic_scholar_base_url=(
            "https://api.semanticscholar.org/graph/v1/"
        ),
    )

    service.search(create_research_strategy())

    assert captured_url == (
        "https://api.semanticscholar.org/graph/v1/"
        "paper/search"
    )


def test_research_source_service_returns_normalized_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify successful source response maps to research references."""

    response_data = create_semantic_scholar_response_data()

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    result = ResearchSourceService().search(
        create_research_strategy()
    )

    assert len(result) == 2

    first_reference = result[0]

    assert first_reference.source_name == "semantic_scholar"
    assert first_reference.source_id == "paper-001"
    assert first_reference.title == (
        "Example Video Representation Paper"
    )
    assert first_reference.authors == (
        "Author One",
        "Author Two",
    )
    assert first_reference.publication_year == 2024
    assert first_reference.source_url == (
        "https://www.semanticscholar.org/"
        "paper/paper-001"
    )
    assert first_reference.metadata == {}


def test_research_source_service_defaults_to_semantic_scholar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Semantic Scholar is used when no source is configured."""

    calls = 0

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        nonlocal calls
        calls += 1
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    strategy = ResearchStrategy(
        concepts=("video representation learning",),
        search_terms=("video representation learning",),
    )

    result = ResearchSourceService().search(strategy)

    assert calls == 1
    assert len(result) == 2
    assert all(
        reference.source_name == "semantic_scholar"
        for reference in result
    )


def test_research_source_service_returns_empty_for_no_search_terms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify empty search terms do not call the external source."""

    calls = 0

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        nonlocal calls
        calls += 1
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(),
        source_names=("semantic_scholar",),
    )

    result = ResearchSourceService().search(strategy)

    assert result == ()
    assert calls == 0


def test_research_source_service_rejects_unsupported_source() -> None:
    """Verify unsupported research sources are rejected."""

    strategy = ResearchStrategy(
        concepts=("video representation learning",),
        search_terms=("video representation learning",),
        source_names=("unsupported_source",),
    )

    with pytest.raises(
        ValueError,
        match="Unsupported research source: unsupported_source",
    ):
        ResearchSourceService().search(strategy)


def test_research_source_service_deduplicates_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify duplicate source identifiers are removed."""

    response_data = create_semantic_scholar_response_data()
    response_data["data"].append(
        response_data["data"][0].copy()
    )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    result = ResearchSourceService().search(
        create_research_strategy()
    )

    assert len(result) == 2
    assert result[0].source_id == "paper-001"
    assert result[1].source_id == "paper-002"


def test_research_source_service_allows_missing_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify optional source fields may be absent or null."""

    response_data = {
        "data": [
            {
                "paperId": "paper-001",
                "title": "Example Paper",
                "authors": None,
                "year": None,
                "url": None,
            },
        ],
    }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    result = ResearchSourceService().search(
        create_research_strategy()
    )

    assert result[0].authors == ()
    assert result[0].publication_year is None
    assert result[0].source_url is None


def test_research_source_service_raises_runtime_error_for_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify non-success HTTP responses become source failures."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            status_code=500,
            data={"error": "source failure"},
        ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Semantic Scholar request failed with HTTP "
            "status 500"
        ),
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_raises_runtime_error_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify connection failures become source failures."""

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        request = httpx.Request(
            "GET",
            (
                "https://api.semanticscholar.org/graph/v1/"
                "paper/search"
            ),
        )
        raise httpx.ConnectError(
            "Connection refused.",
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(
        RuntimeError,
        match="Semantic Scholar service could not be reached",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_rejects_non_json_response(
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
        match="Semantic Scholar response was not valid JSON",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_response_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the response must contain a JSON object."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data=["unexpected", "list"]
        ),
    )

    with pytest.raises(
        TypeError,
        match="response must be a JSON object",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_data_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Semantic Scholar response must contain a data list."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "total": 0,
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="did not include a data list",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_result_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify each search result must be a JSON object."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    "unexpected",
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="search result must be a JSON object",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_paper_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Semantic Scholar results require paper identifiers."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "title": "Example Paper",
                        "authors": [],
                        "year": 2024,
                        "url": None,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="paperId must be a string",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Semantic Scholar results require paper titles."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "paperId": "paper-001",
                        "authors": [],
                        "year": 2024,
                        "url": None,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="title must be a string",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_author_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify authors must be represented as a list or null."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "paperId": "paper-001",
                        "title": "Example Paper",
                        "authors": "Author One",
                        "year": 2024,
                        "url": None,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="authors must be a list or null",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_author_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify each author must be a JSON object."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "paperId": "paper-001",
                        "title": "Example Paper",
                        "authors": [
                            "Author One",
                        ],
                        "year": 2024,
                        "url": None,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="author must be a JSON object",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_author_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify each Semantic Scholar author requires a name."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "paperId": "paper-001",
                        "title": "Example Paper",
                        "authors": [
                            {
                                "authorId": "author-001",
                            },
                        ],
                        "year": 2024,
                        "url": None,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="author name must be a string",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_integer_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify publication year must be an integer or null."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "paperId": "paper-001",
                        "title": "Example Paper",
                        "authors": [],
                        "year": "2024",
                        "url": None,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="year must be an integer or null",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )


def test_research_source_service_requires_string_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify source URL must be a string or null."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            data={
                "data": [
                    {
                        "paperId": "paper-001",
                        "title": "Example Paper",
                        "authors": [],
                        "year": 2024,
                        "url": 123,
                    },
                ],
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="url must be a string or null",
    ):
        ResearchSourceService().search(
            create_research_strategy()
        )
