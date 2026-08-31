# ============================================================
# Project0 - Research Model Tests
#
# File: test_research_models.py
#
# Purpose:
#     Verify Research Agent data models used by Project0
#     research workflows, services, and interfaces.
#
# ============================================================

from __future__ import annotations

from datetime import datetime

from project0.models.research_models import (
    ExistingResearchContext,
    PaperAnalysis,
    PaperMetadata,
    ResearchArtifact,
    ResearchArtifactType,
    ResearchContextDocument,
    ResearchContextDocumentType,
    ResearchContextExtractionStatus,
    ResearchDirection,
    ResearchDirectionAnalysis,
    ResearchEvaluation,
    ResearchEvidenceReference,
    ResearchEvidenceSourceType,
    ResearchFinding,
    ResearchRequest,
    ResearchResult,
    ResearchSourceReference,
    ResearchStatus,
    ResearchStrategy,
    ResearchSynthesis,
)


def test_research_status_values() -> None:
    """Verify supported research status values."""

    assert ResearchStatus.PENDING == "pending"
    assert ResearchStatus.COMPLETED == "completed"
    assert (
        ResearchStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert ResearchStatus.FAILED == "failed"


def test_research_artifact_type_values() -> None:
    """Verify supported research artifact type values."""

    assert (
        ResearchArtifactType.PAPER_SUMMARY
        == "paper_summary"
    )
    assert (
        ResearchArtifactType.LITERATURE_COMPARISON
        == "literature_comparison"
    )
    assert (
        ResearchArtifactType.RESEARCH_GAP
        == "research_gap"
    )
    assert (
        ResearchArtifactType.EXPERIMENT_PROPOSAL
        == "experiment_proposal"
    )


def test_research_context_document_type_values() -> None:
    """Verify supported research context document type values."""

    assert ResearchContextDocumentType.PDF == "pdf"
    assert ResearchContextDocumentType.MARKDOWN == "markdown"
    assert ResearchContextDocumentType.TEXT == "text"


def test_research_context_extraction_status_values() -> None:
    """Verify supported research context extraction status values."""

    assert (
        ResearchContextExtractionStatus.COMPLETED
        == "completed"
    )
    assert (
        ResearchContextExtractionStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert ResearchContextExtractionStatus.FAILED == "failed"


def test_research_evidence_source_type_values() -> None:
    """Verify supported research evidence source type values."""

    assert (
        ResearchEvidenceSourceType.CONTEXT_DOCUMENT
        == "context_document"
    )
    assert (
        ResearchEvidenceSourceType.RESEARCH_PAPER
        == "research_paper"
    )


def test_research_request_creation() -> None:
    """Verify creation of a research request."""

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
        metadata={
            "course": "ECE-551 Part 2",
        },
    )

    assert request.question == (
        "How can self-supervised video representations "
        "be improved for VideoQA?"
    )
    assert request.constraints == (
        "Focus on vision-language alignment.",
        "Prefer recent research.",
    )
    assert request.focus_areas == (
        "video representation learning",
        "multimodal alignment",
    )
    assert request.source_names == (
        "arxiv",
        "semantic_scholar",
    )
    assert request.metadata == {
        "course": "ECE-551 Part 2",
    }
    assert request.request_id


def test_research_request_defaults() -> None:
    """Verify default research request values."""

    request = ResearchRequest(
        question="Find relevant video representation research.",
    )

    assert request.constraints == ()
    assert request.focus_areas == ()
    assert request.source_names == ()
    assert request.metadata == {}
    assert request.request_id


def test_research_request_ids_are_unique() -> None:
    """Verify research requests receive unique identifiers."""

    first_request = ResearchRequest(
        question="First research question.",
    )

    second_request = ResearchRequest(
        question="Second research question.",
    )

    assert first_request.request_id != second_request.request_id


def test_research_request_metadata_is_independent() -> None:
    """Verify research requests receive independent metadata."""

    first_request = ResearchRequest(
        question="First research question.",
    )

    second_request = ResearchRequest(
        question="Second research question.",
    )

    assert first_request.metadata is not second_request.metadata


def test_research_strategy_creation() -> None:
    """Verify creation of a research strategy."""

    strategy = ResearchStrategy(
        concepts=(
            "self-supervised learning",
            "video representation learning",
            "vision-language alignment",
        ),
        search_terms=(
            "self-supervised video representation VideoQA",
            "vision-language alignment video",
        ),
        constraints=(
            "Prefer recent research.",
        ),
        source_names=(
            "arxiv",
        ),
        rationale=(
            "The strategy targets representation learning "
            "and semantic alignment."
        ),
    )

    assert strategy.concepts == (
        "self-supervised learning",
        "video representation learning",
        "vision-language alignment",
    )
    assert strategy.search_terms == (
        "self-supervised video representation VideoQA",
        "vision-language alignment video",
    )
    assert strategy.constraints == (
        "Prefer recent research.",
    )
    assert strategy.source_names == (
        "arxiv",
    )
    assert strategy.rationale == (
        "The strategy targets representation learning "
        "and semantic alignment."
    )


def test_research_strategy_defaults() -> None:
    """Verify default research strategy values."""

    strategy = ResearchStrategy(
        concepts=("video representation learning",),
        search_terms=("video representation learning",),
    )

    assert strategy.constraints == ()
    assert strategy.source_names == ()
    assert strategy.rationale is None


def test_research_source_reference_creation() -> None:
    """Verify creation of a research source reference."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Video Representation Paper",
        source_url="https://arxiv.org/abs/2401.12345",
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
        metadata={
            "category": "cs.CV",
        },
    )

    assert reference.source_name == "arxiv"
    assert reference.source_id == "2401.12345"
    assert reference.title == (
        "Example Video Representation Paper"
    )
    assert reference.source_url == (
        "https://arxiv.org/abs/2401.12345"
    )
    assert reference.authors == (
        "Author One",
        "Author Two",
    )
    assert reference.publication_year == 2024
    assert reference.metadata == {
        "category": "cs.CV",
    }


def test_research_source_reference_defaults() -> None:
    """Verify default research source reference values."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    assert reference.source_url is None
    assert reference.authors == ()
    assert reference.publication_year is None
    assert reference.metadata == {}


def test_research_source_reference_metadata_is_independent() -> None:
    """Verify source references receive independent metadata."""

    first_reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="first",
        title="First Paper",
    )

    second_reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="second",
        title="Second Paper",
    )

    assert first_reference.metadata is not second_reference.metadata


def test_paper_metadata_creation() -> None:
    """Verify creation of paper metadata."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Video Representation Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Video Representation Paper",
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
        abstract="Example abstract.",
        venue="Example Conference",
        doi="10.1000/example",
        source_url="https://arxiv.org/abs/2401.12345",
        metadata={
            "citation_count": 12,
        },
    )

    assert paper.source_reference == reference
    assert paper.title == (
        "Example Video Representation Paper"
    )
    assert paper.authors == (
        "Author One",
        "Author Two",
    )
    assert paper.publication_year == 2024
    assert paper.abstract == "Example abstract."
    assert paper.venue == "Example Conference"
    assert paper.doi == "10.1000/example"
    assert paper.source_url == (
        "https://arxiv.org/abs/2401.12345"
    )
    assert paper.metadata == {
        "citation_count": 12,
    }


def test_paper_metadata_defaults() -> None:
    """Verify default paper metadata values."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
    )

    assert paper.authors == ()
    assert paper.publication_year is None
    assert paper.abstract is None
    assert paper.venue is None
    assert paper.doi is None
    assert paper.source_url is None
    assert paper.metadata == {}


def test_paper_metadata_metadata_is_independent() -> None:
    """Verify paper metadata receives independent metadata."""

    first_reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="first",
        title="First Paper",
    )

    second_reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="second",
        title="Second Paper",
    )

    first_paper = PaperMetadata(
        source_reference=first_reference,
        title="First Paper",
    )

    second_paper = PaperMetadata(
        source_reference=second_reference,
        title="Second Paper",
    )

    assert first_paper.metadata is not second_paper.metadata


def test_research_context_document_creation() -> None:
    """Verify creation of a normalized research context document."""

    document = ResearchContextDocument(
        source_name="ECE-551_Project-1.pdf",
        document_type=ResearchContextDocumentType.PDF,
        extraction_method="pdf_text",
        extracted_text="Extracted research context.",
        extraction_status=(
            ResearchContextExtractionStatus.COMPLETED
        ),
        warnings=("Example warning.",),
        page_count=8,
    )

    assert document.source_name == "ECE-551_Project-1.pdf"
    assert document.document_type == ResearchContextDocumentType.PDF
    assert document.extraction_method == "pdf_text"
    assert document.extracted_text == "Extracted research context."
    assert (
        document.extraction_status
        == ResearchContextExtractionStatus.COMPLETED
    )
    assert document.warnings == ("Example warning.",)
    assert document.page_count == 8
    assert document.document_id


def test_research_context_document_ids_are_unique() -> None:
    """Verify research context documents receive unique identifiers."""

    first_document = ResearchContextDocument(
        source_name="first.txt",
        document_type=ResearchContextDocumentType.TEXT,
        extraction_method="plain_text",
        extracted_text="First document.",
        extraction_status=(
            ResearchContextExtractionStatus.COMPLETED
        ),
    )

    second_document = ResearchContextDocument(
        source_name="second.txt",
        document_type=ResearchContextDocumentType.TEXT,
        extraction_method="plain_text",
        extracted_text="Second document.",
        extraction_status=(
            ResearchContextExtractionStatus.COMPLETED
        ),
    )

    assert first_document.document_id != second_document.document_id


def test_research_evidence_reference_creation() -> None:
    """Verify creation of research evidence references."""

    context_reference = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
        source_id="context-001",
        page_number=4,
        section="Future Work",
    )

    paper_reference = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
        source_id="2401.12345",
    )

    assert (
        context_reference.source_type
        == ResearchEvidenceSourceType.CONTEXT_DOCUMENT
    )
    assert context_reference.source_id == "context-001"
    assert context_reference.page_number == 4
    assert context_reference.section == "Future Work"
    assert (
        paper_reference.source_type
        == ResearchEvidenceSourceType.RESEARCH_PAPER
    )
    assert paper_reference.source_id == "2401.12345"
    assert paper_reference.page_number is None
    assert paper_reference.section is None


def test_research_finding_preserves_evidence() -> None:
    """Verify research findings preserve supporting evidence."""

    evidence = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
        source_id="context-001",
        page_number=5,
    )

    finding = ResearchFinding(
        content="Semantic alignment remains unresolved.",
        evidence=(evidence,),
    )

    assert finding.content == (
        "Semantic alignment remains unresolved."
    )
    assert finding.evidence == (evidence,)


def test_existing_research_context_creation() -> None:
    """Verify structured existing research context creation."""

    evidence = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
        source_id="context-001",
        section="Results",
    )

    limitation = ResearchFinding(
        content="Fusion did not resolve semantic alignment.",
        evidence=(evidence,),
    )

    context = ExistingResearchContext(
        limitations=(limitation,),
    )

    assert context.research_problem is None
    assert context.prior_work == ()
    assert context.implemented_approaches == ()
    assert context.findings == ()
    assert context.limitations == (limitation,)
    assert context.unresolved_questions == ()
    assert context.stated_future_work == ()


def test_paper_analysis_creation() -> None:
    """Verify structured retained-paper analysis creation."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
    )

    evidence = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
        source_id=reference.source_id,
        section="Method",
    )

    problem = ResearchFinding(
        content="Align video and text representations.",
        evidence=(evidence,),
    )

    approach = ResearchFinding(
        content="Use contrastive multimodal learning.",
        evidence=(evidence,),
    )

    analysis = PaperAnalysis(
        paper=paper,
        problem=problem,
        approach=approach,
        modalities=(
            ResearchFinding(
                content="Video and text.",
                evidence=(evidence,),
            ),
        ),
    )

    assert analysis.paper == paper
    assert analysis.problem == problem
    assert analysis.approach == approach
    assert analysis.representations == ()
    assert analysis.modalities[0].content == "Video and text."
    assert analysis.learning_objectives == ()
    assert analysis.datasets_tasks == ()
    assert analysis.findings == ()
    assert analysis.limitations == ()


def test_research_synthesis_creation() -> None:
    """Verify creation of cross-paper research synthesis."""

    finding = ResearchFinding(
        content="Contrastive alignment is a recurring theme.",
    )

    synthesis = ResearchSynthesis(
        themes=(finding,),
    )

    assert synthesis.themes == (finding,)
    assert synthesis.comparisons == ()
    assert synthesis.shared_limitations == ()
    assert synthesis.unresolved_questions == ()


def test_research_direction_creation() -> None:
    """Verify evidence-grounded research direction creation."""

    context_evidence = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
        source_id="context-001",
    )

    literature_evidence = ResearchEvidenceReference(
        source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
        source_id="2401.12345",
    )

    direction = ResearchDirection(
        direction="Align the video encoder with a semantic space.",
        rationale="Prior limitations and literature support the direction.",
        context_evidence=(context_evidence,),
        literature_evidence=(literature_evidence,),
    )

    assert direction.direction == (
        "Align the video encoder with a semantic space."
    )
    assert direction.rationale == (
        "Prior limitations and literature support the direction."
    )
    assert direction.context_evidence == (context_evidence,)
    assert direction.literature_evidence == (literature_evidence,)
    assert direction.speculative is False


def test_research_direction_supports_speculative_state() -> None:
    """Verify research directions can be explicitly speculative."""

    direction = ResearchDirection(
        direction="Explore an unvalidated alignment approach.",
        rationale="The direction requires further literature support.",
        speculative=True,
    )

    assert direction.context_evidence == ()
    assert direction.literature_evidence == ()
    assert direction.speculative is True


def test_research_direction_analysis_creation() -> None:
    """Verify synthesis and candidate directions are combined."""

    synthesis = ResearchSynthesis(
        unresolved_questions=(
            ResearchFinding(
                content="How should video and text spaces be aligned?",
            ),
        ),
    )

    direction = ResearchDirection(
        direction="Evaluate shared-space video representations.",
        rationale="The unresolved question motivates evaluation.",
        speculative=True,
    )

    analysis = ResearchDirectionAnalysis(
        synthesis=synthesis,
        candidate_directions=(direction,),
    )

    assert analysis.synthesis == synthesis
    assert analysis.candidate_directions == (direction,)


def test_research_analysis_default_tuples_are_immutable_safe() -> None:
    """Verify research analysis models use independent tuple defaults."""

    first_finding = ResearchFinding(content="First finding.")
    second_finding = ResearchFinding(content="Second finding.")

    first_context = ExistingResearchContext()
    second_context = ExistingResearchContext()

    assert first_finding.evidence == ()
    assert second_finding.evidence == ()
    assert first_context.prior_work == ()
    assert second_context.prior_work == ()


def test_research_evaluation_creation() -> None:
    """Verify creation of a research evaluation."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
    )

    evaluation = ResearchEvaluation(
        paper=paper,
        relevance_score=0.92,
        relevance_summary=(
            "The paper directly addresses video representation "
            "learning and multimodal alignment."
        ),
        strengths=(
            "Strong semantic alignment method.",
        ),
        limitations=(
            "Limited VideoQA evaluation.",
        ),
        research_connections=(
            "Potential teacher-student alignment experiment.",
        ),
        warnings=(
            "Full paper review is required.",
        ),
    )

    assert evaluation.paper == paper
    assert evaluation.relevance_score == 0.92
    assert evaluation.relevance_summary == (
        "The paper directly addresses video representation "
        "learning and multimodal alignment."
    )
    assert evaluation.strengths == (
        "Strong semantic alignment method.",
    )
    assert evaluation.limitations == (
        "Limited VideoQA evaluation.",
    )
    assert evaluation.research_connections == (
        "Potential teacher-student alignment experiment.",
    )
    assert evaluation.warnings == (
        "Full paper review is required.",
    )


def test_research_evaluation_defaults() -> None:
    """Verify default research evaluation values."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
    )

    evaluation = ResearchEvaluation(
        paper=paper,
        relevance_score=None,
        relevance_summary="Relevance could not be determined.",
    )

    assert evaluation.relevance_score is None
    assert evaluation.strengths == ()
    assert evaluation.limitations == ()
    assert evaluation.research_connections == ()
    assert evaluation.warnings == ()


def test_research_artifact_creation() -> None:
    """Verify creation of a research artifact."""

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Example Paper Summary",
        content="Structured paper summary content.",
        source_references=(reference,),
        metadata={
            "reviewed": False,
        },
    )

    assert (
        artifact.artifact_type
        == ResearchArtifactType.PAPER_SUMMARY
    )
    assert artifact.title == "Example Paper Summary"
    assert artifact.content == (
        "Structured paper summary content."
    )
    assert artifact.source_references == (reference,)
    assert artifact.metadata == {
        "reviewed": False,
    }
    assert artifact.artifact_id


def test_research_artifact_defaults() -> None:
    """Verify default research artifact values."""

    artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.RESEARCH_GAP,
        title="Research Gap",
        content="Potential research gap.",
    )

    assert artifact.source_references == ()
    assert artifact.metadata == {}
    assert artifact.artifact_id


def test_research_artifact_ids_are_unique() -> None:
    """Verify research artifacts receive unique identifiers."""

    first_artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="First Artifact",
        content="First content.",
    )

    second_artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Second Artifact",
        content="Second content.",
    )

    assert (
        first_artifact.artifact_id
        != second_artifact.artifact_id
    )


def test_research_artifact_metadata_is_independent() -> None:
    """Verify research artifacts receive independent metadata."""

    first_artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="First Artifact",
        content="First content.",
    )

    second_artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Second Artifact",
        content="Second content.",
    )

    assert first_artifact.metadata is not second_artifact.metadata


def test_research_result_creation() -> None:
    """Verify creation of a completed research result."""

    created_at = datetime(2026, 8, 20, 13, 0)

    strategy = ResearchStrategy(
        concepts=(
            "video representation learning",
            "vision-language alignment",
        ),
        search_terms=(
            "video representation vision-language alignment",
        ),
    )

    reference = ResearchSourceReference(
        source_name="arxiv",
        source_id="2401.12345",
        title="Example Paper",
    )

    paper = PaperMetadata(
        source_reference=reference,
        title="Example Paper",
    )

    evaluation = ResearchEvaluation(
        paper=paper,
        relevance_score=0.9,
        relevance_summary="Highly relevant.",
    )

    artifact = ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Example Paper Summary",
        content="Summary content.",
        source_references=(reference,),
    )

    result = ResearchResult(
        request_id="research-request-123",
        status=ResearchStatus.COMPLETED,
        summary="One relevant paper was identified.",
        strategy=strategy,
        source_references=(reference,),
        papers=(paper,),
        evaluations=(evaluation,),
        artifacts=(artifact,),
        created_at=created_at,
        warnings=(),
        metadata={
            "candidate_count": 1,
        },
    )

    assert result.request_id == "research-request-123"
    assert result.status == ResearchStatus.COMPLETED
    assert result.summary == (
        "One relevant paper was identified."
    )
    assert result.strategy == strategy
    assert result.source_references == (reference,)
    assert result.papers == (paper,)
    assert result.evaluations == (evaluation,)
    assert result.artifacts == (artifact,)
    assert result.created_at == created_at
    assert result.warnings == ()
    assert result.error_message is None
    assert result.metadata == {
        "candidate_count": 1,
    }


def test_research_result_failure_creation() -> None:
    """Verify creation of a failed research result."""

    result = ResearchResult(
        request_id="research-request-456",
        status=ResearchStatus.FAILED,
        summary="Research workflow failed.",
        strategy=None,
        source_references=(),
        papers=(),
        evaluations=(),
        artifacts=(),
        created_at=datetime(2026, 8, 20, 13, 5),
        error_message="Research source was unavailable.",
    )

    assert result.status == ResearchStatus.FAILED
    assert result.strategy is None
    assert result.source_references == ()
    assert result.papers == ()
    assert result.evaluations == ()
    assert result.artifacts == ()
    assert result.error_message == (
        "Research source was unavailable."
    )


def test_research_result_defaults() -> None:
    """Verify default research result values."""

    result = ResearchResult(
        request_id="research-request-789",
        status=ResearchStatus.COMPLETED,
        summary="Research completed.",
        strategy=None,
        source_references=(),
        papers=(),
        evaluations=(),
        artifacts=(),
        created_at=datetime(2026, 8, 20, 13, 10),
    )

    assert result.warnings == ()
    assert result.error_message is None
    assert result.metadata == {}


def test_research_result_metadata_is_independent() -> None:
    """Verify research results receive independent metadata."""

    first_result = ResearchResult(
        request_id="first-request",
        status=ResearchStatus.COMPLETED,
        summary="First result.",
        strategy=None,
        source_references=(),
        papers=(),
        evaluations=(),
        artifacts=(),
        created_at=datetime(2026, 8, 20, 13, 15),
    )

    second_result = ResearchResult(
        request_id="second-request",
        status=ResearchStatus.COMPLETED,
        summary="Second result.",
        strategy=None,
        source_references=(),
        papers=(),
        evaluations=(),
        artifacts=(),
        created_at=datetime(2026, 8, 20, 13, 16),
    )

    assert first_result.metadata is not second_result.metadata
