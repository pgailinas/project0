# ============================================================
# Project0 - Research Agent End-to-End Integration Tests
#
# File: test_research_agent_end_to_end_flow.py
#
# Purpose:
#    High-level integration tests aligned with:
#        Research_Agent_Test_Plan.md
#
# These tests exercise the Research Agent through the
# Platform Dispatcher boundary using deterministic research
# source and reasoning provider behavior.
#
# Verification scenario IDs follow the Test Plan directly:
#    RA-FUN-*  Functional Verification
#    RA-SAF-*  Safety Verification
#    RA-AI-*   AI Reasoning Verification
#    RA-ARCH-* Platform Boundary
#
# Integration test function names add the INT layer prefix.
#
# Implemented integration scenario IDs:
#    RA-FUN-001
#    RA-FUN-002
#    RA-FUN-003
#    RA-FUN-004
#    RA-FUN-005
#    RA-SAF-001
#    RA-AI-001
#
# Deferred IDs require additional integration fixtures:
#    RA-SAF-002
#    RA-AI-002
#    RA-AI-003
#    RA-ARCH-001
#
# These tests verify assembled workflow behavior through Python/service
# boundaries. Browser/UI acceptance testing is maintained separately
# under tests/acceptance/agents/research/.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from project0.config.settings import ProjectSettings
from project0.models.reasoning_models import ProviderResponse
from project0.models.research_models import (
    ResearchArtifactType,
    ResearchStatus,
)
from project0.platform.platform_dispatcher import create_platform_dispatcher
from project0.reasoning.providers.stub_provider import StubReasoningProvider


def _create_reasoning_provider() -> StubReasoningProvider:
    """Create deterministic research evaluation output."""

    return StubReasoningProvider(
        response=ProviderResponse(
            provider_name="stub",
            model_name="stub-model",
            content="",
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
    )


def _search_response() -> dict[str, Any]:
    """Create deterministic Semantic Scholar search output."""

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
    """Create deterministic Semantic Scholar metadata output."""

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

    return httpx.Response(
        200,
        json=data,
        request=httpx.Request("GET", url),
    )


@pytest.fixture
def research_repository(tmp_path: Path) -> Path:
    """Create a minimal repository fixture."""

    (tmp_path / "docs").mkdir(
        parents=True
    )

    (tmp_path / "mkdocs.yml").write_text(
        """
site_name: Integration Test Documentation
""",
        encoding="utf-8",
    )

    return tmp_path


def _create_dispatcher(
    repository_path: Path,
    monkeypatch,
) -> tuple[object, StubReasoningProvider]:
    """Create a dispatcher using deterministic research dependencies."""

    provider = _create_reasoning_provider()

    settings = ProjectSettings(
        project_root=repository_path,
        docs_dir=repository_path / "docs",
        source_dir=repository_path / "src",
        tests_dir=repository_path / "tests",
    )

    monkeypatch.setattr(
        "project0.platform.platform_dispatcher.validate_startup",
        lambda _: None,
    )

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

    dispatcher = create_platform_dispatcher(
        reasoning_provider=provider,
        reasoning_model_name="stub-model",
        settings=settings,
    )

    return dispatcher, provider


def test_INT_RA_FUN_001_research_request_processing(
    research_repository: Path,
    monkeypatch,
):
    """
    Research request completes the assembled workflow.
    """

    dispatcher, _ = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    result = dispatcher.run_research_workflow(
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

    assert result.status is ResearchStatus.COMPLETED
    assert result.error_message is None


def test_INT_RA_FUN_002_research_source_discovery(
    research_repository: Path,
    monkeypatch,
):
    """
    Research source discovery returns normalized references.
    """

    dispatcher, _ = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    result = dispatcher.run_research_workflow(
        question="Find relevant VideoQA research.",
        source_names=("semantic_scholar",),
    )

    assert len(result.source_references) == 1
    assert result.source_references[0].source_id == "paper-001"
    assert result.source_references[0].title == (
        "Example Video Representation Paper"
    )


def test_INT_RA_FUN_003_paper_metadata_retrieval(
    research_repository: Path,
    monkeypatch,
):
    """
    Paper metadata is retrieved through the assembled workflow.
    """

    dispatcher, _ = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    result = dispatcher.run_research_workflow(
        question="Find relevant VideoQA research.",
        source_names=("semantic_scholar",),
    )

    assert len(result.papers) == 1
    assert result.papers[0].abstract == (
        "A paper about semantic video representation learning."
    )
    assert result.papers[0].venue == "Example Conference"
    assert result.papers[0].doi == "10.1000/example"


def test_INT_RA_FUN_004_research_evaluation(
    research_repository: Path,
    monkeypatch,
):
    """
    Candidate papers receive structured research evaluations.
    """

    dispatcher, _ = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    result = dispatcher.run_research_workflow(
        question="Find relevant VideoQA research.",
        source_names=("semantic_scholar",),
    )

    assert len(result.evaluations) == 1
    assert result.evaluations[0].relevance_score == 0.95
    assert result.evaluations[0].research_connections == (
        (
            "Evaluate alignment between self-supervised "
            "video representations and language models."
        ),
    )


def test_INT_RA_FUN_005_research_artifact_generation(
    research_repository: Path,
    monkeypatch,
):
    """
    Research evaluations generate structured research artifacts.
    """

    dispatcher, _ = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    result = dispatcher.run_research_workflow(
        question="Find relevant VideoQA research.",
        source_names=("semantic_scholar",),
    )

    assert tuple(
        artifact.artifact_type
        for artifact in result.artifacts
    ) == (
        ResearchArtifactType.PAPER_SUMMARY,
        ResearchArtifactType.LITERATURE_COMPARISON,
        ResearchArtifactType.RESEARCH_GAP,
        ResearchArtifactType.EXPERIMENT_PROPOSAL,
    )


def test_INT_RA_SAF_001_invalid_request_handling(
    research_repository: Path,
    monkeypatch,
):
    """
    Invalid research requests are rejected at the dispatcher boundary.
    """

    dispatcher, _ = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    with pytest.raises(ValueError):
        dispatcher.run_research_workflow(
            question="",
        )


def test_INT_RA_AI_001_reasoning_provider_integration(
    research_repository: Path,
    monkeypatch,
):
    """
    Verify the reasoning provider participates in evaluation.
    """

    dispatcher, provider = _create_dispatcher(
        research_repository,
        monkeypatch,
    )

    dispatcher.run_research_workflow(
        question="Find relevant VideoQA research.",
        source_names=("semantic_scholar",),
    )

    assert provider.requests


@pytest.mark.skip(
    reason="Requires partial metadata integration fixture."
)
def test_INT_RA_SAF_002_partial_metadata_handling():
    pass


@pytest.mark.skip(
    reason="Requires unsupported-information reasoning fixture."
)
def test_INT_RA_AI_002_unsupported_information_prevention():
    pass


@pytest.mark.skip(
    reason="Requires invalid AI evaluation output fixture."
)
def test_INT_RA_AI_003_invalid_ai_output_handling():
    pass


@pytest.mark.skip(
    reason="Requires architecture dependency validation tooling."
)
def test_INT_RA_ARCH_001_agent_platform_separation():
    pass
