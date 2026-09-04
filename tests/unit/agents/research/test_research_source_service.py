# ============================================================
# Project0 - Research Source Service Tests
#
# File: test_research_source_service.py
#
# Purpose:
#     Verify research source provider dispatch, aggregation,
#     deduplication, fallback, and error handling.
#
# ============================================================

from __future__ import annotations

from dataclasses import replace

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


class FailingResearchSourceProvider:
    """Test provider that simulates an unavailable source."""

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        raise RuntimeError(
            "Provider unavailable."
        )


class PartiallyFailingResearchSourceProvider:
    """Test provider that fails one query and succeeds on another."""

    def __init__(self) -> None:
        self.requests: list[ResearchStrategy] = []

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        self.requests.append(strategy)

        if strategy.search_terms == ("first query",):
            raise RuntimeError(
                "Provider query unavailable."
            )

        return (
            create_reference("paper-002"),
        )


class QueryMappedResearchSourceProvider:
    """Return references configured for each individual query."""

    def __init__(
        self,
        references_by_query: dict[
            str,
            tuple[ResearchSourceReference, ...],
        ],
    ) -> None:
        self._references_by_query = references_by_query
        self.requests: list[ResearchStrategy] = []

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        self.requests.append(strategy)
        query = strategy.search_terms[0]
        return self._references_by_query.get(query, ())


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


def test_research_source_service_dispatches_each_query_independently() -> None:
    """Verify each provider receives one strategy query per request."""

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
    strategy = ResearchStrategy(
        concepts=(
            "video representation learning",
            "video language alignment",
        ),
        search_terms=(
            "video representation learning",
            "video language alignment",
        ),
        source_names=("stub",),
    )

    result = service.search(strategy)

    assert result == (
        create_reference("paper-001"),
    )
    assert provider.requests == [
        replace(
            strategy,
            search_terms=("video representation learning",),
        ),
        replace(
            strategy,
            search_terms=("video language alignment",),
        ),
    ]


def test_research_source_service_dispatches_seed_queries_first() -> None:
    """Verify ordered seed queries reach each provider before discovery."""

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
    strategy = ResearchStrategy(
        concepts=("CLIP teacher alignment",),
        search_terms=(
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
            "arXiv:2405.19009",
            "CLIP teacher alignment",
        ),
        seed_terms=(
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
            "arXiv:2405.19009",
        ),
        source_names=("stub",),
    )

    service.search(strategy)

    assert [
        request.search_terms
        for request in provider.requests
    ] == [
        (
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
        ),
        ("arXiv:2405.19009",),
        ("CLIP teacher alignment",),
    ]


def test_research_source_service_omits_arxiv_identifier_from_crossref() -> None:
    """Crossref receives titles and discovery terms, not arXiv IDs."""

    crossref_provider = StubResearchSourceProvider(references=())
    service = ResearchSourceService(
        providers={
            "crossref": crossref_provider,
        },
    )
    strategy = ResearchStrategy(
        concepts=("CLIP teacher alignment",),
        search_terms=(
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
            "arXiv:2405.19009",
            "CLIP teacher alignment",
        ),
        seed_terms=("arXiv:2405.19009",),
        source_names=("crossref",),
    )

    service.search(strategy)

    assert [
        request.search_terms
        for request in crossref_provider.requests
    ] == [
        (
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
        ),
        ("CLIP teacher alignment",),
    ]


def test_research_source_service_bounds_balanced_evaluation_pool() -> None:
    """Seeds survive a bounded pool balanced across result groups."""

    seed = ResearchSourceReference(
        source_name="arxiv",
        source_id="2405.19009",
        title=(
            "Enhancing Vision-Language Model with Unmasked Token Alignment"
        ),
        source_url="https://arxiv.org/abs/2405.19009",
    )
    first_provider = QueryMappedResearchSourceProvider(
        {
            "arXiv:2405.19009": (
                create_reference("seed-noise"),
                seed,
            ),
            "first discovery": (
                create_reference("first-001"),
                create_reference("first-002"),
            ),
            "second discovery": (
                create_reference("second-001"),
                create_reference("second-002"),
            ),
        }
    )
    second_provider = QueryMappedResearchSourceProvider(
        {
            "arXiv:2405.19009": (seed,),
            "first discovery": (
                create_reference("third-001"),
            ),
            "second discovery": (
                create_reference("fourth-001"),
            ),
        }
    )
    service = ResearchSourceService(
        providers={
            "first": first_provider,
            "second": second_provider,
        },
        evaluation_candidate_limit=5,
    )
    strategy = ResearchStrategy(
        concepts=("CLIP alignment",),
        search_terms=(
            "arXiv:2405.19009",
            "first discovery",
            "second discovery",
        ),
        seed_terms=("arXiv:2405.19009",),
        source_names=("first", "second"),
    )

    result = service.search(strategy)

    assert result[0] == seed
    assert len(result) == 5
    assert {reference.source_id for reference in result} == {
        "2405.19009",
        "seed-noise",
        "first-001",
        "second-001",
        "third-001",
    }
    assert service.last_search_statistics == {
        "retrieved_count": 9,
        "deduplicated_count": 8,
        "seed_preserved_count": 1,
        "evaluation_candidate_count": 5,
    }


def test_research_source_service_rejects_invalid_candidate_limit() -> None:
    """Verify the pre-evaluation candidate limit must be positive."""

    service = ResearchSourceService(
        providers={
            "stub": StubResearchSourceProvider(references=()),
        },
        evaluation_candidate_limit=0,
    )

    with pytest.raises(
        ValueError,
        match="candidate limit must be positive",
    ):
        service.search(create_research_strategy())


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

    service = ResearchSourceService(
        providers={
            "first": StubResearchSourceProvider(
                references=(
                    create_reference("paper-001"),
                ),
            ),
            "second": StubResearchSourceProvider(
                references=(
                    create_reference("paper-002"),
                ),
            ),
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

    service = ResearchSourceService(
        providers={
            "stub": StubResearchSourceProvider(
                references=(
                    create_reference("paper-001"),
                    create_reference("paper-001"),
                    create_reference("paper-002"),
                ),
            ),
        },
    )

    result = service.search(
        create_research_strategy()
    )

    assert result == (
        create_reference("paper-001"),
        create_reference("paper-002"),
    )


def test_research_source_service_retains_richest_publication_version() -> None:
    """Verify a richer duplicate replaces an earlier sparse version."""

    title = (
        "VideoCLIP: Contrastive Pre-training for Zero-shot "
        "Video-Text Understanding"
    )
    authors = (
        "Hu Xu",
        "Gargi Ghosh",
        "Po-Yao Huang",
    )
    sparse = ResearchSourceReference(
        source_name="openalex",
        source_id="https://aclanthology.org/2021.emnlp-main.544",
        title=title,
        source_url="https://aclanthology.org/2021.emnlp-main.544",
        authors=authors,
        publication_year=2021,
        metadata={
            "abstract": "Hu Xu, Gargi Ghosh, Po-Yao Huang. EMNLP 2021.",
        },
    )
    rich = ResearchSourceReference(
        source_name="openalex",
        source_id="https://arxiv.org/abs/2109.14084",
        title=title,
        source_url="https://arxiv.org/abs/2109.14084",
        authors=authors,
        publication_year=2021,
        metadata={
            "abstract": (
                "VideoCLIP pre-trains a unified video and text model "
                "using contrastive learning on temporally overlapping "
                "video-text pairs for zero-shot downstream tasks."
            ),
            "venue": "EMNLP",
        },
    )
    service = ResearchSourceService(
        providers={
            "stub": StubResearchSourceProvider(
                references=(sparse, rich),
            ),
        },
    )

    result = service.search(create_research_strategy())

    assert result == (rich,)


def test_research_source_service_keeps_distinct_same_year_papers() -> None:
    """Verify different titles are not merged despite shared authors."""

    first = replace(
        create_reference("first"),
        title="First Representation Paper",
        authors=("Author One",),
    )
    second = replace(
        create_reference("second"),
        title="Second Representation Paper",
        authors=("Author One",),
    )
    service = ResearchSourceService(
        providers={
            "stub": StubResearchSourceProvider(
                references=(first, second),
            ),
        },
    )

    result = service.search(create_research_strategy())

    assert result == (first, second)


def test_research_source_service_preserves_provider_order() -> None:
    """Verify reference ordering follows provider ordering."""

    service = ResearchSourceService(
        providers={
            "first": StubResearchSourceProvider(
                references=(
                    create_reference("first"),
                ),
            ),
            "second": StubResearchSourceProvider(
                references=(
                    create_reference("second"),
                ),
            ),
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


def test_research_source_service_falls_back_after_provider_failure() -> None:
    """Verify failed providers allow fallback providers."""

    service = ResearchSourceService(
        providers={
            "semantic_scholar": FailingResearchSourceProvider(),
            "stub": StubResearchSourceProvider(
                references=(
                    create_reference(
                        "fallback-paper",
                    ),
                ),
            ),
        },
    )

    result = service.search(
        create_research_strategy(
            (
                "semantic_scholar",
                "stub",
            )
        )
    )

    assert result == (
        create_reference("fallback-paper"),
    )


def test_research_source_service_continues_after_query_failure() -> None:
    """Verify one failed query does not discard successful query results."""

    provider = PartiallyFailingResearchSourceProvider()
    service = ResearchSourceService(
        providers={
            "stub": provider,
        },
    )
    strategy = ResearchStrategy(
        concepts=("first", "second"),
        search_terms=("first query", "second query"),
        source_names=("stub",),
    )

    result = service.search(strategy)

    assert result == (
        create_reference("paper-002"),
    )
    assert provider.requests == [
        replace(
            strategy,
            search_terms=("first query",),
        ),
        replace(
            strategy,
            search_terms=("second query",),
        ),
    ]


def test_research_source_service_fails_when_all_providers_fail() -> None:
    """Verify failure occurs when no providers succeed."""

    service = ResearchSourceService(
        providers={
            "semantic_scholar": FailingResearchSourceProvider(),
            "stub": FailingResearchSourceProvider(),
        },
    )

    with pytest.raises(
        RuntimeError,
        match="All research sources failed",
    ):
        service.search(
            create_research_strategy(
                (
                    "semantic_scholar",
                    "stub",
                )
            )
        )
