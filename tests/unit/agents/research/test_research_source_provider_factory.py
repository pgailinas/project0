# ============================================================
# Project0 - Research Source Provider Factory Tests
#
# File: test_research_source_provider_factory.py
#
# Purpose:
#     Validate Research Agent source provider factory behavior.
#
# ============================================================

from project0.agents.research.arxiv_source_provider import (
    ArxivSourceProvider,
)
from project0.agents.research.openalex_source_provider import (
    OpenAlexSourceProvider,
)
from project0.agents.research.research_source_provider_factory import (
    create_research_source_providers,
)
from project0.agents.research.semantic_scholar_source_provider import (
    SemanticScholarSourceProvider,
)
from project0.agents.research.stub_research_source_provider import (
    StubResearchSourceProvider,
)
from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)


def test_factory_creates_supported_research_source_providers():
    """Verify the factory creates all configured providers."""

    providers = create_research_source_providers()

    assert "semantic_scholar" in providers
    assert "openalex" in providers
    assert "arxiv" in providers
    assert "stub" in providers


def test_factory_creates_semantic_scholar_provider():
    """Verify Semantic Scholar provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["semantic_scholar"],
        SemanticScholarSourceProvider,
    )


def test_factory_creates_openalex_provider():
    """Verify OpenAlex provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["openalex"],
        OpenAlexSourceProvider,
    )


def test_factory_creates_arxiv_provider():
    """Verify arXiv provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["arxiv"],
        ArxivSourceProvider,
    )


def test_factory_creates_stub_provider():
    """Verify stub provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["stub"],
        StubResearchSourceProvider,
    )


def test_factory_providers_implement_research_source_interface():
    """Verify factory results satisfy provider interface contract."""

    providers = create_research_source_providers()

    for provider in providers.values():
        assert isinstance(
            provider,
            ResearchSourceProviderProtocol,
        )


def test_stub_provider_contains_expected_reference():
    """Verify deterministic stub provider test data exists."""

    providers = create_research_source_providers()

    references = providers["stub"].search(
        strategy=None,  # type: ignore[arg-type]
    )

    assert len(references) == 1
    assert references[0].source_name == "stub"
