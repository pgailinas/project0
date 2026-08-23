# ============================================================
# Project0 - Semantic Scholar Source Provider Tests
#
# File: test_semantic_scholar_source_provider.py
#
# Purpose:
#     Verify Semantic Scholar source provider request construction,
#     response normalization, and error handling.
#
# ============================================================

from __future__ import annotations

from typing import Any

import httpx
import pytest

from project0.agents.research.semantic_scholar_source_provider import (
    SemanticScholarSourceProvider,
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
        "data": [
            {
                "paperId": "paper-001",
                "title": "Example Video Representation Paper",
                "authors": [
                    {"name": "Author One"},
                    {"name": "Author Two"},
                ],
                "year": 2024,
                "url": (
                    "https://www.semanticscholar.org/"
                    "paper/paper-001"
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


def test_semantic_scholar_provider_builds_expected_request(
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

    SemanticScholarSourceProvider(
        timeout_seconds=45.0,
        maximum_results=8,
    ).search(create_research_strategy())

    assert captured["timeout"] == 45.0
    assert captured["params"]["limit"] == 8


def test_semantic_scholar_provider_normalizes_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify source responses map to research references."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(),
    )

    result = SemanticScholarSourceProvider().search(
        create_research_strategy()
    )

    assert len(result) == 1
    assert result[0].source_name == "semantic_scholar"
    assert result[0].source_id == "paper-001"


def test_semantic_scholar_provider_returns_empty_for_no_terms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify empty search terms do not call the source."""

    calls = 0

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        nonlocal calls
        calls += 1
        return create_http_response()

    monkeypatch.setattr(httpx, "get", fake_get)

    result = SemanticScholarSourceProvider().search(
        ResearchStrategy(
            concepts=(),
            search_terms=(),
        )
    )

    assert result == ()
    assert calls == 0


def test_semantic_scholar_provider_raises_runtime_error_for_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP failures become source failures."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            status_code=500,
        ),
    )

    with pytest.raises(RuntimeError):
        SemanticScholarSourceProvider().search(
            create_research_strategy()
        )


def test_semantic_scholar_provider_raises_runtime_error_for_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify rate limiting becomes a controlled source failure."""

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: create_http_response(
            status_code=429,
        ),
    )

    with pytest.raises(RuntimeError):
        SemanticScholarSourceProvider().search(
            create_research_strategy()
        )


def test_semantic_scholar_provider_rejects_invalid_response_json(
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
        SemanticScholarSourceProvider().search(
            create_research_strategy()
        )


def test_semantic_scholar_provider_requires_response_object(
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
        SemanticScholarSourceProvider().search(
            create_research_strategy()
        )
