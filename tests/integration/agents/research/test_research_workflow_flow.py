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
    ResearchStatus,
)
from project0.workflow.research_workflow import ResearchWorkflow

from project0.agents.research.semantic_scholar_source_provider import (
    SemanticScholarSourceProvider,
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
        source_service=ResearchSourceService(
            providers={
                "semantic_scholar": SemanticScholarSourceProvider(
                    maximum_results=5,
                ),
                "arxiv": ArxivSourceProvider(),
            },
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
    assert len(result.artifacts) == 4

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
        ResearchArtifactType.PAPER_SUMMARY,
        ResearchArtifactType.LITERATURE_COMPARISON,
        ResearchArtifactType.RESEARCH_GAP,
        ResearchArtifactType.EXPERIMENT_PROPOSAL,
    )

    assert len(provider.requests) == 1
    assert provider.requests[0].model_name == "stub-model"


def test_research_workflow_preserves_source_traceability(
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

    source_reference = result.source_references[0]

    assert result.artifacts[0].source_references == (
        source_reference,
    )
    assert result.artifacts[1].source_references == ()
    assert result.artifacts[2].source_references == ()
    assert result.artifacts[3].source_references == ()


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
            question="What should I investigate next?",
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
        "Improve semantic alignment between video "
        "and language representations."
        in result.strategy.concepts
    )
    assert (
        "Video representations were not aligned "
        "with language representations."
        in result.strategy.concepts
    )
    assert len(context_provider.requests) == 1
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
