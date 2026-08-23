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
from project0.models.research_models import ResearchSourceReference


def create_research_source_providers() -> dict[str, ResearchSourceProviderProtocol]:
    """Create configured Research Agent source providers."""

    providers: dict[str, ResearchSourceProviderProtocol] = {}

    providers["semantic_scholar"] = SemanticScholarSourceProvider()

    providers["stub"] = StubResearchSourceProvider(
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
    )

    unsupported_providers = (
        set(providers.keys())
        -
        set(SUPPORTED_RESEARCH_SOURCE_PROVIDERS)
    )

    if unsupported_providers:
        raise ValueError(
            f"Unsupported research source providers: "
            f"{unsupported_providers}"
        )

    return providers
