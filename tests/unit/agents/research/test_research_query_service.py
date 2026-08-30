# ============================================================
# Project0 - Research Query Service Tests
#
# File: test_research_query_service.py
#
# Purpose:
#     Verify deterministic Research Query Service behavior.
#
# ============================================================

from __future__ import annotations

from project0.agents.research.research_query_service import (
    ResearchQueryService,
)
from project0.models.research_models import ResearchStrategy


def create_research_strategy() -> ResearchStrategy:
    """Create a representative research strategy."""

    return ResearchStrategy(
        concepts=(
            "video representation learning",
            "multimodal alignment",
            "video representation learning",
        ),
        search_terms=(
            "video representation learning",
            "multimodal alignment",
        ),
        constraints=(
            "Prefer recent research.",
        ),
        source_names=(
            "semantic_scholar",
        ),
        rationale="Investigate VideoQA research directions.",
    )


def test_research_query_service_generates_queries_from_strategy():
    """Verify queries are generated from research concepts."""

    result = ResearchQueryService().generate_queries(
        create_research_strategy()
    )

    assert result.search_terms == (
        "video representation learning",
        "multimodal alignment",
    )


def test_research_query_service_removes_duplicate_queries():
    """Verify duplicate queries are removed."""

    result = ResearchQueryService().generate_queries(
        create_research_strategy()
    )

    assert result.search_terms.count(
        "video representation learning"
    ) == 1


def test_research_query_service_preserves_query_order():
    """Verify query order is deterministic."""

    result = ResearchQueryService().generate_queries(
        create_research_strategy()
    )

    assert result.search_terms == (
        "video representation learning",
        "multimodal alignment",
    )


def test_research_query_service_normalizes_query_whitespace():
    """Verify query whitespace is normalized."""

    strategy = ResearchStrategy(
        concepts=(
            "  video   representation   learning  ",
        ),
        search_terms=(
            "video representation learning",
        ),
    )

    result = ResearchQueryService().generate_queries(
        strategy
    )

    assert result.search_terms == (
        "video representation learning",
    )


def test_research_query_service_handles_empty_strategy():
    """Verify empty strategies produce no queries."""

    result = ResearchQueryService().generate_queries(
        ResearchStrategy(
            concepts=(),
            search_terms=(),
        )
    )

    assert result.search_terms == ()


def test_research_query_service_preserves_strategy_planning_fields():
    """Verify query generation enriches rather than replaces strategy data."""

    strategy = ResearchStrategy(
        concepts=("video representation alignment",),
        search_terms=(),
        objective="Find relevant alignment research.",
        sub_questions=("Which methods align video and text?",),
        constraints=("Prefer recent research.",),
        source_names=("arxiv",),
        rationale="Structured research plan.",
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.objective == strategy.objective
    assert result.sub_questions == strategy.sub_questions
    assert result.constraints == strategy.constraints
    assert result.source_names == strategy.source_names
    assert result.rationale == strategy.rationale
    assert result.search_terms == (
        "video representation alignment",
    )


def test_research_query_service_excludes_objective_question_concept():
    """Verify objective question text is not used as a provider query."""

    strategy = ResearchStrategy(
        concepts=(
            "What should I investigate next",
            "semantic alignment objectives",
        ),
        search_terms=(),
        objective="What should I investigate next?",
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "semantic alignment objectives",
    )


def test_research_query_service_excludes_objective_from_fallback():
    """Verify fallback does not restore the objective question."""

    strategy = ResearchStrategy(
        concepts=(
            "What should I investigate next",
            (
                "Video representations require stronger semantic "
                "alignment with language representations"
            ),
        ),
        search_terms=(),
        objective="What should I investigate next?",
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "Video representations require stronger semantic "
            "alignment with language"
        ),
    )


def test_research_query_service_uses_focus_constraint_when_needed():
    """Verify a Focus on constraint can supply a technical query."""

    strategy = ResearchStrategy(
        concepts=(
            (
                "How can self-supervised video representations "
                "be improved for VideoQA"
            ),
        ),
        search_terms=(),
        objective=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        constraints=(
            "Focus on vision-language alignment.",
        ),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "vision-language alignment",
    )
