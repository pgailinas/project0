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
from project0.models.research_models import (
    ExistingResearchContext,
    ResearchFinding,
    ResearchGuidanceRelevance,
    ResearchGuidanceSeed,
    ResearchRequest,
)
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


def test_build_strategy_preserves_explicit_publication_seeds() -> None:
    """Verify titles and identifiers become intact ordered seeds."""

    request = ResearchRequest(
        question="How can visual representations align with CLIP?",
        guidance=(
            "Treat \u201cEnhancing Vision-Language Model with Unmasked "
            "Token Alignment\u201d (UTA, arXiv:2405.19009v2) as a seed. "
            "Compare DOI:10.1000/example.1 as related work."
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(request)

    assert result.seed_terms == (
        "Enhancing Vision-Language Model with Unmasked Token Alignment",
        "arXiv:2405.19009",
        "doi:10.1000/example.1",
    )
    assert any(
        "arXiv:2405.19009v2" in concept
        for concept in result.concepts
    )


def test_build_strategy_structures_high_relevance_seed_designation() -> None:
    """High relevance is retained separately from publication identity."""

    request = ResearchRequest(
        question="How can video representations align with CLIP?",
        guidance=(
            "Treat arXiv:2303.16058 and arXiv:2405.19009v2 as highly "
            "relevant seed papers. Compare DOI:10.1000/related as related "
            "work."
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(request)

    assert result.guidance_seeds == (
        ResearchGuidanceSeed(
            term="arXiv:2303.16058",
            relevance=ResearchGuidanceRelevance.HIGH,
        ),
        ResearchGuidanceSeed(
            term="arXiv:2405.19009",
            relevance=ResearchGuidanceRelevance.HIGH,
        ),
        ResearchGuidanceSeed(term="doi:10.1000/related"),
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


def test_build_strategy_excludes_prioritization_from_search_concepts() -> None:
    """Source-selection instructions must not become provider queries."""

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question=(
                "How do vision-language and video-language models create "
                "a shared semantic representation space?"
            ),
            focus_areas=("Prioritize primary research papers",),
            guidance="Prioritize primary research papers.",
        )
    )

    assert "Prioritize primary research papers" not in result.concepts
    assert result.constraints == (
        "Prioritize primary research papers.",
    )


def test_build_strategy_does_not_split_wrapped_guidance_into_concepts() -> None:
    """Visual line wrapping must preserve one directive sentence."""

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question=(
                "How do state-of-the-art vision-language and "
                "video-language models learn or create a shared semantic "
                "representation space between visual and textual "
                "information?"
            ),
            guidance=(
                "Focus on major alignment approaches, foundational work, "
                "2023-2026 SOTA\n"
                "developments, and open problems relevant to learned video\n"
                "representations for VideoQA.\n"
                "Prioritize primary research papers."
            ),
        )
    )

    assert result.concepts == (
        "How do state-of-the-art vision-language and video-language models "
        "learn or create a shared semantic representation space between "
        "visual and textual information",
    )
    assert result.constraints == (
        "Focus on major alignment approaches, foundational work, 2023-2026 "
        "SOTA developments, and open problems relevant to learned video "
        "representations for VideoQA.",
        "Prioritize primary research papers.",
    )


def test_build_strategy_preserves_seed_free_technical_guidance() -> None:
    """Verify technical guidance remains available for query generation."""

    guidance = (
        "Find methods that align newly trained, self-supervised, "
        "masked-model, or autoencoder visual representations with frozen "
        "CLIP vision features or the shared CLIP vision-text embedding "
        "space. Include transferable image-domain methods even when they "
        "do not mention video or VideoQA. Assess their applicability to "
        "aligning autoencoder-generated video representations."
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question="How should video representations align with CLIP?",
            guidance=guidance,
        )
    )

    assert result.seed_terms == ()
    assert result.concepts[:3] == (
        (
            "Find methods that align newly trained, self-supervised, "
            "masked-model, or autoencoder visual representations with "
            "frozen CLIP vision features or the shared CLIP vision-text "
            "embedding space"
        ),
        (
            "Include transferable image-domain methods even when they do "
            "not mention video or VideoQA"
        ),
        (
            "Assess their applicability to aligning autoencoder-generated "
            "video representations"
        ),
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


def test_build_strategy_includes_only_searchable_context_concepts() -> None:
    """Verify context contributes only inferred search concepts."""

    context = ExistingResearchContext(
        research_problem=ResearchFinding(
            content="Video representations lack semantic alignment.",
        ),
        limitations=(
            ResearchFinding(
                content=(
                    "Reconstruction quality does not ensure "
                    "semantic usefulness."
                ),
            ),
        ),
        unresolved_questions=(
            ResearchFinding(
                content=(
                    "How should video and text representations "
                    "be aligned?"
                ),
            ),
        ),
        stated_future_work=(
            ResearchFinding(
                content=(
                    "Investigate semantic alignment objectives."
                ),
            ),
        ),
        inferred_solution_search_concepts=(
            "feature distillation frozen teacher representations",
            "token-level alignment learned visual representations",
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question="What should I investigate next?"
        ),
        context=context,
    )

    assert result.concepts == (
        "What should I investigate next",
        "feature distillation frozen teacher representations",
        "token-level alignment learned visual representations",
    )
    assert result.rationale == (
        "Research strategy derived from the submitted "
        "research question, guidance, and existing "
        "research context."
    )
    assert result.inferred_solution_search_concepts == (
        "feature distillation frozen teacher representations",
        "token-level alignment learned visual representations",
    )


def test_build_strategy_excludes_existing_project_claims() -> None:
    """Verify project findings and conclusions do not become concepts."""

    context = ExistingResearchContext(
        prior_work=(
            ResearchFinding(
                content="Prior reconstruction experiments.",
            ),
        ),
        implemented_approaches=(
            ResearchFinding(
                content="Implemented a fusion network.",
            ),
        ),
        findings=(
            ResearchFinding(
                content=(
                    "Hybrid methods performed worse than the "
                    "self-supervised autoencoder."
                ),
            ),
        ),
        limitations=(
            ResearchFinding(
                content="Semantic alignment remains unresolved.",
            ),
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question="Find relevant follow-on research."
        ),
        context=context,
    )

    assert result.concepts == (
        "Find relevant follow-on research",
    )


def test_build_strategy_deduplicates_context_concepts() -> None:
    """Verify duplicate context concepts are removed deterministically."""

    context = ExistingResearchContext(
        limitations=(
            ResearchFinding(
                content="semantic alignment",
            ),
        ),
        unresolved_questions=(
            ResearchFinding(
                content="semantic alignment",
            ),
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question="Research question.",
            guidance="semantic alignment.",
        ),
        context=context,
    )

    assert result.concepts == (
        "semantic alignment",
        "Research question",
    )


def test_build_strategy_context_none_preserves_existing_behavior() -> None:
    """Verify explicit no-context strategy matches legacy behavior."""

    request = ResearchRequest(
        question="Research question.",
        guidance="video representation learning.",
    )

    service = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    )

    assert service.build_strategy(
        request,
        context=None,
    ) == service.build_strategy(request)


def test_build_strategy_context_only_does_not_execute() -> None:
    """Verify context alone does not create an executable strategy."""

    context = ExistingResearchContext(
        limitations=(
            ResearchFinding(
                content="Semantic alignment remains unresolved.",
            ),
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(question=""),
        context=context,
    )

    assert result.objective is None
    assert result.concepts == ()
    assert result.search_terms == ()
    assert result.sub_questions == ()
    assert result.constraints == ()
    assert result.source_names == ()
    assert result.inferred_solution_search_concepts == ()


def test_build_strategy_uses_inferred_concepts_not_context_prose() -> None:
    """Verify technical mechanisms replace project-context prose."""

    context = ExistingResearchContext(
        research_problem=ResearchFinding(
            content=(
                "The primary challenge is learning compact "
                "representations that preserve useful information."
            ),
        ),
        limitations=(
            ResearchFinding(
                content=(
                    "Current reconstruction metrics do not measure "
                    "semantic alignment with language."
                ),
            ),
        ),
        unresolved_questions=(
            ResearchFinding(
                content=(
                    "How should video representations be aligned "
                    "with language representations?"
                ),
            ),
        ),
        stated_future_work=(
            ResearchFinding(
                content=(
                    "Investigate semantic alignment objectives for "
                    "video representations."
                ),
            ),
        ),
        inferred_solution_search_concepts=(
            "feature distillation frozen teacher representations",
            "token-level alignment learned visual representations",
        ),
    )

    result = ResearchStrategyService(
        source_names=DEFAULT_RESEARCH_SOURCE_PROVIDERS,
    ).build_strategy(
        ResearchRequest(
            question="What should I investigate next?"
        ),
        context=context,
    )

    assert result.concepts == (
        "What should I investigate next",
        "feature distillation frozen teacher representations",
        "token-level alignment learned visual representations",
    )
