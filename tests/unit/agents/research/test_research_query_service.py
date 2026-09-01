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


def test_research_query_service_excludes_objective_from_long_concept_query():
    """Verify a long concept query does not restore the objective."""

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


def test_research_query_service_preserves_follow_on_and_domain_queries():
    """Verify distinct follow-on and domain queries are preserved."""

    strategy = ResearchStrategy(
        concepts=(
            "What should I investigate next",
            (
                "Investigate semantic alignment objectives for "
                "video representations and language models"
            ),
            (
                "How should video representations be aligned "
                "with language representations?"
            ),
            (
                "VideoQA requires semantically aligned video and "
                "language representations for question answering"
            ),
        ),
        search_terms=(),
        objective="What should I investigate next?",
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "semantic alignment objectives for video "
            "representations and language"
        ),
        (
            "VideoQA requires semantically aligned video and language"
        ),
    )

def test_research_query_service_strips_future_research_framing():
    """Verify future-research framing does not consume query budget."""

    strategy = ResearchStrategy(
        concepts=(
            "What should I investigate next",
            (
                "Contrastive objectives latent-space regularization "
                "for representation learning approaches in video"
            ),
            (
                "Future research should focus on video language "
                "semantic alignment"
            ),
        ),
        search_terms=(),
        objective="What should I investigate next?",
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "Contrastive objectives latent-space regularization for "
            "representation learning approaches"
        ),
        (
            "video language semantic alignment"
        ),
    )

def test_research_query_service_generates_complementary_context_queries():
    """Verify context concepts produce complementary bounded queries."""

    strategy = ResearchStrategy(
        concepts=(
            "What should I investigate next",
            (
                "Future work should explore contrastive objectives, "
                "latent-space regularization, transformer-based video "
                "encoders, and more sophisticated hybrid fusion methods."
            ),
            (
                "Future research should focus on improving semantic "
                "organization of self-supervised video representations "
                "rather than just reconstruction quality."
            ),
            (
                "The primary challenge is learning compact "
                "representations that preserve semantic structure, "
                "not just visual ones."
            ),
            (
                "The self-supervised autoencoder was optimized for "
                "visual reconstruction rather than semantic "
                "understanding, leading to lower accuracy in VideoQA tasks."
            ),
            (
                "Increasing the training subset did not improve "
                "performance, suggesting that additional data alone "
                "is insufficient to enhance video representation quality."
            ),
            (
                "The research problem is to investigate the effectiveness "
                "of self-supervised video representations for Video "
                "Question Answering (VideoQA) tasks, specifically comparing "
                "them with pretrained CLIP and hybrid CLIP-autoencoder "
                "approaches."
            ),
        ),
        search_terms=(),
        objective="What should I investigate next?",
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "contrastive objectives latent-space regularization "
            "transformer-based video encoders"
        ),
        (
            "improving semantic organization of self-supervised "
            "video representations"
        ),
        (
            "effectiveness of self-supervised video representations "
            "for VideoQA CLIP"
        ),
    )


def test_research_query_service_limits_query_dimensions():
    """Verify provider query count is bounded to three dimensions."""

    strategy = ResearchStrategy(
        concepts=(
            "first representation objective",
            "second alignment objective",
            "third evaluation objective",
            "fourth application objective",
        ),
        search_terms=(),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "first representation objective",
        "second alignment objective",
        "fourth application objective",
    )


def test_research_query_service_removes_overlapping_dimensions():
    """Verify substantially overlapping query dimensions are removed."""

    strategy = ResearchStrategy(
        concepts=(
            "semantic video language alignment",
            "video semantic language alignments",
            "temporal representation evaluation",
        ),
        search_terms=(),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "semantic video language alignment",
        "temporal representation evaluation",
    )
