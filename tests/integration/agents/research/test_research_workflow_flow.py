# ============================================================
# Project0 - Research Workflow Flow Tests
#
# File: test_research_workflow_flow.py
#
# Purpose:
#     Verify the complete Project0 Research Agent workflow using
#     real Research Agent service implementations.
#
# ============================================================

from __future__ import annotations

import json
from typing import Any

import httpx

from project0.agents.research.existing_research_context_analysis_service import (
    ExistingResearchContextAnalysisService,
)
from project0.agents.research.paper_analysis_service import (
    PaperAnalysisService,
)
from project0.agents.research.paper_metadata_service import (
    PaperMetadataService,
)
from project0.agents.research.research_context_ingestion_service import (
    ResearchContextIngestionService,
)
from project0.agents.research.research_artifact_service import (
    ResearchArtifactService,
)
from project0.agents.research.research_query_service import (
    ResearchQueryService,
)
from project0.agents.research.research_evaluation_service import (
    ResearchEvaluationService,
)
from project0.agents.research.research_source_service import (
    ResearchSourceService,
)
from project0.agents.research.research_strategy_service import (
    ResearchStrategyService,
)
from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.models.research_models import (
    ResearchArtifactType,
    ResearchRequest,
    ResearchSourceReference,
    ResearchStatus,
)
from project0.workflow.research_workflow import ResearchWorkflow

from project0.agents.research.semantic_scholar_source_provider import (
    SemanticScholarSourceProvider,
)
from project0.agents.research.stub_research_source_provider import (
    StubResearchSourceProvider,
)
from project0.agents.research.arxiv_source_provider import (
    ArxivSourceProvider,
)


class StubReasoningProvider:
    """Return deterministic research evaluation output."""

    def __init__(
        self,
        response: ProviderResponse,
    ) -> None:
        self._response = response
        self.requests: list[ProviderRequest] = []

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Return the configured provider response."""

        self.requests.append(request)
        return self._response


def _provider_response() -> ProviderResponse:
    """Create a deterministic research evaluation response."""

    return ProviderResponse(
        provider_name="stub",
        model_name="stub-model",
        content="{}",
        structured_output={
            "evaluations": [
                {
                    "source_id": "paper-001",
                    "relevance_score": 95,
                    "relevance_summary": (
                        "The paper is highly relevant to "
                        "vision-language alignment for VideoQA."
                    ),
                    "strengths": [
                        "Uses semantic representation learning.",
                    ],
                    "limitations": [
                        "Limited direct VideoQA evaluation.",
                    ],
                    "research_connections": [
                        (
                            "Evaluate alignment between self-supervised "
                            "video representations and language models."
                        ),
                    ],
                    "warnings": [],
                }
            ],
        },
    )


def _paper_analysis_provider_response() -> ProviderResponse:
    """Create deterministic retained-paper metadata analysis output."""

    return ProviderResponse(
        provider_name="stub",
        model_name="stub-model",
        content="{}",
        structured_output={
            "source_id": "paper-001",
            "problem": {
                "content": (
                    "The paper studies semantic video representation "
                    "alignment."
                ),
                "section": None,
            },
            "approach": {
                "content": (
                    "The paper uses semantic representation learning."
                ),
                "section": None,
            },
            "representations": [
                {
                    "content": (
                        "Video representations are analyzed for "
                        "semantic alignment."
                    ),
                        "section": None,
                }
            ],
            "modalities": [
                {
                    "content": "The paper studies video representations.",
                        "section": None,
                }
            ],
            "learning_objectives": [],
            "datasets_tasks": [],
            "findings": [
                {
                    "content": (
                        "Semantic representation learning is relevant "
                        "to the research question."
                    ),
                        "section": None,
                }
            ],
            "limitations": [],
            "research_relevance": {
                "content": (
                    "The paper informs semantic video-language "
                    "alignment research."
                ),
                "section": None,
            },
            "warnings": [],
        },
    )


def _context_provider_response() -> ProviderResponse:
    """Create deterministic existing research context analysis output."""

    return ProviderResponse(
        provider_name="stub",
        model_name="stub-model",
        content="{}",
        structured_output={
            "research_problem": {
                "content": (
                    "Improve semantic alignment between video "
                    "and language representations."
                ),
                "section": None,
            },
            "prior_work": [],
            "implemented_approaches": [],
            "findings": [],
            "limitations": [
                {
                    "content": (
                        "Video representations were not aligned "
                        "with language representations."
                    ),
                    "section": None,
                }
            ],
            "unresolved_questions": [],
            "stated_future_work": [],
            "inferred_solution_search_concepts": [
                {
                    "source_representation": "video features",
                    "target_model_or_space": "embedding space",
                    "solution_mechanism": "feature distillation",
                },
                {
                    "source_representation": "autoencoder video tokens",
                    "target_model_or_space": "frozen CLIP",
                    "solution_mechanism": "token alignment",
                },
                {
                    "source_representation": "autoencoder representations",
                    "target_model_or_space": "CLIP space",
                    "solution_mechanism": "contrastive projection",
                },
            ],
        },
    )


def _search_response() -> dict[str, Any]:
    """Create a deterministic Semantic Scholar search response."""

    return {
        "total": 1,
        "offset": 0,
        "next": 1,
        "data": [
            {
                "paperId": "paper-001",
                "title": "Example Video Representation Paper",
                "authors": [
                    {
                        "authorId": "author-001",
                        "name": "Author One",
                    },
                    {
                        "authorId": "author-002",
                        "name": "Author Two",
                    },
                ],
                "year": 2024,
                "url": (
                    "https://www.semanticscholar.org/"
                    "paper/paper-001"
                ),
            }
        ],
    }


def _metadata_response() -> dict[str, Any]:
    """Create deterministic Semantic Scholar paper metadata."""

    return {
        "paperId": "paper-001",
        "title": "Example Video Representation Paper",
        "authors": [
            {
                "authorId": "author-001",
                "name": "Author One",
            },
            {
                "authorId": "author-002",
                "name": "Author Two",
            },
        ],
        "year": 2024,
        "abstract": (
            "A paper about semantic video representation learning."
        ),
        "venue": "Example Conference",
        "externalIds": {
            "DOI": "10.1000/example",
        },
        "url": (
            "https://www.semanticscholar.org/"
            "paper/paper-001"
        ),
    }


def _arxiv_response() -> str:
    """Create deterministic arXiv XML search output."""

    return """
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>arXiv Query Results</title>
    </feed>
    """


def _xml_http_response(
    url: str,
    xml_text: str,
) -> httpx.Response:
    """Create an HTTP XML response with request metadata attached."""

    request = httpx.Request(
        "GET",
        url,
    )

    return httpx.Response(
        200,
        text=xml_text,
        request=request,
    )


def _http_response(
    url: str,
    data: dict[str, Any],
) -> httpx.Response:
    """Create an HTTP response with request metadata attached."""

    request = httpx.Request(
        "GET",
        url,
    )

    return httpx.Response(
        200,
        json=data,
        request=request,
    )


def _create_workflow(
    provider: StubReasoningProvider,
    context_provider: StubReasoningProvider | None = None,
    paper_analysis_provider: StubReasoningProvider | None = None,
    source_service: ResearchSourceService | None = None,
) -> ResearchWorkflow:
    """Create the real Research Agent integration pipeline."""

    return ResearchWorkflow(
        strategy_service=ResearchStrategyService(
            source_names=(
                "semantic_scholar",
                "arxiv",
            ),
        ),
        query_service=ResearchQueryService(),
        source_service=(
            source_service
            if source_service is not None
            else ResearchSourceService(
                providers={
                    "semantic_scholar": SemanticScholarSourceProvider(
                        maximum_results=5,
                    ),
                    "arxiv": ArxivSourceProvider(),
                },
            )
        ),
        metadata_service=PaperMetadataService(),
        evaluation_service=ResearchEvaluationService(
            provider=provider,
            model_name="stub-model",
        ),
        artifact_service=ResearchArtifactService(),
        context_ingestion_service=(
            ResearchContextIngestionService()
            if context_provider is not None
            else None
        ),
        context_analysis_service=(
            ExistingResearchContextAnalysisService(
                provider=context_provider,
                model_name="stub-model",
            )
            if context_provider is not None
            else None
        ),
        paper_analysis_service=(
            PaperAnalysisService(
                provider=paper_analysis_provider,
                model_name="stub-model",
            )
            if paper_analysis_provider is not None
            else None
        ),
    )


def test_research_workflow_completes_real_service_pipeline(
    monkeypatch,
) -> None:
    """A research request completes the real service pipeline."""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        del params
        del headers
        del timeout

        if url.endswith("/paper/search"):
            return _http_response(
                url,
                _search_response(),
            )

        if url.endswith("/paper/paper-001"):
            return _http_response(
                url,
                _metadata_response(),
            )

        if url.endswith("/api/query"):
            return _xml_http_response(
                url,
                _arxiv_response(),
            )

        raise AssertionError(
            f"Unexpected request: {url}"
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = StubReasoningProvider(
        _provider_response()
    )
    workflow = _create_workflow(provider)

    result = workflow.execute(
        ResearchRequest(
            question=(
                "How can self-supervised video representations "
                "be improved for VideoQA?"
            ),
            guidance=(
                "Focus on vision-language alignment. "
                "video representation learning"
            ),
        )
    )

    assert result.status is ResearchStatus.COMPLETED
    assert result.error_message is None
    assert result.strategy is not None
    assert len(result.strategy.search_terms) >= 1
    assert len(result.source_references) == 1
    assert len(result.papers) == 1
    assert len(result.evaluations) == 1
    assert len(result.artifacts) == 3

    reference = result.source_references[0]
    paper = result.papers[0]
    evaluation = result.evaluations[0]

    assert reference.source_id == "paper-001"
    assert reference.title == "Example Video Representation Paper"
    assert paper.source_reference == reference
    assert paper.abstract == (
        "A paper about semantic video representation learning."
    )
    assert paper.venue == "Example Conference"
    assert paper.doi == "10.1000/example"
    assert evaluation.paper == paper
    assert evaluation.relevance_score == 0.95

    assert tuple(
        artifact.artifact_type
        for artifact in result.artifacts
    ) == (
        ResearchArtifactType.LITERATURE_COMPARISON,
        ResearchArtifactType.RESEARCH_GAP,
        ResearchArtifactType.EXPERIMENT_PROPOSAL,
    )

    assert len(provider.requests) == 1
    assert provider.requests[0].model_name == "stub-model"


def test_research_workflow_uses_richest_publication_version() -> None:
    """Duplicate publication locations produce one metadata-rich paper."""

    title = "Example Video Representation Paper"
    authors = ("Author One", "Author Two")
    sparse = ResearchSourceReference(
        source_name="openalex",
        source_id="paper-sparse",
        title=title,
        source_url="https://aclanthology.org/example",
        authors=authors,
        publication_year=2024,
        metadata={
            "abstract": "Author One and Author Two. Example Conference.",
        },
    )
    rich = ResearchSourceReference(
        source_name="openalex",
        source_id="paper-001",
        title=title,
        source_url="https://arxiv.org/abs/2401.12345",
        authors=authors,
        publication_year=2024,
        metadata={
            "abstract": (
                "A paper about semantic video representation learning "
                "with a complete description of its method and findings."
            ),
            "venue": "Example Conference",
        },
    )
    source_service = ResearchSourceService(
        providers={
            "semantic_scholar": StubResearchSourceProvider(
                references=(sparse,),
            ),
            "arxiv": StubResearchSourceProvider(
                references=(rich,),
            ),
        },
    )
    workflow = _create_workflow(
        StubReasoningProvider(_provider_response()),
        source_service=source_service,
    )

    result = workflow.execute(
        ResearchRequest(
            question=(
                "How can self-supervised video representations "
                "be improved for VideoQA?"
            ),
            guidance="Focus on vision-language alignment.",
        )
    )

    assert result.status is ResearchStatus.COMPLETED
    assert result.source_references == (rich,)
    assert len(result.papers) == 1
    assert result.papers[0].abstract == rich.metadata["abstract"]
    assert len(result.evaluations) == 1


def test_research_workflow_omits_redundant_artifact_traceability(
    monkeypatch,
) -> None:
    """Generated research artifacts preserve source references."""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        del params
        del headers
        del timeout

        if url.endswith("/paper/search"):
            return _http_response(
                url,
                _search_response(),
            )

        if url.endswith("/paper/paper-001"):
            return _http_response(
                url,
                _metadata_response(),
            )

        if url.endswith("/api/query"):
            return _xml_http_response(
                url,
                _arxiv_response(),
            )

        raise AssertionError(
            f"Unexpected request: {url}"
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = StubReasoningProvider(
        _provider_response()
    )
    workflow = _create_workflow(provider)

    result = workflow.execute(
        ResearchRequest(
            question="Find relevant VideoQA research.",
            guidance="semantic_scholar",
        )
    )

    assert result.status is ResearchStatus.COMPLETED
    assert len(result.source_references) == 1

    assert result.artifacts[0].source_references == ()
    assert result.artifacts[1].source_references == ()
    assert result.artifacts[2].source_references == ()


def test_research_workflow_returns_warning_when_search_is_empty(
    monkeypatch,
) -> None:
    """Empty research search results produce a warning result."""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        del params
        del headers
        del timeout

        if url.endswith("/paper/search"):
            return _http_response(
                url,
                {
                    "total": 0,
                    "offset": 0,
                    "data": [],
                },
            )

        if url.endswith("/api/query"):
            return _xml_http_response(
                url,
                _arxiv_response(),
            )

        raise AssertionError(
            f"Unexpected request: {url}"
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = StubReasoningProvider(
        _provider_response()
    )
    workflow = _create_workflow(provider)

    result = workflow.execute(
        ResearchRequest(
            question="Find relevant VideoQA research.",
            guidance="semantic_scholar",
        )
    )

    assert (
        result.status
        is ResearchStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.source_references == ()
    assert result.papers == ()
    assert result.evaluations == ()
    assert result.artifacts == ()
    assert result.warnings == (
        "No candidate research sources were found.",
    )
    assert provider.requests == []


def test_research_workflow_uses_existing_research_context(
    monkeypatch,
) -> None:
    """Existing research context informs the real strategy pipeline."""

    requested_search_terms: list[str] = []

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        del headers
        del timeout

        if url.endswith("/paper/search"):
            requested_search_terms.append(params["query"])
            return _http_response(
                url,
                _search_response(),
            )

        if url.endswith("/paper/paper-001"):
            return _http_response(
                url,
                _metadata_response(),
            )

        if url.endswith("/api/query"):
            return _xml_http_response(
                url,
                _arxiv_response(),
            )

        raise AssertionError(
            f"Unexpected request: {url}"
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    evaluation_provider = StubReasoningProvider(
        _provider_response()
    )
    context_provider = StubReasoningProvider(
        _context_provider_response()
    )
    workflow = _create_workflow(
        evaluation_provider,
        context_provider,
    )

    result = workflow.execute(
        ResearchRequest(
            question=(
                "How can autoencoder video representations align with "
                "frozen CLIP embeddings?"
            ),
        ),
        context_source_name="prior_research.txt",
        context_content=(
            b"Prior research found limited semantic alignment "
            b"between video and language representations."
        ),
    )

    assert result.status is ResearchStatus.COMPLETED
    assert result.error_message is None
    assert result.strategy is not None
    assert (
        "How can autoencoder video representations align with frozen "
        "CLIP embeddings"
        not in result.strategy.search_terms
    )
    assert (
        "Improve semantic alignment between video "
        "and language representations."
        in result.strategy.concepts
    )
    assert (
        "Video representations were not aligned "
        "with language representations."
        in result.strategy.concepts
    )
    assert result.strategy.search_terms == (
        "autoencoder CLIP video features embedding space feature distillation",
        "autoencoder video tokens frozen CLIP token alignment",
        "autoencoder representations CLIP space contrastive projection",
    )
    assert len(context_provider.requests) == 1
    assert len(result.strategy.inferred_solution_search_concepts) == 3
    assert requested_search_terms[:3] == [
        "autoencoder CLIP video features embedding space feature distillation",
        "autoencoder video tokens frozen CLIP token alignment",
        "autoencoder representations CLIP space contrastive projection",
    ]
    assert json.loads(
        context_provider.requests[0].user_prompt
    )["research_question"] == (
        "How can autoencoder video representations align with frozen "
        "CLIP embeddings?"
    )
    assert len(evaluation_provider.requests) == 1


def test_research_workflow_runs_metadata_paper_analysis_pipeline(
    monkeypatch,
) -> None:
    """Retained papers are analyzed from metadata and abstract."""

    requested_urls: list[str] = []

    def fake_get(
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        del kwargs
        requested_urls.append(url)

        if url.endswith("/paper/search"):
            return _http_response(
                url,
                _search_response(),
            )

        if url.endswith("/paper/paper-001"):
            return _http_response(
                url,
                _metadata_response(),
            )

        if url.endswith("/api/query"):
            return _xml_http_response(
                url,
                _arxiv_response(),
            )

        raise AssertionError(
            f"Unexpected request: {url}"
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    evaluation_provider = StubReasoningProvider(
        _provider_response()
    )
    paper_analysis_provider = StubReasoningProvider(
        _paper_analysis_provider_response()
    )
    workflow = _create_workflow(
        evaluation_provider,
        paper_analysis_provider=paper_analysis_provider,
    )

    result = workflow.execute(
        ResearchRequest(
            question=(
                "How can self-supervised video representations "
                "be improved for VideoQA?"
            ),
            guidance="Focus on vision-language alignment.",
        )
    )

    assert result.status is ResearchStatus.COMPLETED
    assert result.error_message is None
    assert len(result.papers) == 1
    assert len(evaluation_provider.requests) == 1
    assert len(paper_analysis_provider.requests) == 1
    assert "https://doi.org/10.1000/example" not in requested_urls

    analysis_request = paper_analysis_provider.requests[0]

    assert analysis_request.metadata[
        "paper_source_id"
    ] == "paper-001"
    assert analysis_request.metadata[
        "analysis_basis"
    ] == "abstract_metadata"

    analysis_payload = __import__("json").loads(
        analysis_request.user_prompt
    )

    assert analysis_payload["paper"]["source_id"] == "paper-001"
    assert analysis_payload["paper"]["analysis_basis"] == "abstract_metadata"
    assert analysis_payload["paper"]["abstract"] == (
        "A paper about semantic video representation learning."
    )
    assert "pages" not in analysis_payload["paper"]


def test_research_workflow_evaluates_explicit_publication_seed() -> None:
    """An explicit guidance seed reaches retrieval and evaluation."""

    seed_provider = StubResearchSourceProvider(
        references=(
            ResearchSourceReference(
                source_name="stub",
                source_id="paper-001",
                title=(
                    "Enhancing Vision-Language Model with "
                    "Unmasked Token Alignment"
                ),
                source_url="https://arxiv.org/abs/2405.19009",
                authors=("Author One",),
                publication_year=2024,
                metadata={
                    "abstract": (
                        "A CLIP teacher aligns a visual encoder."
                    ),
                    "arxiv_id": "2405.19009",
                },
            ),
        ),
    )
    arxiv_provider = StubResearchSourceProvider(references=())
    evaluation_provider = StubReasoningProvider(
        _provider_response()
    )
    source_service = ResearchSourceService(
        providers={
            "semantic_scholar": seed_provider,
            "arxiv": arxiv_provider,
        },
    )
    workflow = _create_workflow(
        evaluation_provider,
        source_service=source_service,
    )

    result = workflow.execute(
        ResearchRequest(
            question=(
                "How can autoencoder video representations "
                "align with CLIP?"
            ),
            guidance=(
                "Treat \u201cEnhancing Vision-Language Model with "
                "Unmasked Token Alignment\u201d (UTA, "
                "arXiv:2405.19009v2) as a seed."
            ),
        )
    )

    assert result.status is ResearchStatus.COMPLETED
    assert result.strategy is not None
    assert result.strategy.seed_terms == (
        "Enhancing Vision-Language Model with Unmasked Token Alignment",
        "arXiv:2405.19009",
    )
    assert [
        request.search_terms
        for request in seed_provider.requests[:2]
    ] == [
        (
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
        ),
        ("arXiv:2405.19009",),
    ]
    assert len(result.evaluations) == 1
    assert len(evaluation_provider.requests) == 1
    assert result.metadata["source_search"] == {
        "retrieved_count": len(seed_provider.requests),
        "deduplicated_count": 1,
        "seed_preserved_count": 1,
        "evaluation_candidate_count": 1,
    }
    assert source_service.last_candidate_trace == (
        {
            "deduplicated_rank": 1,
            "evaluation_rank": 1,
            "selection_status": "preserved_seed",
            "title": (
                "Enhancing Vision-Language Model with Unmasked Token Alignment"
            ),
            "canonical_source_name": "stub",
            "source_id": "paper-001",
            "retrieval_providers": ("semantic_scholar",),
            "retrieval_queries": (
                (
                    "Enhancing Vision-Language Model with "
                    "Unmasked Token Alignment"
                ),
                "arXiv:2405.19009",
            ),
            "stable_identifiers": ("arxiv:2405.19009",),
        },
    )


def test_research_workflow_uses_technical_seed_free_guidance_queries() -> None:
    """Seed-free guidance reaches retrieval as technical query phrases."""

    source_provider = StubResearchSourceProvider(references=())
    evaluation_provider = StubReasoningProvider(
        _provider_response()
    )
    context_provider = StubReasoningProvider(
        _context_provider_response()
    )
    workflow = _create_workflow(
        evaluation_provider,
        context_provider=context_provider,
        source_service=ResearchSourceService(
            providers={
                "semantic_scholar": source_provider,
                "arxiv": StubResearchSourceProvider(references=()),
            },
        ),
    )

    result = workflow.execute(
        ResearchRequest(
            question=(
                "How should autoencoder-generated video representations "
                "align with CLIP?"
            ),
            guidance=(
                "Find methods that align newly trained, self-supervised, "
                "masked-model, or autoencoder visual representations with "
                "frozen CLIP vision features or the shared CLIP vision-text "
                "embedding space. Include transferable image-domain methods "
                "even when they do not mention video or VideoQA. Assess "
                "their applicability to aligning autoencoder-generated "
                "video representations."
            ),
        ),
        context_source_name="prior_research.txt",
        context_content=(
            b"Prior research found limited semantic alignment between "
            b"video and language representations."
        ),
    )

    assert result.status is ResearchStatus.COMPLETED_WITH_WARNINGS
    assert result.warnings == (
        "No candidate research sources were found.",
    )
    assert result.strategy is not None
    assert result.strategy.seed_terms == ()
    assert len(context_provider.requests) == 1
    assert [
        request.search_terms
        for request in source_provider.requests
    ] == [
        (
            "align self-supervised masked-model autoencoder frozen "
            "CLIP vision features",
        ),
        ("transferable image-domain methods CLIP alignment",),
        ("aligning autoencoder-generated video representations CLIP",),
    ]
    assert evaluation_provider.requests == []
