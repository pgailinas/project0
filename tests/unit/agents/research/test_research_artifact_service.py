# ============================================================
# Project0 - Research Artifact Service Tests
#
# File: test_research_artifact_service.py
#
# Purpose:
#     Verify Research Agent artifact generation, source
#     preservation, deduplication, and deterministic output.
#
# ============================================================

from __future__ import annotations

from project0.agents.research.research_artifact_service import (
    ResearchArtifactService,
)
from project0.models.research_models import (
    PaperMetadata,
    ResearchArtifactType,
    ResearchEvaluation,
    ResearchRequest,
    ResearchSourceReference,
)


def create_research_request() -> ResearchRequest:
    """Create a representative research request."""

    return ResearchRequest(
        question=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
    )


def create_source_reference(
    source_id: str = "paper-001",
    title: str = "Example Video Representation Paper",
) -> ResearchSourceReference:
    """Create a representative research source reference."""

    return ResearchSourceReference(
        source_name="semantic_scholar",
        source_id=source_id,
        title=title,
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
    )


def create_paper_metadata(
    source_id: str = "paper-001",
    title: str = "Example Video Representation Paper",
) -> PaperMetadata:
    """Create representative paper metadata."""

    reference = create_source_reference(
        source_id=source_id,
        title=title,
    )

    return PaperMetadata(
        source_reference=reference,
        title=title,
        authors=reference.authors,
        publication_year=2024,
        abstract="Example abstract.",
    )


def create_research_evaluation(
    source_id: str = "paper-001",
    title: str = "Example Video Representation Paper",
    relevance_score: float | None = 0.95,
    limitations: tuple[str, ...] = (
        "Limited VideoQA evaluation.",
    ),
    research_connections: tuple[str, ...] = (
        "Supports a vision-language alignment experiment.",
    ),
    warnings: tuple[str, ...] = (),
) -> ResearchEvaluation:
    """Create a representative research evaluation."""

    return ResearchEvaluation(
        paper=create_paper_metadata(
            source_id=source_id,
            title=title,
        ),
        relevance_score=relevance_score,
        relevance_summary=(
            "The paper is highly relevant to the research question."
        ),
        strengths=(
            "Uses semantic representation learning.",
        ),
        limitations=limitations,
        research_connections=research_connections,
        warnings=warnings,
    )


def test_research_artifact_service_generates_expected_artifacts() -> None:
    """Verify complete research artifact generation."""

    service = ResearchArtifactService()

    result = service.generate_artifacts(
        create_research_request(),
        (create_research_evaluation(),),
    )

    assert len(result) == 3
    assert result[0].artifact_type == (
        ResearchArtifactType.LITERATURE_COMPARISON
    )
    assert result[1].artifact_type == (
        ResearchArtifactType.RESEARCH_GAP
    )
    assert result[2].artifact_type == (
        ResearchArtifactType.EXPERIMENT_PROPOSAL
    )


def test_research_artifact_service_generates_literature_comparison() -> None:
    """Verify literature comparison contains each evaluation."""

    first = create_research_evaluation(
        source_id="paper-001",
        title="First Paper",
        relevance_score=0.9,
    )
    second = create_research_evaluation(
        source_id="paper-002",
        title="Second Paper",
        relevance_score=0.7,
    )

    artifact = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (
            first,
            second,
        ),
    )[0]

    assert artifact.title == "Literature Comparison"
    assert "Paper: First Paper" in artifact.content
    assert "Relevance Score: 0.9" in artifact.content
    assert "Paper: Second Paper" in artifact.content
    assert "Relevance Score: 0.7" in artifact.content
    assert artifact.source_references == ()


def test_research_artifact_service_generates_research_gap() -> None:
    """Verify research gap artifact uses limitations and connections."""

    evaluation = create_research_evaluation()

    artifact = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (evaluation,),
    )[1]

    assert artifact.title == "Research Gap Analysis"
    assert (
        "Research Question: How can self-supervised video "
        "representations be improved for VideoQA?"
        in artifact.content
    )
    assert "Observed Limitations:" in artifact.content
    assert "- Limited VideoQA evaluation." in artifact.content
    assert "Potential Research Opportunities:" in artifact.content
    assert (
        "- Supports a vision-language alignment experiment."
        in artifact.content
    )


def test_research_artifact_service_generates_experiment_proposal() -> None:
    """Verify experiment proposal contains research connections."""

    evaluation = create_research_evaluation()

    artifact = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (evaluation,),
    )[2]

    assert artifact.title == "Experiment Proposal"
    assert "Experiment Directions:" in artifact.content
    assert (
        "- Supports a vision-language alignment experiment."
        in artifact.content
    )


def test_research_artifact_service_omits_synthesis_source_references() -> None:
    """Verify synthesis artifacts do not repeat source references."""

    first = create_research_evaluation()
    second = ResearchEvaluation(
        paper=first.paper,
        relevance_score=0.8,
        relevance_summary="Second evaluation.",
    )

    result = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (
            first,
            second,
        ),
    )

    comparison = result[0]
    research_gap = result[1]
    experiment = result[2]

    assert comparison.source_references == ()
    assert research_gap.source_references == ()
    assert experiment.source_references == ()


def test_research_artifact_service_deduplicates_limitations() -> None:
    """Verify repeated limitations appear once in research gaps."""

    first = create_research_evaluation(
        source_id="paper-001",
        title="First Paper",
        limitations=(
            "Limited VideoQA evaluation.",
        ),
    )
    second = create_research_evaluation(
        source_id="paper-002",
        title="Second Paper",
        limitations=(
            "Limited VideoQA evaluation.",
        ),
    )

    artifact = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (
            first,
            second,
        ),
    )[1]

    assert artifact.content.count(
        "- Limited VideoQA evaluation."
    ) == 1


def test_research_artifact_service_deduplicates_connections() -> None:
    """Verify repeated research connections appear once."""

    first = create_research_evaluation(
        source_id="paper-001",
        title="First Paper",
        research_connections=(
            "Evaluate vision-language alignment.",
        ),
    )
    second = create_research_evaluation(
        source_id="paper-002",
        title="Second Paper",
        research_connections=(
            "Evaluate vision-language alignment.",
        ),
    )

    artifacts = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (
            first,
            second,
        ),
    )

    assert artifacts[1].content.count(
        "- Evaluate vision-language alignment."
    ) == 1
    assert artifacts[2].content.count(
        "- Evaluate vision-language alignment."
    ) == 1


def test_research_artifact_service_preserves_unique_item_order() -> None:
    """Verify unique research items preserve source order."""

    first = create_research_evaluation(
        source_id="paper-001",
        title="First Paper",
        limitations=(
            "First limitation.",
            "Shared limitation.",
        ),
    )
    second = create_research_evaluation(
        source_id="paper-002",
        title="Second Paper",
        limitations=(
            "Shared limitation.",
            "Second limitation.",
        ),
    )

    artifact = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (
            first,
            second,
        ),
    )[1]

    assert artifact.content.index("- First limitation.") < (
        artifact.content.index("- Shared limitation.")
    )
    assert artifact.content.index("- Shared limitation.") < (
        artifact.content.index("- Second limitation.")
    )


def test_research_artifact_service_returns_empty_for_no_evaluations() -> None:
    """Verify empty research evaluations produce no artifacts."""

    result = ResearchArtifactService().generate_artifacts(
        create_research_request(),
        (),
    )

    assert result == ()


def test_research_artifact_service_returns_deterministic_content() -> None:
    """Verify repeated artifact generation is deterministic."""

    request = create_research_request()
    evaluations = (
        create_research_evaluation(),
    )

    service = ResearchArtifactService()

    first_result = service.generate_artifacts(
        request,
        evaluations,
    )
    second_result = service.generate_artifacts(
        request,
        evaluations,
    )

    assert tuple(
        (
            artifact.artifact_type,
            artifact.title,
            artifact.content,
            artifact.source_references,
            artifact.metadata,
        )
        for artifact in first_result
    ) == tuple(
        (
            artifact.artifact_type,
            artifact.title,
            artifact.content,
            artifact.source_references,
            artifact.metadata,
        )
        for artifact in second_result
    )

