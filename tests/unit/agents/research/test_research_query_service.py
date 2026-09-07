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
    assert result.seed_terms == strategy.seed_terms
    assert result.search_terms == (
        "video representation alignment",
    )


def test_research_query_service_prioritizes_exact_seed_queries():
    """Verify exact seeds precede bounded discovery queries."""

    strategy = ResearchStrategy(
        concepts=(
            (
                "Treat Enhancing Vision-Language Model with Unmasked "
                "Token Alignment as a highly relevant seed example"
            ),
            "CLIP teacher student visual encoder feature alignment",
            "autoencoder latent projection frozen CLIP image embedding",
            "masked autoencoder CLIP feature distillation",
        ),
        search_terms=(),
        seed_terms=(
            "Enhancing Vision-Language Model with Unmasked Token Alignment",
            "arXiv:2405.19009",
        ),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "Enhancing Vision-Language Model with Unmasked Token Alignment",
        "arXiv:2405.19009",
        "CLIP teacher student visual encoder feature alignment",
        "masked autoencoder CLIP feature distillation",
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


def test_research_query_service_converts_guidance_directives_to_queries():
    """Verify guidance remains prioritized over later context concepts."""

    strategy = ResearchStrategy(
        concepts=(
            (
                "Find methods that align newly trained, self-supervised, "
                "masked-model, or autoencoder visual representations with "
                "frozen CLIP vision features or the shared CLIP "
                "vision-text embedding space"
            ),
            (
                "Include transferable image-domain methods even when they "
                "do not mention video or VideoQA"
            ),
            (
                "Assess their applicability to aligning autoencoder-generated "
                "video representations"
            ),
            (
                "Future work should explore contrastive objectives and "
                "latent-space regularization"
            ),
            (
                "The research problem is to investigate self-supervised "
                "video representations for VideoQA"
            ),
        ),
        search_terms=(),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "align self-supervised masked-model autoencoder frozen "
            "CLIP vision features"
        ),
        "transferable image-domain methods CLIP alignment",
        "aligning autoencoder-generated video representations CLIP",
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


def test_research_query_service_preserves_inferred_solution_queries():
    """Verify inferred solution concepts reach providers unchanged."""

    strategy = ResearchStrategy(
        concepts=(
            "What should I investigate next",
            "autoencoder video features frozen CLIP feature distillation",
            "video encoder tokens frozen CLIP token alignment",
            "autoencoder representations CLIP space contrastive projection",
            "A broad documented research limitation.",
        ),
        search_terms=(),
        objective="What should I investigate next?",
        inferred_solution_search_concepts=(
            "autoencoder video features frozen CLIP feature distillation",
            "video encoder tokens frozen CLIP token alignment",
            "autoencoder representations CLIP space contrastive projection",
        ),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "autoencoder video features frozen CLIP feature distillation",
        "video encoder tokens frozen CLIP token alignment",
        "autoencoder representations CLIP space contrastive projection",
    )


def test_research_query_service_compacts_long_inferred_solution_query():
    """Verify compaction retains source, target, and solution mechanism."""

    inferred_concept = (
        "autoencoder video representations into frozen CLIP shared "
        "space using feature distillation"
    )
    strategy = ResearchStrategy(
        concepts=(inferred_concept,),
        search_terms=(),
        inferred_solution_search_concepts=(inferred_concept,),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "autoencoder video representations CLIP space feature "
            "distillation"
        ),
    )


def test_research_query_service_preserves_verbose_target_and_mechanism():
    """Verify verbose structured output retains endpoints and mechanism."""

    inferred_concept = (
        "autoencoder-generated video representations shared embedding "
        "space of frozen CLIP vision and text model feature distillation"
    )
    strategy = ResearchStrategy(
        concepts=(inferred_concept,),
        search_terms=(),
        inferred_solution_search_concepts=(inferred_concept,),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        (
            "autoencoder-generated video representations CLIP model "
            "feature distillation"
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

def test_research_query_service_selects_distinct_research_roles():
    """Verify distinct guidance roles leave room for inferred context."""

    inferred_concept = "source representations target space alignment"
    strategy = ResearchStrategy(
        concepts=(
            inferred_concept,
            (
                "Find methods that preserve semantic structure using "
                "contrastive objectives"
            ),
            (
                "Find related or alternative methods for cross-modal "
                "representation mapping"
            ),
        ),
        search_terms=(),
        inferred_solution_search_concepts=(inferred_concept,),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "preserve semantic structure using contrastive objectives",
        "for cross-modal representation mapping",
        "source representations target space alignment",
    )


def test_research_query_service_does_not_fill_roles_with_inferred_variants():
    """Verify inferred variants do not consume every query role."""

    strategy = ResearchStrategy(
        concepts=(
            "source representation target space feature distillation",
            "source representation target space token alignment",
            "source representation target space contrastive projection",
            "A broad documented limitation.",
        ),
        search_terms=(),
        inferred_solution_search_concepts=(
            "source representation target space feature distillation",
            "source representation target space token alignment",
            "source representation target space contrastive projection",
        ),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "source representation target space feature distillation",
        "source representation target space token alignment",
        "source representation target space contrastive projection",
    )



def test_research_query_service_prioritizes_directives_over_inferred_queries():
    """Verify explicit guidance roles outrank inferred context queries."""

    inferred_concepts = (
        "source representation target space feature distillation",
        "source representation target space token alignment",
        "source representation target space contrastive projection",
    )
    strategy = ResearchStrategy(
        concepts=(
            *inferred_concepts,
            "Find methods that preserve semantic structure",
            "Include transferable cross-domain methods",
            "Assess their applicability to downstream retrieval",
        ),
        search_terms=(),
        inferred_solution_search_concepts=inferred_concepts,
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "preserve semantic structure",
        "transferable cross-domain methods",
        "downstream retrieval",
    )


def test_research_query_service_derives_queries_from_strategy_roles():
    """Verify rich strategies are decomposed into distinct research roles."""

    strategy = ResearchStrategy(
        concepts=(
            "learned representations align with pretrained embedding space",
            (
                "Future work should explore contrastive objectives, "
                "projection losses, and latent-space regularization"
            ),
            "latent representations map into frozen foundation embedding space",
            "downstream task performance remains limited",
        ),
        search_terms=(),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "learned representations align pretrained embedding space",
        "contrastive objectives projection losses latent-space regularization",
        "latent representations map frozen embedding space",
    )


def test_research_query_service_avoids_mixed_quality_query_when_roles_exist():
    """Verify mechanism roles displace broad mixed quality descriptions."""

    strategy = ResearchStrategy(
        concepts=(
            (
                "source representations align with pretrained target "
                "embedding space"
            ),
            (
                "source reconstruction quality semantic understanding "
                "jointly optimizing fidelity and consistency"
            ),
            (
                "Future work should explore contrastive objectives, "
                "latent-space regularization, and projection losses"
            ),
            (
                "latent representations map into frozen target "
                "embedding space"
            ),
        ),
        search_terms=(),
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "source representations align pretrained target embedding space",
        "contrastive objectives latent-space regularization projection losses",
        "latent representations map frozen target embedding space",
    )
    assert all(
        "fidelity" not in query.casefold()
        for query in result.search_terms
    )

def test_research_query_service_derives_roles_when_inferred_queries_exist():
    """Verify rich strategy roles outrank broad inferred query phrases."""

    inferred_concepts = (
        (
            "self-supervised encoder pretrained target model and its "
            "embedding space aligning latent representations with embeddings"
        ),
        (
            "source reconstruction quality semantic understanding jointly "
            "optimizing fidelity and consistency"
        ),
        (
            "hybrid representation model semantically aligned latent "
            "representations mapping into pretrained target embedding spaces"
        ),
    )
    strategy = ResearchStrategy(
        concepts=(
            "learned source representations align with pretrained target "
            "embedding space",
            *inferred_concepts,
            (
                "Future research should focus on improving semantic "
                "organization of learned representations rather than just "
                "reconstruction quality."
            ),
            (
                "The primary challenge is learning compact representations "
                "that preserve semantic structure, not just visual ones."
            ),
            (
                "Future work should explore contrastive objectives, "
                "latent-space regularization, transformer-based encoders, "
                "and more sophisticated fusion methods."
            ),
        ),
        search_terms=(),
        inferred_solution_search_concepts=inferred_concepts,
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == (
        "learned source representations align pretrained target embedding space",
        "contrastive objectives latent-space regularization transformer-based encoders",
        "representation model aligned latent representations mapping pretrained target",
    )
    assert all(
        "fidelity" not in query.casefold()
        for query in result.search_terms
    )


def test_research_query_service_rejects_degenerate_derived_role_query():
    """Verify weak derived roles do not displace stronger inferred queries."""

    inferred_concepts = (
        "source target features embedding space feature distillation",
        "source tokens frozen target token alignment",
        "source representations target space contrastive projection",
    )
    strategy = ResearchStrategy(
        concepts=(
            *inferred_concepts,
            "Improve semantic alignment between representations.",
            "Representations were not aligned with target representations.",
            "A documented limitation remains unresolved.",
            "A downstream evaluation found lower task performance.",
        ),
        search_terms=(),
        inferred_solution_search_concepts=inferred_concepts,
    )

    result = ResearchQueryService().generate_queries(strategy)

    assert result.search_terms == inferred_concepts
    assert "alignment representations" not in result.search_terms

