# ============================================================
# Project0 - Stub Research Source Provider Tests
#
# File: test_stub_research_source_provider.py
#
# Purpose:
#     Verify deterministic stub research source provider behavior
#     for Project0 tests, demonstrations, and integration flows.
#
# ============================================================

from __future__ import annotations

import pytest

from project0.agents.research.stub_research_source_provider import (
    StubResearchSourceProvider,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


def create_research_strategy(
    concept: str = "Research concept.",
) -> ResearchStrategy:
    """Create a research strategy for testing."""

    return ResearchStrategy(
        concepts=(
            concept,
        ),
        search_terms=(
            concept,
        ),
    )


def create_research_references() -> tuple[
    ResearchSourceReference,
    ...,
]:
    """Create research references for testing."""

    return (
        ResearchSourceReference(
            source_name="stub",
            source_id="stub-paper-001",
            title="Stub Research Paper",
            source_url="https://example.com/stub-paper",
            authors=(
                "Stub Author",
            ),
            publication_year=2026,
            metadata={
                "stub": True,
            },
        ),
    )


def test_stub_research_source_provider_returns_configured_references(
) -> None:
    """Verify configured references are returned."""

    strategy = create_research_strategy()
    references = create_research_references()

    provider = StubResearchSourceProvider(
        references=references,
    )

    result = provider.search(strategy)

    assert result is references


def test_stub_research_source_provider_records_strategy(
) -> None:
    """Verify search strategies are recorded."""

    strategy = create_research_strategy()

    provider = StubResearchSourceProvider(
        references=create_research_references(),
    )

    provider.search(strategy)

    assert provider.requests == [
        strategy,
    ]


def test_stub_research_source_provider_records_multiple_strategies(
) -> None:
    """Verify multiple strategies are recorded in call order."""

    first_strategy = create_research_strategy(
        "First concept.",
    )
    second_strategy = create_research_strategy(
        "Second concept.",
    )

    provider = StubResearchSourceProvider(
        references=create_research_references(),
    )

    provider.search(first_strategy)
    provider.search(second_strategy)

    assert provider.requests == [
        first_strategy,
        second_strategy,
    ]


def test_stub_research_source_provider_returns_same_configured_references(
) -> None:
    """Verify repeated calls return configured references."""

    references = create_research_references()

    provider = StubResearchSourceProvider(
        references=references,
    )

    first_result = provider.search(
        create_research_strategy("First concept."),
    )
    second_result = provider.search(
        create_research_strategy("Second concept."),
    )

    assert first_result is references
    assert second_result is references


def test_stub_research_source_provider_starts_with_empty_history(
) -> None:
    """Verify a new provider has no recorded strategies."""

    provider = StubResearchSourceProvider(
        references=create_research_references(),
    )

    assert provider.requests == []


def test_stub_research_source_provider_histories_are_independent(
) -> None:
    """Verify provider instances have independent histories."""

    first_provider = StubResearchSourceProvider(
        references=create_research_references(),
    )
    second_provider = StubResearchSourceProvider(
        references=create_research_references(),
    )

    first_provider.search(
        create_research_strategy(),
    )

    assert len(first_provider.requests) == 1
    assert second_provider.requests == []
    assert (
        first_provider.requests
        is not second_provider.requests
    )


def test_stub_research_source_provider_raises_configured_error(
) -> None:
    """Verify a configured provider error is raised."""

    error = RuntimeError(
        "Configured stub research provider failure."
    )

    provider = StubResearchSourceProvider(
        references=create_research_references(),
        error=error,
    )

    with pytest.raises(
        RuntimeError,
        match="Configured stub research provider failure",
    ):
        provider.search(
            create_research_strategy(),
        )


def test_stub_research_source_provider_records_strategy_before_error(
) -> None:
    """Verify failed searches are recorded before raising."""

    strategy = create_research_strategy()

    provider = StubResearchSourceProvider(
        references=create_research_references(),
        error=OSError(
            "Stub research source unavailable."
        ),
    )

    with pytest.raises(OSError):
        provider.search(strategy)

    assert provider.requests == [
        strategy,
    ]


def test_stub_research_source_provider_error_defaults_to_none(
) -> None:
    """Verify provider errors are disabled by default."""

    provider = StubResearchSourceProvider(
        references=create_research_references(),
    )

    assert provider.error is None


def test_stub_research_source_provider_error_can_be_cleared(
) -> None:
    """Verify a configured error can be removed."""

    provider = StubResearchSourceProvider(
        references=create_research_references(),
        error=RuntimeError(
            "Temporary failure."
        ),
    )

    provider.error = None

    result = provider.search(
        create_research_strategy(),
    )

    assert result is provider.references
