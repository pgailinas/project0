# ============================================================
# Project0 - arXiv Research Source Provider Tests
#
# File: test_arxiv_source_provider.py
#
# Purpose:
#     Verify arXiv provider query generation, response parsing,
#     and error handling behavior.
#
# ============================================================

from __future__ import annotations

import httpx
import pytest

from project0.agents.research.arxiv_source_provider import (
    ArxivSourceProvider,
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
            "arxiv",
        ),
        rationale="Test arXiv provider behavior.",
    )


def test_arxiv_provider_builds_query() -> None:
    """Verify deterministic query generation."""

    provider = ArxivSourceProvider()

    query = provider._build_query(
        create_strategy()
    )

    assert query == (
        "video representation learning "
        "multimodal alignment"
    )


def test_arxiv_provider_removes_duplicate_terms() -> None:
    """Verify duplicate search terms are removed."""

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(
            "video",
            "video",
            "learning",
        ),
        constraints=(),
        source_names=("arxiv",),
        rationale=None,
    )

    provider = ArxivSourceProvider()

    query = provider._build_query(strategy)

    assert query == "video learning"


def test_arxiv_provider_returns_empty_query() -> None:
    """Verify empty strategies produce no query."""

    provider = ArxivSourceProvider()

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(),
        constraints=(),
        source_names=("arxiv",),
        rationale=None,
    )

    assert provider._build_query(strategy) == ""


def test_arxiv_provider_parses_response() -> None:
    """Verify arXiv XML is converted into references."""

    xml_response = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345</id>
        <title>
          Example Video Representation Paper
        </title>
        <published>2024-01-01T00:00:00Z</published>
        <author>
          <name>Author One</name>
        </author>
      </entry>
    </feed>
    """

    result = ArxivSourceProvider._parse_response(
        xml_response
    )

    assert len(result) == 1
    assert result[0].source_name == "arxiv"
    assert result[0].source_id == (
        "http://arxiv.org/abs/2401.12345"
    )
    assert result[0].title == (
        "Example Video Representation Paper"
    )
    assert result[0].publication_year == 2024
    assert result[0].authors == (
        "Author One",
    )


def test_arxiv_provider_handles_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP failures become provider errors."""

    def mock_get(*args, **kwargs):
        raise httpx.HTTPError(
            "Connection failed."
        )

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        mock_get,
    )

    provider = ArxivSourceProvider()

    with pytest.raises(
        RuntimeError,
        match="arXiv request failed",
    ):
        provider.search(
            create_strategy()
        )


def test_arxiv_provider_empty_strategy_returns_no_results() -> None:
    """Verify empty search strategies return no results."""

    provider = ArxivSourceProvider()

    result = provider.search(
        ResearchStrategy(
            concepts=(),
            search_terms=(),
            constraints=(),
            source_names=("arxiv",),
            rationale=None,
        )
    )

    assert result == ()


def test_arxiv_provider_retries_transient_request_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify transient request failures are retried."""

    attempts = 0

    xml_response = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345</id>
        <title>Recovered Paper</title>
        <published>2024-01-01T00:00:00Z</published>
      </entry>
    </feed>
    """

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            request = httpx.Request(
                "GET",
                "https://export.arxiv.org/api/query",
            )
            raise httpx.ReadTimeout(
                "Read timed out.",
                request=request,
            )

        return httpx.Response(
            200,
            text=xml_response,
            request=httpx.Request(
                "GET",
                "https://export.arxiv.org/api/query",
            ),
        )

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = ArxivSourceProvider(
        retry_delay_seconds=0.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert len(result) == 1
    assert result[0].title == "Recovered Paper"


def test_arxiv_provider_sends_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify arXiv requests identify the Project0 client."""

    captured_headers = {}

    xml_response = (
        '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    )

    def mock_get(
        url,
        *,
        params,
        headers,
        timeout,
    ):
        captured_headers.update(headers)

        return httpx.Response(
            200,
            text=xml_response,
            request=httpx.Request(
                "GET",
                url,
            ),
        )

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        mock_get,
    )

    provider = ArxivSourceProvider(
        user_agent="Project0-Test-Agent",
    )

    provider.search(
        create_strategy()
    )

    assert captured_headers == {
        "User-Agent": "Project0-Test-Agent",
    }


def test_arxiv_provider_retries_rate_limit_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP 429 responses are retried before failing."""

    attempts = 0

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1

        return httpx.Response(
            429,
            text="rate limited",
            request=httpx.Request(
                "GET",
                "https://export.arxiv.org/api/query",
            ),
        )

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.time.sleep",
        lambda seconds: None,
    )

    provider = ArxivSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=0.0,
    )

    with pytest.raises(
        RuntimeError,
        match="arXiv request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3
