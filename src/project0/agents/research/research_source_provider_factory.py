# ============================================================
# Project0 - Research Source Provider Factory
#
# File: research_source_provider_factory.py
#
# Purpose:
#     Create configured Research Agent source providers.
#
# ============================================================

from __future__ import annotations

from project0.agents.research.arxiv_source_provider import (
    ArxivSourceProvider,
)
from project0.agents.research.crossref_source_provider import (
    CrossrefSourceProvider,
)
from project0.agents.research.openalex_source_provider import (
    OpenAlexSourceProvider,
)
from project0.agents.research.openreview_source_provider import (
    OpenReviewSourceProvider,
)
from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.agents.research.semantic_scholar_source_provider import (
    SemanticScholarSourceProvider,
)
from project0.agents.research.stub_research_source_provider import (
    StubResearchSourceProvider,
)
from project0.config.constants import (
    SUPPORTED_RESEARCH_SOURCE_PROVIDERS,
)
from project0.config.settings import SETTINGS
from project0.models.research_models import ResearchSourceReference


def create_research_source_providers(
    provider_names: tuple[str, ...] | None = None,
) -> dict[str, ResearchSourceProviderProtocol]:
    """Create configured Research Agent source providers."""

    available_providers: dict[str, ResearchSourceProviderProtocol] = {
        "semantic_scholar": SemanticScholarSourceProvider(
            api_key=SETTINGS.semantic_scholar_api_key,
        ),
        "openalex": OpenAlexSourceProvider(),
        "openreview": OpenReviewSourceProvider(),
        "crossref": CrossrefSourceProvider(),
        "arxiv": ArxivSourceProvider(),
        "stub": StubResearchSourceProvider(
            references=(
                ResearchSourceReference(
                    source_name="stub",
                    source_id="stub-paper-001",
                    title=(
                        "Self-Supervised Video Representation "
                        "Learning for VideoQA"
                    ),
                    source_url="https://example.com/stub-paper-001",
                    authors=("Project0 Research Stub",),
                    publication_year=2026,
                ),
            ),
        ),
    }

    selected_provider_names = (
        provider_names
        if provider_names is not None
        else tuple(available_providers.keys())
    )

    unsupported_providers = (
        set(selected_provider_names)
        -
        set(SUPPORTED_RESEARCH_SOURCE_PROVIDERS)
    )

    if unsupported_providers:
        raise ValueError(
            f"Unsupported research source providers: "
            f"{unsupported_providers}"
        )

    return {
        name: available_providers[name]
        for name in selected_provider_names
    }
