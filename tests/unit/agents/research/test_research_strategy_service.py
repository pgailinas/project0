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
        constraints=(
            "Focus on vision-language alignment.",
            "Prefer recent research.",
        ),
        focus_areas=(
            "video representation learning",
            "multimodal alignment",
        ),
        source_names=(
            "arxiv",
            "semantic_scholar",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "multimodal alignment",
        (
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
    )
    assert result.search_terms == (
        "video representation learning",
        "multimodal alignment",
        (
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
    )
    assert result.constraints == (
        "Focus on vision-language alignment.",
        "Prefer recent research.",
    )
    assert result.source_names == (
        "arxiv",
        "semantic_scholar",
    )
    assert result.rationale == (
        "Research strategy derived from the submitted "
        "research question, focus areas, and constraints."
    )


def test_build_strategy_with_question_only() -> None:
    """Verify strategy construction from a question only."""

    request = ResearchRequest(
        question="Find relevant VideoQA representation research.",
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "Find relevant VideoQA representation research.",
    )
    assert result.search_terms == (
        "Find relevant VideoQA representation research.",
    )
    assert result.constraints == ()
    assert result.source_names == (
        "semantic_scholar",
        "arxiv",
    )


def test_build_strategy_preserves_focus_area_order() -> None:
    """Verify research focus areas preserve request order."""

    request = ResearchRequest(
        question="Research question.",
        focus_areas=(
            "second concept",
            "first concept",
            "third concept",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "second concept",
        "first concept",
        "third concept",
        "Research question.",
    )


def test_build_strategy_removes_duplicate_focus_areas() -> None:
    """Verify duplicate focus areas are removed."""

    request = ResearchRequest(
        question="Research question.",
        focus_areas=(
            "video representation learning",
            "video representation learning",
            "multimodal alignment",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "multimodal alignment",
        "Research question.",
    )


def test_build_strategy_strips_focus_area_whitespace() -> None:
    """Verify focus area whitespace is normalized."""

    request = ResearchRequest(
        question="Research question.",
        focus_areas=(
            "  video representation learning  ",
            " multimodal alignment ",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "multimodal alignment",
        "Research question.",
    )


def test_build_strategy_ignores_empty_focus_areas() -> None:
    """Verify empty focus areas are ignored."""

    request = ResearchRequest(
        question="Research question.",
        focus_areas=(
            "",
            "   ",
            "video representation learning",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
        "Research question.",
    )


def test_build_strategy_strips_question_whitespace() -> None:
    """Verify research question whitespace is normalized."""

    request = ResearchRequest(
        question="  Research question.  ",
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "Research question.",
    )
    assert result.search_terms == (
        "Research question.",
    )


def test_build_strategy_avoids_duplicate_question_concept() -> None:
    """Verify question text is not duplicated in concepts."""

    request = ResearchRequest(
        question="video representation learning",
        focus_areas=(
            "video representation learning",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == (
        "video representation learning",
    )
    assert result.search_terms == (
        "video representation learning",
    )


def test_build_strategy_preserves_constraints() -> None:
    """Verify request constraints are preserved unchanged."""

    constraints = (
        "Prefer papers after 2020.",
        "Focus on VideoQA.",
    )

    request = ResearchRequest(
        question="Research question.",
        constraints=constraints,
    )

    service = ResearchStrategyService()

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
        source_names=source_names,
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.source_names == source_names


def test_build_strategy_returns_deterministic_results() -> None:
    """Verify repeated strategy construction is deterministic."""

    request = ResearchRequest(
        question="Research question.",
        constraints=(
            "Constraint one.",
        ),
        focus_areas=(
            "concept one",
            "concept two",
        ),
        source_names=(
            "arxiv",
        ),
    )

    service = ResearchStrategyService()

    first_result = service.build_strategy(request)
    second_result = service.build_strategy(request)

    assert first_result == second_result


def test_build_strategy_allows_empty_question() -> None:
    """Verify empty research questions produce an empty strategy."""

    request = ResearchRequest(
        question="",
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == ()
    assert result.search_terms == ()
    assert result.constraints == ()
    assert result.source_names == ()


def test_build_strategy_allows_whitespace_question() -> None:
    """Verify whitespace-only questions produce an empty strategy."""

    request = ResearchRequest(
        question="   ",
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.concepts == ()
    assert result.search_terms == ()


def test_build_strategy_search_terms_match_concepts() -> None:
    """Verify deterministic search terms follow concept ordering."""

    request = ResearchRequest(
        question="Research question.",
        focus_areas=(
            "concept one",
            "concept two",
        ),
    )

    service = ResearchStrategyService()

    result = service.build_strategy(request)

    assert result.search_terms == result.concepts


def test_strategy_defaults_to_multiple_research_sources():
    request = ResearchRequest(
        question="How can video representations be aligned with language models?"
    )

    strategy = ResearchStrategyService().build_strategy(
        request
    )

    assert strategy.source_names == (
        "semantic_scholar",
        "arxiv",
    )
    
