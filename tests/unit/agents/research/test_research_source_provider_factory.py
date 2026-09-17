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
from project0.agents.research.crossref_source_provider import (
    CrossrefSourceProvider,
)
from project0.agents.research.openalex_source_provider import (
    OpenAlexSourceProvider,
)
from project0.agents.research.openreview_source_provider import (
    OpenReviewSourceProvider,
)
from project0.agents.research.research_source_provider_factory import (
    create_research_source_providers,
)
from project0.agents.research.research_source_service import (
    ResearchSourceService,
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
from project0.config.settings import ProjectSettings
from project0.models.research_models import ResearchStrategy


def test_factory_creates_supported_research_source_providers():
    """Verify the factory creates all configured providers."""

    providers = create_research_source_providers()

    assert "semantic_scholar" in providers
    assert "openalex" in providers
    assert "openreview" in providers
    assert "crossref" in providers
    assert "arxiv" in providers
    assert "stub" in providers


def test_factory_creates_semantic_scholar_provider():
    """Verify Semantic Scholar provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["semantic_scholar"],
        SemanticScholarSourceProvider,
    )


def test_factory_configures_semantic_scholar_api_key(
    monkeypatch,
    tmp_path,
):
    """Verify Semantic Scholar provider receives configured API key."""

    settings = ProjectSettings(
        project_root=tmp_path,
        docs_dir=tmp_path / "docs",
        source_dir=tmp_path / "src",
        tests_dir=tmp_path / "tests",
        semantic_scholar_api_key="test-semantic-scholar-key",
    )

    monkeypatch.setattr(
        "project0.agents.research.research_source_provider_factory.SETTINGS",
        settings,
    )

    providers = create_research_source_providers(
        ("semantic_scholar",)
    )

    assert providers["semantic_scholar"].api_key == (
        "test-semantic-scholar-key"
    )


def test_factory_creates_openalex_provider():
    """Verify OpenAlex provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["openalex"],
        OpenAlexSourceProvider,
    )


def test_factory_creates_openreview_provider():
    """Verify OpenReview provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["openreview"],
        OpenReviewSourceProvider,
    )


def test_factory_creates_crossref_provider():
    """Verify Crossref provider creation."""

    providers = create_research_source_providers()

    assert isinstance(
        providers["crossref"],
        CrossrefSourceProvider,
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
    assert references[0].title == (
        "Self-Supervised Video Representation Alignment "
        "with Frozen CLIP for VideoQA"
    )
    assert references[0].metadata["abstract"] == (
        "A learned video encoder aligns its representations with a frozen "
        "CLIP vision-language teacher through feature matching in the "
        "shared embedding space."
    )


def test_stub_provider_survives_strict_alignment_selection() -> None:
    """Dashboard stub evidence satisfies the production alignment gate."""

    providers = create_research_source_providers(("stub",))
    strategy = ResearchStrategy(
        concepts=("video vision-language representation alignment",),
        search_terms=("video representations CLIP feature alignment",),
        source_names=("stub",),
    )

    result = ResearchSourceService(providers=providers).search(strategy)

    assert len(result) == 1
    assert result[0].source_id == "stub-paper-001"
