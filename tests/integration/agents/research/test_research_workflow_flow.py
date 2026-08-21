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

from project0.agents.research.paper_metadata_service import (
    PaperMetadataService,
)
from project0.agents.research.research_artifact_service import (
    ResearchArtifactService,
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
                    "relevance_score": 0.95,
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
) -> ResearchWorkflow:
    """Create the real Research Agent integration pipeline."""

    return ResearchWorkflow(
        strategy_service=ResearchStrategyService(),
        source_service=ResearchSourceService(
            maximum_results=5,
        ),
        metadata_service=PaperMetadataService(),
        evaluation_service=ResearchEvaluationService(
            provider=provider,
            model_name="stub-model",
        ),
        artifact_service=ResearchArtifactService(),
    )


def test_research_workflow_completes_real_service_pipeline(
    monkeypatch,
) -> None:
    """A research request completes the real service pipeline."""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        del params
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

        raise AssertionError(
            f"Unexpected Semantic Scholar request: {url}"
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
            constraints=(
                "Focus on vision-language alignment.",
            ),
            focus_areas=(
                "video representation learning",
            ),
            source_names=(
                "semantic_scholar",
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
        timeout: float,
    ) -> httpx.Response:
        del params
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

        raise AssertionError(
            f"Unexpected Semantic Scholar request: {url}"
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
            source_names=(
                "semantic_scholar",
            ),
        )
    )

    assert result.status is ResearchStatus.COMPLETED
    assert len(result.source_references) == 1

    source_reference = result.source_references[0]

    for artifact in result.artifacts:
        assert artifact.source_references == (
            source_reference,
        )


def test_research_workflow_returns_warning_when_search_is_empty(
    monkeypatch,
) -> None:
    """Empty research search results produce a warning result."""

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        del params
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

        raise AssertionError(
            f"Unexpected Semantic Scholar request: {url}"
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
            source_names=(
                "semantic_scholar",
            ),
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
