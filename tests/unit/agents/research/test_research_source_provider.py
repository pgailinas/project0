# ============================================================
# Project0 - Research Source Provider Tests
#
# File: test_research_source_provider.py
#
# Purpose:
#     Verify Research Agent source provider interface behavior
#     for Project0 research source implementations.
#
# ============================================================

from __future__ import annotations

from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


class ExampleResearchSourceProvider:
    """Example provider implementation for protocol testing."""

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Return deterministic research references."""

        return (
            ResearchSourceReference(
                source_name="example",
                source_id="example-001",
                title="Example Research Paper",
                source_url="https://example.com/paper",
                authors=("Example Author",),
                publication_year=2026,
                metadata={},
            ),
        )


def test_research_source_provider_protocol_is_satisfied() -> None:
    """Verify provider implementations satisfy the protocol."""

    provider = ExampleResearchSourceProvider()

    assert isinstance(
        provider,
        ResearchSourceProviderProtocol,
    )


def test_research_source_provider_returns_reference_collection() -> None:
    """Verify providers return research source references."""

    provider = ExampleResearchSourceProvider()

    strategy = ResearchStrategy(
        concepts=("video representation learning",),
        search_terms=("video representation learning",),
    )

    result = provider.search(strategy)

    assert result == (
        ResearchSourceReference(
            source_name="example",
            source_id="example-001",
            title="Example Research Paper",
            source_url="https://example.com/paper",
            authors=("Example Author",),
            publication_year=2026,
            metadata={},
        ),
    )


def test_research_source_provider_returns_deterministic_results() -> None:
    """Verify repeated provider calls return deterministic results."""

    provider = ExampleResearchSourceProvider()

    strategy = ResearchStrategy(
        concepts=("concept one",),
        search_terms=("concept one",),
    )

    first_result = provider.search(strategy)
    second_result = provider.search(strategy)

    assert first_result == second_result
