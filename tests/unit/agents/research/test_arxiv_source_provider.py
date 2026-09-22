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
        "all:video AND all:alignment AND all:representation"
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

    assert query == "all:video AND all:learning"


@pytest.mark.parametrize(
    ("search_term", "expected_query"),
    (
        (
            "video representations teacher guided feature alignment",
            "all:video AND all:teacher AND all:alignment",
        ),
        (
            "visual representations CLIP token alignment",
            "all:clip AND all:token AND all:alignment",
        ),
        (
            "visual representations CLIP latent alignment",
            "all:clip AND all:latent AND all:alignment",
        ),
        (
            "visual representations CLIP knowledge distillation",
            "all:clip AND all:distillation AND all:representations",
        ),
    ),
)
def test_arxiv_provider_builds_fielded_mechanism_query(
    search_term: str,
    expected_query: str,
) -> None:
    """Mechanism searches retain a target, mechanism, and relation."""

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(search_term,),
        source_names=("arxiv",),
    )

    assert ArxivSourceProvider._build_query(strategy) == expected_query


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


@pytest.mark.parametrize(
    ("seed", "expected_identifier"),
    (
        ("arXiv:2303.16058", "2303.16058"),
        (
            "https://arxiv.org/html/2405.19009v2",
            "2405.19009",
        ),
    ),
)
def test_arxiv_provider_uses_direct_identifier_lookup(
    monkeypatch: pytest.MonkeyPatch,
    seed: str,
    expected_identifier: str,
) -> None:
    """Explicit arXiv seeds bypass fuzzy keyword search."""

    captured_params = {}
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
        del headers
        del timeout
        captured_params.update(params)

        return httpx.Response(
            200,
            text=xml_response,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        mock_get,
    )

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=(seed,),
        seed_terms=(seed,),
        source_names=("arxiv",),
    )

    ArxivSourceProvider().search(strategy)

    assert captured_params == {
        "id_list": expected_identifier,
        "max_results": 1,
    }


def test_arxiv_provider_does_not_treat_identifier_as_keyword() -> None:
    """Versioned arXiv identifiers are recognized as direct seeds."""

    strategy = ResearchStrategy(
        concepts=(),
        search_terms=("arXiv:2405.19009v2",),
        source_names=("arxiv",),
    )

    assert ArxivSourceProvider._extract_arxiv_ids(strategy) == (
        "2405.19009",
    )


def test_arxiv_provider_parses_response() -> None:
    """Verify arXiv XML is converted into references."""

    xml_response = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345</id>
        <title>
          Example Video Representation Paper
        </title>
        <summary>
          We align learned video representations with a
          frozen vision-language model embedding space.
        </summary>
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
    assert result[0].metadata["abstract"] == (
        "We align learned video representations with a "
        "frozen vision-language model embedding space."
    )


def test_arxiv_provider_omits_missing_abstract() -> None:
    """Verify entries without summaries remain valid."""

    xml_response = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345</id>
        <title>Paper Without Summary</title>
        <published>2024-01-01T00:00:00Z</published>
      </entry>
    </feed>
    """

    result = ArxivSourceProvider._parse_response(
        xml_response
    )

    assert len(result) == 1
    assert "abstract" not in result[0].metadata


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
        "Accept": "application/atom+xml",
        "Accept-Encoding": "identity",
    }


def test_arxiv_provider_retries_not_acceptable_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify transient HTTP 406 responses are retried."""

    get_attempts = 0
    post_attempts = 0
    post_data = {}
    sleep_calls = []
    xml_response = (
        '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    )

    def mock_get(*args, **kwargs):
        nonlocal get_attempts
        get_attempts += 1

        return httpx.Response(
            406,
            text="not acceptable",
            request=httpx.Request(
                "GET",
                "https://export.arxiv.org/api/query",
            ),
        )

    def mock_post(url, *, data, headers, timeout):
        nonlocal post_attempts
        post_attempts += 1
        post_data.update(data)

        return httpx.Response(
            200,
            text=xml_response,
            request=httpx.Request(
                "POST",
                url,
            ),
        )

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        mock_get,
    )
    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.post",
        mock_post,
    )
    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.time.sleep",
        sleep_calls.append,
    )

    result = ArxivSourceProvider(
        maximum_attempts=2,
        retry_delay_seconds=0.0,
    ).search(create_strategy())

    assert get_attempts == 1
    assert post_attempts == 1
    assert post_data["search_query"] == (
        "all:video AND all:alignment AND all:representation"
    )
    assert sleep_calls == [3.0]
    assert result == ()


def test_arxiv_provider_spaces_independent_searches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify consecutive searches respect the arXiv request interval."""

    xml_response = (
        '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    )
    sleep_calls = []
    monotonic_values = iter((100.0, 101.0, 104.0))

    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.httpx.get",
        lambda url, **kwargs: httpx.Response(
            200,
            text=xml_response,
            request=httpx.Request("GET", url),
        ),
    )
    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.time.monotonic",
        lambda: next(monotonic_values),
    )
    monkeypatch.setattr(
        "project0.agents.research.arxiv_source_provider.time.sleep",
        sleep_calls.append,
    )

    provider = ArxivSourceProvider(
        minimum_request_interval_seconds=3.0,
    )

    provider.search(create_strategy())
    provider.search(create_strategy())

    assert sleep_calls == [2.0]


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

def test_arxiv_provider_honors_retry_after_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP 429 Retry-After values control retry delay."""

    attempts = 0
    sleep_calls = []

    xml_response = (
        '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    )

    def mock_get(*args, **kwargs):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return httpx.Response(
                429,
                text="rate limited",
                headers={
                    "Retry-After": "5",
                },
                request=httpx.Request(
                    "GET",
                    "https://export.arxiv.org/api/query",
                ),
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
        sleep_calls.append,
    )

    provider = ArxivSourceProvider(
        maximum_attempts=2,
        retry_delay_seconds=1.0,
    )

    result = provider.search(
        create_strategy()
    )

    assert attempts == 2
    assert result == ()
    assert sleep_calls == [5.0]


def test_arxiv_provider_uses_exponential_backoff_for_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify HTTP 429 retries use exponential backoff."""

    attempts = 0
    sleep_calls = []

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
        sleep_calls.append,
    )

    provider = ArxivSourceProvider(
        maximum_attempts=3,
        retry_delay_seconds=2.0,
    )

    with pytest.raises(
        RuntimeError,
        match="arXiv request failed",
    ):
        provider.search(
            create_strategy()
        )

    assert attempts == 3
    assert sleep_calls == [
        2.0,
        4.0,
    ]
