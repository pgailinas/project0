# ============================================================
# Project0 - Research Strategy Service Tests
#
# File: test_research_strategy_service.py
#
# Purpose:
#     Verify deterministic research strategy construction
#     for Project0 Research Agent requests.
#
# ============================================================

from __future__ import annotations

from project0.config.constants import DEFAULT_RESEARCH_SOURCE_PROVIDERS
from project0.models.research_models import ResearchRequest
from project0.agents.research.research_strategy_service import (
    ResearchStrategyService,
)


def test_build_strategy_from_complete_request() -> None:
    """Verify complete research strategy construction."""

    request = ResearchRequest(
        question=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        guidance=(
            "Focus on vision-language alignment. "
            "Prefer recent research. "
            "video representation learning. "
            "multimodal alignment."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.objective == (
        "How can self-supervised video representations "
        "be improved for VideoQA?"
    )
    assert result.concepts == (
        "video representation learning",
        "multimodal alignment",
        (
            "How can self-supervised video representations "
            "be improved for VideoQA"
        ),
    )
    assert result.search_terms == ()
    assert result.sub_questions == ()
    assert result.constraints == (
        "Focus on vision-language alignment.",
        "Prefer recent research.",
    )
    assert result.source_names == (
        "semantic_scholar",
        "arxiv",
    )
    assert result.rationale == (
        "Research strategy derived from the submitted "
        "research question and guidance."
    )


def test_build_strategy_with_question_only() -> None:
    """Verify strategy construction from a question only."""

    request = ResearchRequest(
        question="Find relevant VideoQA representation research.",
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.objective == (
        "Find relevant VideoQA representation research."
    )
    assert result.concepts == (
        "Find relevant VideoQA representation research",
    )
    assert result.search_terms == ()
    assert result.constraints == ()
    assert result.source_names == (
        "semantic_scholar",
        "arxiv",
    )


def test_build_strategy_preserves_guidance_concept_order() -> None:
    """Verify research guidance concepts preserve request order."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "second concept. "
            "first concept. "
            "third concept."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.concepts == (
        "second concept",
        "first concept",
        "third concept",
        "Research question",
    )


def test_build_strategy_removes_duplicate_guidance_concepts() -> None:
    """Verify duplicate guidance concepts are removed."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "video representation learning. "
            "video representation learning. "
            "multimodal alignment."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "multimodal alignment",
        "Research question",
    )


def test_build_strategy_strips_guidance_concept_whitespace() -> None:
    """Verify focus area whitespace is normalized."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "  video representation learning. "
            "multimodal alignment."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "multimodal alignment",
        "Research question",
    )


def test_build_strategy_ignores_empty_guidance_concepts() -> None:
    """Verify empty guidance concepts are ignored."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            ". "
            "   "
            "video representation learning."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "Research question",
    )


def test_build_strategy_strips_question_whitespace() -> None:
    """Verify research question whitespace is normalized."""

    request = ResearchRequest(
        question="  Research question.  ",
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.objective == "Research question."
    assert result.concepts == (
        "Research question",
    )
    assert result.search_terms == ()


def test_build_strategy_avoids_duplicate_question_concept() -> None:
    """Verify question text is not duplicated in concepts."""

    request = ResearchRequest(
        question="video representation learning",
        guidance=(
            "video representation learning."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
    )
    assert result.search_terms == ()


def test_build_strategy_preserves_constraints() -> None:
    """Verify request constraints are preserved unchanged."""

    constraints = (
        "Prefer papers after 2020.",
        "Focus on VideoQA.",
    )

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "Prefer papers after 2020. "
            "Focus on VideoQA."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.constraints == constraints


def test_build_strategy_preserves_source_names() -> None:
    """Verify configured research source names are preserved."""

    source_names = (
        "arxiv",
        "semantic_scholar",
    )

    request = ResearchRequest(
        question="Research question.",
        guidance="Use configured sources.",
    )

    service = ResearchStrategyService(
        source_names=source_names,
    )

    result = service.build_strategy(request)

    assert result.source_names == source_names


def test_build_strategy_returns_deterministic_results() -> None:
    """Verify repeated strategy construction is deterministic."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "Constraint one. "
            "concept one. "
            "concept two."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    first_result = service.build_strategy(request)
    second_result = service.build_strategy(request)

    assert first_result == second_result


def test_build_strategy_allows_empty_question() -> None:
    """Verify empty research questions produce an empty strategy."""

    request = ResearchRequest(
        question="",
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.objective is None
    assert result.concepts == ()
    assert result.search_terms == ()
    assert result.sub_questions == ()
    assert result.constraints == ()
    assert result.source_names == ()


def test_build_strategy_allows_whitespace_question() -> None:
    """Verify whitespace-only questions produce an empty strategy."""

    request = ResearchRequest(
        question="   ",
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.concepts == ()
    assert result.search_terms == ()


def test_build_strategy_leaves_search_terms_for_query_service() -> None:
    """Verify strategy construction defers executable query generation."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "concept one. "
            "concept two."
        ),
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    result = service.build_strategy(request)

    assert result.search_terms == ()


def test_strategy_defaults_to_multiple_research_sources():
    request = ResearchRequest(
        question="How can video representations be aligned with language models?"
    )

    strategy = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        request
    )

    assert strategy.source_names == (
        "semantic_scholar",
        "arxiv",
    )
    


def test_build_strategy_separates_directive_guidance_from_concepts() -> None:
    """Verify directive guidance is retained only as constraints."""

    request = ResearchRequest(
        question="Research question.",
        guidance=(
            "Focus on vision-language alignment. "
            "Prefer recent research. "
            "multimodal alignment."
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(request)

    assert result.concepts == (
        "multimodal alignment",
        "Research question",
    )
    assert result.constraints == (
        "Focus on vision-language alignment.",
        "Prefer recent research.",
    )


def test_build_strategy_extracts_benchmark_question_concept() -> None:
    """Verify benchmark research wording produces a concise concept."""

    question = (
        "Find recent research on aligning video representations "
        "with text or vision-language semantic spaces for VideoQA."
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(question=question)
    )

    assert result.objective == question
    assert result.concepts == (
        "aligning video representations with text or "
        "vision-language semantic spaces for VideoQA",
    )
