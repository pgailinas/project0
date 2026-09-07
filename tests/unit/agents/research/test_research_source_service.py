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
import logging

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
        concepts=("research evidence",),
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


def test_research_source_service_prioritizes_query_anchor_matches() -> None:
    """Repeated technical anchors outrank generic provider matches."""

    generic = replace(
        create_reference("generic"),
        title="Self-Supervised Latent Representations for ECG",
    )
    aligned = replace(
        create_reference("aligned"),
        title=(
            "CLIP Autoencoder Latent Alignment for Video Representations"
        ),
    )
    provider = QueryMappedResearchSourceProvider(
        {
            "self-supervised autoencoder CLIP latent representations": (
                generic,
                aligned,
            ),
            "autoencoder CLIP video embedding alignment": (),
        }
    )
    service = ResearchSourceService(
        providers={"stub": provider},
        evaluation_candidate_limit=1,
    )
    strategy = ResearchStrategy(
        concepts=("video language representation alignment",),
        search_terms=(
            "self-supervised autoencoder CLIP latent representations",
            "autoencoder CLIP video embedding alignment",
        ),
        source_names=("stub",),
    )

    result = service.search(strategy)

    assert result == (aligned,)
    assert service.last_candidate_trace[0]["selection_status"] == (
        "outside_alignment_profile"
    )
    assert service.last_candidate_trace[1]["evaluation_rank"] == 1


def test_research_source_service_excludes_alignment_profile_mismatch() -> None:
    """Alignment strategies require a concrete transfer path."""

    flood_forecasting = replace(
        create_reference("flood"),
        title="Zero-Shot Flood Forecasting Using Vision-Language Models",
    )
    direct_alignment = replace(
        create_reference("alignment"),
        title="Video Autoencoder CLIP Latent Alignment",
    )
    text_to_image = replace(
        create_reference("text-to-image"),
        title="CLIP Contrastive Representation Alignment for Text-to-Image Diffusion",
    )
    generic_vlm = replace(
        create_reference("vlm"),
        title="Vision-Language Model Embeddings for Construction Safety",
    )
    generative_alignment = replace(
        create_reference("generative"),
        title="Video CLIP Latent Alignment for Diffusion Generation",
    )
    provider = QueryMappedResearchSourceProvider(
        {
            "video CLIP autoencoder alignment": (
                flood_forecasting,
                text_to_image,
                generic_vlm,
                generative_alignment,
                direct_alignment,
            ),
        }
    )
    service = ResearchSourceService(
        providers={"stub": provider},
        evaluation_candidate_limit=2,
    )
    strategy = ResearchStrategy(
        concepts=("video language representation alignment",),
        search_terms=("video CLIP autoencoder alignment",),
        source_names=("stub",),
    )

    result = service.search(strategy)

    assert result == (direct_alignment,)
    assert service.last_candidate_trace[0]["selection_status"] == (
        "outside_alignment_profile"
    )
    assert service.last_candidate_trace[1]["selection_status"] == (
        "outside_alignment_profile"
    )
    assert service.last_candidate_trace[2]["selection_status"] == (
        "outside_alignment_profile"
    )
    assert service.last_candidate_trace[3]["selection_status"] == (
        "outside_alignment_profile"
    )


def test_research_source_service_allows_synthesis_for_synthesis_strategy() -> None:
    """A synthesis-focused strategy does not apply representation exclusions."""

    generative_alignment = replace(
        create_reference("generative"),
        title="Video CLIP Latent Alignment for Diffusion Generation",
    )
    provider = QueryMappedResearchSourceProvider(
        {
            "video CLIP latent alignment diffusion generation": (
                generative_alignment,
            ),
        }
    )
    service = ResearchSourceService(
        providers={"stub": provider},
        evaluation_candidate_limit=1,
    )
    strategy = ResearchStrategy(
        concepts=("video diffusion generation",),
        search_terms=(
            "video CLIP latent alignment diffusion generation",
        ),
        source_names=("stub",),
    )

    assert service.search(strategy) == (generative_alignment,)


def test_research_source_service_retains_transferable_visual_alignment() -> None:
    """Visual transfer requires explicit CLIP alignment and representation evidence."""

    transferable_alignment = replace(
        create_reference("transferable"),
        title="Image Autoencoder CLIP Latent Representation Distillation",
    )
    provider = QueryMappedResearchSourceProvider(
        {
            "video CLIP autoencoder alignment": (
                transferable_alignment,
            ),
        }
    )
    service = ResearchSourceService(
        providers={"stub": provider},
        evaluation_candidate_limit=1,
    )
    strategy = ResearchStrategy(
        concepts=("video language representation alignment",),
        search_terms=("video CLIP autoencoder alignment",),
        source_names=("stub",),
    )

    assert service.search(strategy) == (transferable_alignment,)


def test_research_source_service_traces_excluded_candidate_provenance(
    caplog,
) -> None:
    """Selection changes retain query and provider provenance."""

    selected = create_reference("selected")
    uta = ResearchSourceReference(
        source_name="openalex",
        source_id="https://arxiv.org/abs/2405.19009",
        title=(
            "Video CLIP Autoencoder Latent Representation Alignment"
        ),
        source_url="https://arxiv.org/abs/2405.19009",
        publication_year=2024,
        metadata={"arxiv_id": "2405.19009"},
    )
    service = ResearchSourceService(
        providers={
            "openalex": QueryMappedResearchSourceProvider(
                {
                    "CLIP feature alignment": (
                        selected,
                        uta,
                    ),
                }
            ),
        },
        evaluation_candidate_limit=1,
    )
    strategy = ResearchStrategy(
        concepts=("CLIP feature alignment",),
        search_terms=("CLIP feature alignment",),
        source_names=("openalex",),
    )

    with caplog.at_level(logging.DEBUG):
        result = service.search(strategy)

    assert result == (uta,)
    assert service.last_candidate_trace[0] == {
        "deduplicated_rank": 1,
        "evaluation_rank": None,
        "selection_status": "outside_balanced_candidate_limit",
        "title": "Paper selected",
        "canonical_source_name": "stub",
        "source_id": "selected",
        "retrieval_providers": ("openalex",),
        "retrieval_queries": ("CLIP feature alignment",),
        "stable_identifiers": (),
    }
    assert service.last_candidate_trace[1] == {
        "deduplicated_rank": 2,
        "evaluation_rank": 1,
        "selection_status": "balanced_selection",
        "title": (
            "Video CLIP Autoencoder Latent Representation Alignment"
        ),
        "canonical_source_name": "openalex",
        "source_id": "https://arxiv.org/abs/2405.19009",
        "retrieval_providers": ("openalex",),
        "retrieval_queries": ("CLIP feature alignment",),
        "stable_identifiers": ("arxiv:2405.19009",),
    }
    assert "Video CLIP Autoencoder" in caplog.text
    assert "Paper selected" in caplog.text
    assert "outside_balanced_candidate_limit" in caplog.text


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


def test_research_source_service_retains_clip_latent_alignment_transfer():
    """CLIP latent alignment can qualify as transferable visual evidence."""

    transferable_alignment = replace(
        create_reference("clip-latent-alignment"),
        title="Context Autoencoder with CLIP Latent Alignment",
    )
    provider = QueryMappedResearchSourceProvider(
        {
            "CLIP autoencoder latent alignment": (
                transferable_alignment,
            ),
        }
    )
    service = ResearchSourceService(
        providers={"stub": provider},
        evaluation_candidate_limit=1,
    )
    strategy = ResearchStrategy(
        concepts=("video language representation alignment",),
        search_terms=("CLIP autoencoder latent alignment",),
        source_names=("stub",),
    )

    assert service.search(strategy) == (transferable_alignment,)

