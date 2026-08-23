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

    assert result == (
        "video representation learning",
        "multimodal alignment",
    )


def test_research_query_service_removes_duplicate_queries():
    """Verify duplicate queries are removed."""

    result = ResearchQueryService().generate_queries(
        create_research_strategy()
    )

    assert result.count(
        "video representation learning"
    ) == 1


def test_research_query_service_preserves_query_order():
    """Verify query order is deterministic."""

    result = ResearchQueryService().generate_queries(
        create_research_strategy()
    )

    assert result == (
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

    assert result == (
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

    assert result == ()
