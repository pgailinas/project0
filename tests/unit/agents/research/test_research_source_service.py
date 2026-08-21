# ============================================================
# Project0 - Research Source Service Tests
#
# File: test_research_source_service.py
#
# Purpose:
#     Verify research source provider dispatch, aggregation,
#     deduplication, and error handling.
#
# ============================================================

from __future__ import annotations

import pytest

from project0.agents.research.research_source_service import (
    ResearchSourceService,
)
from project0.agents.research.stub_research_source_provider import (
    StubResearchSourceProvider,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


def create_research_strategy(
    source_names: tuple[str, ...] = (
        "stub",
    ),
) -> ResearchStrategy:
    """Create a representative research strategy."""

    return ResearchStrategy(
        concepts=(
            "video representation learning",
        ),
        search_terms=(
            "video representation learning",
        ),
        source_names=source_names,
    )


def create_reference(
    source_id: str,
    source_name: str = "stub",
) -> ResearchSourceReference:
    """Create a research reference for testing."""

    return ResearchSourceReference(
        source_name=source_name,
        source_id=source_id,
        title=f"Paper {source_id}",
        source_url=None,
        authors=(),
        publication_year=2026,
        metadata={},
    )


def test_research_source_service_dispatches_to_provider() -> None:
    """Verify requests are delegated to configured providers."""

    provider = StubResearchSourceProvider(
        references=(
            create_reference("paper-001"),
        ),
    )

    service = ResearchSourceService(
        providers={
            "stub": provider,
        },
    )

    result = service.search(
        create_research_strategy()
    )

    assert result == (
        create_reference("paper-001"),
    )
    assert provider.requests == [
        create_research_strategy()
    ]


def test_research_source_service_defaults_to_semantic_scholar_name() -> None:
    """Verify missing source names use the default provider name."""

    provider = StubResearchSourceProvider(
        references=(
            create_reference(
                "paper-001",
                "semantic_scholar",
            ),
        ),
    )

    service = ResearchSourceService(
        providers={
            "semantic_scholar": provider,
        },
    )

    strategy = ResearchStrategy(
        concepts=("video",),
        search_terms=("video",),
    )

    result = service.search(strategy)

    assert len(result) == 1
    assert provider.requests == [
        strategy
    ]


def test_research_source_service_rejects_unknown_provider() -> None:
    """Verify unsupported providers are rejected."""

    service = ResearchSourceService(
        providers={},
    )

    with pytest.raises(
        ValueError,
        match="Unsupported research source: unknown",
    ):
        service.search(
            create_research_strategy(
                ("unknown",)
            )
        )


def test_research_source_service_aggregates_multiple_providers() -> None:
    """Verify multiple providers contribute references."""

    first_provider = StubResearchSourceProvider(
        references=(
            create_reference("paper-001"),
        ),
    )
    second_provider = StubResearchSourceProvider(
        references=(
            create_reference("paper-002"),
        ),
    )

    service = ResearchSourceService(
        providers={
            "first": first_provider,
            "second": second_provider,
        },
    )

    result = service.search(
        create_research_strategy(
            ("first", "second")
        )
    )

    assert result == (
        create_reference("paper-001"),
        create_reference("paper-002"),
    )


def test_research_source_service_deduplicates_references() -> None:
    """Verify duplicate references are removed."""

    provider = StubResearchSourceProvider(
        references=(
            create_reference("paper-001"),
            create_reference("paper-001"),
            create_reference("paper-002"),
        ),
    )

    service = ResearchSourceService(
        providers={
            "stub": provider,
        },
    )

    result = service.search(
        create_research_strategy()
    )

    assert result == (
        create_reference("paper-001"),
        create_reference("paper-002"),
    )


def test_research_source_service_preserves_provider_order() -> None:
    """Verify reference ordering follows provider ordering."""

    first_provider = StubResearchSourceProvider(
        references=(
            create_reference("first"),
        ),
    )
    second_provider = StubResearchSourceProvider(
        references=(
            create_reference("second"),
        ),
    )

    service = ResearchSourceService(
        providers={
            "first": first_provider,
            "second": second_provider,
        },
    )

    result = service.search(
        create_research_strategy(
            ("first", "second")
        )
    )

    assert [item.source_id for item in result] == [
        "first",
        "second",
    ]
