# ============================================================
# Project0 - Research Workflow Tests
#
# File: test_research_workflow.py
#
# Purpose:
#     Verify orchestration behavior for the Project0
#     Research Agent workflow.
#
# ============================================================

from datetime import UTC, datetime

from project0.models.research_models import (
    ExistingResearchContext,
    PaperMetadata,
    ResearchArtifact,
    ResearchArtifactType,
    ResearchContextDocument,
    ResearchContextDocumentType,
    ResearchContextExtractionStatus,
    ResearchEvaluation,
    ResearchFinding,
    ResearchPaperAcquisition,
    ResearchPaperAcquisitionStatus,
    ResearchPaperAnalysisBasis,
    ResearchPaperDocument,
    ResearchPaperDocumentType,
    ResearchPaperExtractionStatus,
    ResearchPaperPage,
    ResearchRequest,
    ResearchResult,
    ResearchSourceReference,
    ResearchStatus,
    ResearchStrategy,
)
from project0.workflow.research_workflow import ResearchWorkflow


class StubResearchStrategyService:
    """Return a configured research strategy."""

    def __init__(
        self,
        strategy: ResearchStrategy,
        error: Exception | None = None,
    ) -> None:
        self._strategy = strategy
        self._error = error
        self.requests: list[ResearchRequest] = []
        self.contexts: list[ExistingResearchContext | None] = []

    def build_strategy(
        self,
        request: ResearchRequest,
        context: ExistingResearchContext | None = None,
    ) -> ResearchStrategy:
        self.requests.append(request)
        self.contexts.append(context)

        if self._error is not None:
            raise self._error

        return self._strategy


class StubResearchContextIngestionService:
    """Return a configured normalized research context document."""

    def __init__(
        self,
        document: ResearchContextDocument,
        error: Exception | None = None,
    ) -> None:
        self._document = document
        self._error = error
        self.requests: list[tuple[str, bytes]] = []

    def ingest(
        self,
        source_name: str,
        content: bytes,
    ) -> ResearchContextDocument:
        self.requests.append(
            (
                source_name,
                content,
            )
        )

        if self._error is not None:
            raise self._error

        return self._document


class StubExistingResearchContextAnalysisService:
    """Return configured existing research context analysis."""

    def __init__(
        self,
        context: ExistingResearchContext,
        error: Exception | None = None,
    ) -> None:
        self._context = context
        self._error = error
        self.requests: list[ResearchContextDocument] = []

    def analyze(
        self,
        document: ResearchContextDocument,
    ) -> ExistingResearchContext:
        self.requests.append(document)

        if self._error is not None:
            raise self._error

        return self._context


class StubResearchQueryService:
    """Return a configured research strategy with generated queries."""

    def __init__(
        self,
        strategy: ResearchStrategy,
        error: Exception | None = None,
    ) -> None:
        self._strategy = strategy
        self._error = error
        self.requests: list[ResearchStrategy] = []

    def generate_queries(
        self,
        strategy: ResearchStrategy,
    ) -> ResearchStrategy:
        self.requests.append(strategy)

        if self._error is not None:
            raise self._error

        return self._strategy


class StubResearchSourceService:
    """Return configured research source references."""

    def __init__(
        self,
        references: tuple[ResearchSourceReference, ...],
        error: Exception | None = None,
    ) -> None:
        self._references = references
        self._error = error
        self.requests: list[ResearchStrategy] = []

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        self.requests.append(strategy)

        if self._error is not None:
            raise self._error

        return self._references


class StubPaperMetadataService:
    """Return configured paper metadata."""

    def __init__(
        self,
        papers: tuple[PaperMetadata, ...],
        error: Exception | None = None,
    ) -> None:
        self._papers = papers
        self._error = error
        self.requests: list[
            tuple[ResearchSourceReference, ...]
        ] = []

    def retrieve_metadata(
        self,
        references: tuple[ResearchSourceReference, ...],
    ) -> tuple[PaperMetadata, ...]:
        self.requests.append(references)

        if self._error is not None:
            raise self._error

        return self._papers


class StubResearchEvaluationService:
    """Return configured research evaluations."""

    def __init__(
        self,
        evaluations: tuple[ResearchEvaluation, ...],
        error: Exception | None = None,
    ) -> None:
        self._evaluations = evaluations
        self._error = error
        self.requests: list[
            tuple[
                ResearchRequest,
                ResearchStrategy,
                tuple[PaperMetadata, ...],
            ]
        ] = []

    def evaluate(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        self.requests.append(
            (
                request,
                strategy,
                papers,
            )
        )

        if self._error is not None:
            raise self._error

        return self._evaluations


class StubResearchPaperAcquisitionService:
    """Return configured retained-paper acquisition results."""

    def __init__(
        self,
        acquisitions: dict[str, ResearchPaperAcquisition],
        error: Exception | None = None,
    ) -> None:
        self._acquisitions = acquisitions
        self._error = error
        self.requests: list[PaperMetadata] = []

    def acquire(
        self,
        paper: PaperMetadata,
    ) -> ResearchPaperAcquisition:
        self.requests.append(paper)

        if self._error is not None:
            raise self._error

        return self._acquisitions[
            paper.source_reference.source_id
        ]


class StubResearchPaperIngestionService:
    """Return configured normalized retained-paper documents."""

    def __init__(
        self,
        documents: dict[str, ResearchPaperDocument],
        error: Exception | None = None,
    ) -> None:
        self._documents = documents
        self._error = error
        self.requests: list[ResearchPaperAcquisition] = []

    def ingest(
        self,
        acquisition: ResearchPaperAcquisition,
    ) -> ResearchPaperDocument:
        self.requests.append(acquisition)

        if self._error is not None:
            raise self._error

        return self._documents[
            acquisition.paper.source_reference.source_id
        ]


class StubPaperAnalysisService:
    """Record retained-paper analysis requests."""

    def __init__(
        self,
        error: Exception | None = None,
    ) -> None:
        self._error = error
        self.requests: list[tuple] = []

    def analyze(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
        paper_documents: tuple[ResearchPaperDocument, ...] = (),
    ) -> tuple:
        self.requests.append(
            (
                request,
                strategy,
                papers,
                paper_documents,
            )
        )

        if self._error is not None:
            raise self._error

        return ()


class StubResearchArtifactService:
    """Return configured research artifacts."""

    def __init__(
        self,
        artifacts: tuple[ResearchArtifact, ...],
        error: Exception | None = None,
    ) -> None:
        self._artifacts = artifacts
        self._error = error
        self.requests: list[
            tuple[
                ResearchRequest,
                tuple[ResearchEvaluation, ...],
            ]
        ] = []

    def generate_artifacts(
        self,
        request: ResearchRequest,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> tuple[ResearchArtifact, ...]:
        self.requests.append(
            (
                request,
                evaluations,
            )
        )

        if self._error is not None:
            raise self._error

        return self._artifacts


def _research_request(
    max_results: int = 10,
) -> ResearchRequest:
    """Create a research request for workflow tests."""

    return ResearchRequest(
        question=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        max_results=max_results,
        constraints=(
            "Focus on vision-language alignment.",
        ),
        focus_areas=(
            "video representation learning",
        ),
        source_names=(
            "arxiv",
        ),
        metadata={
            "course": "ECE-551 Part 2",
        },
    )


def _research_strategy() -> ResearchStrategy:
    """Create a research strategy for workflow tests."""

    return ResearchStrategy(
        concepts=(
            "self-supervised learning",
            "video representation learning",
        ),
        search_terms=(
            "self-supervised video representation VideoQA",
        ),
        objective=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        sub_questions=(),
        constraints=(
            "Focus on vision-language alignment.",
        ),
        source_names=(
            "arxiv",
        ),
        rationale="Search for relevant video representation research.",
    )


def _context_document() -> ResearchContextDocument:
    """Create a normalized research context document for workflow tests."""

    return ResearchContextDocument(
        source_name="prior_research.txt",
        document_type=ResearchContextDocumentType.TEXT,
        extraction_method="utf-8",
        extracted_text=(
            "Prior research identified limited semantic alignment."
        ),
        extraction_status=(
            ResearchContextExtractionStatus.COMPLETED
        ),
    )


def _existing_research_context() -> ExistingResearchContext:
    """Create existing research context for workflow tests."""

    return ExistingResearchContext(
        limitations=(
            ResearchFinding(
                content=(
                    "Video representations were not aligned with "
                    "language representations."
                ),
            ),
        ),
    )


def _source_reference(
    source_id: str = "2401.12345",
    title: str = "Example Paper",
) -> ResearchSourceReference:
    """Create a research source reference for workflow tests."""

    return ResearchSourceReference(
        source_name="arxiv",
        source_id=source_id,
        title=title,
        source_url=f"https://arxiv.org/abs/{source_id}",
        authors=(
            "Author One",
            "Author Two",
        ),
        publication_year=2024,
    )


def _paper_metadata(
    reference: ResearchSourceReference,
) -> PaperMetadata:
    """Create paper metadata for workflow tests."""

    return PaperMetadata(
        source_reference=reference,
        title=reference.title,
        authors=reference.authors,
        publication_year=reference.publication_year,
        abstract="Example abstract.",
        source_url=reference.source_url,
    )


def _evaluation(
    paper: PaperMetadata,
    relevance_score: float | None = 0.9,
) -> ResearchEvaluation:
    """Create a research evaluation for workflow tests."""

    return ResearchEvaluation(
        paper=paper,
        relevance_score=relevance_score,
        relevance_summary="Highly relevant to the research question.",
        strengths=(
            "Uses semantic representation learning.",
        ),
        limitations=(
            "Limited VideoQA evaluation.",
        ),
        research_connections=(
            "Supports a vision-language alignment experiment.",
        ),
    )


def _paper_acquisition(
    paper: PaperMetadata,
    *,
    acquired: bool = True,
) -> ResearchPaperAcquisition:
    """Create retained-paper acquisition data for workflow tests."""

    if not acquired:
        return ResearchPaperAcquisition(
            paper=paper,
            source_url=None,
            content=None,
            acquisition_status=ResearchPaperAcquisitionStatus.UNAVAILABLE,
            warnings=("Full text unavailable.",),
        )

    return ResearchPaperAcquisition(
        paper=paper,
        source_url="https://example.test/paper.pdf",
        content=b"%PDF-example",
        acquisition_status=ResearchPaperAcquisitionStatus.ACQUIRED,
        content_type="application/pdf",
    )


def _paper_document(
    paper: PaperMetadata,
) -> ResearchPaperDocument:
    """Create a normalized retained-paper document for workflow tests."""

    return ResearchPaperDocument(
        paper=paper,
        source_url="https://example.test/paper.pdf",
        document_type=ResearchPaperDocumentType.PDF,
        extraction_method="pypdf",
        pages=(
            ResearchPaperPage(
                page_number=1,
                text="Example full-text research paper content.",
            ),
        ),
        extraction_status=ResearchPaperExtractionStatus.COMPLETED,
    )


def _artifact(
    reference: ResearchSourceReference,
) -> ResearchArtifact:
    """Create a research artifact for workflow tests."""

    return ResearchArtifact(
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Example Paper Summary",
        content="Structured research artifact content.",
        source_references=(reference,),
    )


def _create_workflow(
    *,
    strategy: ResearchStrategy | None = None,
    references: tuple[ResearchSourceReference, ...] | None = None,
    papers: tuple[PaperMetadata, ...] | None = None,
    evaluations: tuple[ResearchEvaluation, ...] | None = None,
    artifacts: tuple[ResearchArtifact, ...] | None = None,
    strategy_error: Exception | None = None,
    query_error: Exception | None = None,
    source_error: Exception | None = None,
    metadata_error: Exception | None = None,
    evaluation_error: Exception | None = None,
    artifact_error: Exception | None = None,
    context_ingestion_service=None,
    context_analysis_service=None,
    paper_acquisition_service=None,
    paper_ingestion_service=None,
    paper_analysis_service=None,
):
    """Create a workflow and its test doubles."""

    configured_strategy = strategy or _research_strategy()

    configured_references = (
        references
        if references is not None
        else (_source_reference(),)
    )

    configured_papers = (
        papers
        if papers is not None
        else tuple(
            _paper_metadata(reference)
            for reference in configured_references
        )
    )

    configured_evaluations = (
        evaluations
        if evaluations is not None
        else tuple(
            _evaluation(paper)
            for paper in configured_papers
        )
    )

    configured_artifacts = (
        artifacts
        if artifacts is not None
        else tuple(
            _artifact(reference)
            for reference in configured_references[:1]
        )
    )

    strategy_service = StubResearchStrategyService(
        configured_strategy,
        strategy_error,
    )
    query_service = StubResearchQueryService(
        configured_strategy,
        query_error,
    )
    source_service = StubResearchSourceService(
        configured_references,
        source_error,
    )
    metadata_service = StubPaperMetadataService(
        configured_papers,
        metadata_error,
    )
    evaluation_service = StubResearchEvaluationService(
        configured_evaluations,
        evaluation_error,
    )
    artifact_service = StubResearchArtifactService(
        configured_artifacts,
        artifact_error,
    )

    workflow = ResearchWorkflow(
        strategy_service=strategy_service,
        query_service=query_service,
        source_service=source_service,
        metadata_service=metadata_service,
        evaluation_service=evaluation_service,
        artifact_service=artifact_service,
        context_ingestion_service=context_ingestion_service,
        context_analysis_service=context_analysis_service,
        paper_acquisition_service=paper_acquisition_service,
        paper_ingestion_service=paper_ingestion_service,
        paper_analysis_service=paper_analysis_service,
    )

    return (
        workflow,
        strategy_service,
        query_service,
        source_service,
        metadata_service,
        evaluation_service,
        artifact_service,
    )


def test_completed_research_workflow_returns_result() -> None:
    """A successful research workflow returns a completed result."""

    components = _create_workflow()
    workflow = components[0]

    request = _research_request()

    result = workflow.execute(request)

    assert result.status is ResearchStatus.COMPLETED
    assert result.request_id == request.request_id
    assert result.strategy == _research_strategy()
    assert len(result.source_references) == 1
    assert len(result.papers) == 1
    assert len(result.evaluations) == 1
    assert len(result.artifacts) == 1
    assert result.warnings == ()
    assert result.error_message is None


def test_workflow_forwards_request_and_results_between_services() -> None:
    """Workflow outputs are forwarded to dependent services."""

    components = _create_workflow()
    (
        workflow,
        strategy_service,
        query_service,
        source_service,
        metadata_service,
        evaluation_service,
        artifact_service,
    ) = components

    request = _research_request()

    result = workflow.execute(request)

    assert strategy_service.requests == [request]
    assert query_service.requests == [
        result.strategy
    ]
    assert source_service.requests == [result.strategy]
    assert metadata_service.requests == [
        result.source_references
    ]
    assert evaluation_service.requests == [
        (
            request,
            result.strategy,
            result.papers,
        )
    ]
    assert artifact_service.requests == [
        (
            request,
            result.evaluations,
        )
    ]


def test_no_source_references_produces_warning() -> None:
    """No research source results produce a warning."""

    workflow = _create_workflow(
        references=(),
        papers=(),
        evaluations=(),
        artifacts=(),
    )[0]

    result = workflow.execute(_research_request())

    assert (
        result.status
        is ResearchStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.source_references == ()
    assert result.papers == ()
    assert result.evaluations == ()
    assert result.artifacts == ()
    assert result.warnings == (
        "No candidate research sources were found.",
    )


def test_partial_metadata_produces_warning() -> None:
    """Missing metadata for a source produces a warning."""

    first_reference = _source_reference(
        source_id="2401.11111",
        title="First Paper",
    )
    second_reference = _source_reference(
        source_id="2401.22222",
        title="Second Paper",
    )

    first_paper = _paper_metadata(first_reference)

    workflow = _create_workflow(
        references=(
            first_reference,
            second_reference,
        ),
        papers=(first_paper,),
        evaluations=(
            _evaluation(first_paper),
        ),
        artifacts=(
            _artifact(first_reference),
        ),
    )[0]

    result = workflow.execute(_research_request())

    assert (
        result.status
        is ResearchStatus.COMPLETED_WITH_WARNINGS
    )
    assert len(result.source_references) == 2
    assert len(result.papers) == 1
    assert result.warnings == (
        "Metadata could not be retrieved for one or more "
        "research source references.",
    )


def test_summary_reports_result_counts() -> None:
    """Completed workflow summary reports result counts."""

    result = _create_workflow()[0].execute(
        _research_request()
    )

    assert result.summary == (
        "Research workflow completed with "
        "1 source reference(s), "
        "1 paper metadata record(s), "
        "1 evaluation(s), and "
        "1 artifact(s)."
    )


def test_workflow_orders_and_limits_results_by_relevance() -> None:
    """Workflow should return only the highest-relevance results."""

    references = (
        _source_reference(
            source_id="2401.11111",
            title="Lower Relevance Paper",
        ),
        _source_reference(
            source_id="2401.22222",
            title="Highest Relevance Paper",
        ),
        _source_reference(
            source_id="2401.33333",
            title="Middle Relevance Paper",
        ),
    )
    papers = tuple(
        _paper_metadata(reference)
        for reference in references
    )
    evaluations = (
        _evaluation(papers[0], relevance_score=0.2),
        _evaluation(papers[1], relevance_score=0.95),
        _evaluation(papers[2], relevance_score=0.7),
    )

    components = _create_workflow(
        references=references,
        papers=papers,
        evaluations=evaluations,
        artifacts=(),
    )
    workflow = components[0]
    artifact_service = components[6]

    request = _research_request(
        max_results=2
    )
    result = workflow.execute(
        request
    )

    assert tuple(
        evaluation.relevance_score
        for evaluation in result.evaluations
    ) == (
        0.95,
        0.7,
    )
    assert tuple(
        paper.title
        for paper in result.papers
    ) == (
        "Highest Relevance Paper",
        "Middle Relevance Paper",
    )
    assert result.source_references == references
    assert artifact_service.requests == [
        (
            request,
            result.evaluations,
        )
    ]


def test_strategy_failure_stops_workflow() -> None:
    """A strategy service failure stops later workflow services."""

    components = _create_workflow(
        strategy_error=ValueError("Strategy failed."),
    )
    (
        workflow,
        _,
        _,
        source_service,
        metadata_service,
        evaluation_service,
        artifact_service,
    ) = components

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Strategy failed."
    assert result.strategy is None
    assert result.source_references == ()
    assert result.papers == ()
    assert result.evaluations == ()
    assert result.artifacts == ()
    assert source_service.requests == []
    assert metadata_service.requests == []
    assert evaluation_service.requests == []
    assert artifact_service.requests == []



def test_query_failure_returns_failed_result() -> None:
    """A query service failure returns a failed result."""

    components = _create_workflow(
        query_error=RuntimeError("Query generation failed."),
    )
    workflow = components[0]
    source_service = components[3]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Query generation failed."
    assert source_service.requests == []


def test_rate_limit_failure_returns_user_friendly_error() -> None:
    """A provider rate-limit failure returns a user-friendly message."""

    workflow = _create_workflow(
        source_error=RuntimeError(
            "Semantic Scholar request failed with HTTP status 429."
        ),
    )[0]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == (
        "The configured research source is temporarily "
        "unavailable due to rate limiting. "
        "Please retry later."
    )


def test_source_failure_returns_failed_result() -> None:
    """A source service failure returns a failed result."""

    components = _create_workflow(
        source_error=RuntimeError("Source search failed."),
    )
    workflow = components[0]
    metadata_service = components[4]
    evaluation_service = components[5]
    artifact_service = components[6]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Source search failed."
    assert metadata_service.requests == []
    assert evaluation_service.requests == []
    assert artifact_service.requests == []


def test_metadata_failure_returns_failed_result() -> None:
    """A metadata service failure returns a failed result."""

    components = _create_workflow(
        metadata_error=OSError("Metadata retrieval failed."),
    )
    workflow = components[0]
    evaluation_service = components[5]
    artifact_service = components[6]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == (
        "Metadata retrieval failed."
    )
    assert evaluation_service.requests == []
    assert artifact_service.requests == []


def test_evaluation_failure_returns_failed_result() -> None:
    """An evaluation service failure returns a failed result."""

    components = _create_workflow(
        evaluation_error=TypeError("Evaluation failed."),
    )
    workflow = components[0]
    artifact_service = components[6]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Evaluation failed."
    assert artifact_service.requests == []


def test_artifact_failure_returns_failed_result() -> None:
    """An artifact service failure returns a failed result."""

    workflow = _create_workflow(
        artifact_error=RuntimeError(
            "Artifact generation failed."
        ),
    )[0]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == (
        "Artifact generation failed."
    )


def test_failure_result_preserves_existing_warnings() -> None:
    """Warnings collected before failure remain in failed results."""

    workflow = _create_workflow(
        references=(),
        papers=(),
        evaluations=(),
        artifacts=(),
        metadata_error=RuntimeError(
            "Metadata service unavailable."
        ),
    )[0]

    result = workflow.execute(_research_request())

    assert result.status is ResearchStatus.FAILED
    assert result.warnings == (
        "No candidate research sources were found.",
    )
    assert result.error_message == (
        "Metadata service unavailable."
    )


def test_workflow_result_timestamp_is_timezone_aware() -> None:
    """Research workflow result timestamp is timezone-aware."""

    before = datetime.now(UTC)

    result = _create_workflow()[0].execute(
        _research_request()
    )

    after = datetime.now(UTC)

    assert result.created_at.tzinfo is UTC
    assert before <= result.created_at <= after


def test_failed_result_timestamp_is_timezone_aware() -> None:
    """Failed research workflow timestamp is timezone-aware."""

    before = datetime.now(UTC)

    result = _create_workflow(
        strategy_error=ValueError("Strategy failed."),
    )[0].execute(
        _research_request()
    )

    after = datetime.now(UTC)

    assert result.status is ResearchStatus.FAILED
    assert result.created_at.tzinfo is UTC
    assert before <= result.created_at <= after


def test_research_result_is_created_from_configured_outputs() -> None:
    """Configured service outputs are preserved in the result."""

    strategy = ResearchStrategy(
        concepts=("contrastive learning",),
        search_terms=("contrastive video learning",),
        rationale="Custom strategy.",
    )

    reference = _source_reference(
        source_id="2501.98765",
        title="Custom Paper",
    )
    paper = _paper_metadata(reference)
    evaluation = _evaluation(paper)
    artifact = _artifact(reference)

    workflow = _create_workflow(
        strategy=strategy,
        references=(reference,),
        papers=(paper,),
        evaluations=(evaluation,),
        artifacts=(artifact,),
    )[0]

    result = workflow.execute(_research_request())

    assert result.strategy == strategy
    assert result.source_references == (reference,)
    assert result.papers == (paper,)
    assert result.evaluations == (evaluation,)
    assert result.artifacts == (artifact,)


def test_workflow_uses_query_service_strategy_for_downstream_services() -> None:
    """Workflow should use query-enriched strategy for later stages."""

    original_strategy = ResearchStrategy(
        concepts=("video representation alignment",),
        search_terms=(),
        objective="Find video representation alignment research.",
        source_names=("arxiv",),
    )
    enriched_strategy = ResearchStrategy(
        concepts=original_strategy.concepts,
        search_terms=("video representation alignment",),
        objective=original_strategy.objective,
        source_names=original_strategy.source_names,
    )

    components = _create_workflow(
        strategy=original_strategy,
    )
    (
        workflow,
        _,
        query_service,
        source_service,
        _,
        evaluation_service,
        _,
    ) = components

    query_service._strategy = enriched_strategy

    request = _research_request()
    result = workflow.execute(request)

    assert query_service.requests == [original_strategy]
    assert source_service.requests == [enriched_strategy]
    assert evaluation_service.requests[0][1] == enriched_strategy
    assert result.strategy == enriched_strategy


def test_workflow_ingests_analyzes_and_forwards_context() -> None:
    """Context input is normalized, analyzed, and sent to strategy."""

    document = _context_document()
    context = _existing_research_context()
    ingestion_service = StubResearchContextIngestionService(
        document
    )
    context_analysis_service = (
        StubExistingResearchContextAnalysisService(
            context
        )
    )

    components = _create_workflow(
        context_ingestion_service=ingestion_service,
        context_analysis_service=context_analysis_service,
    )
    workflow = components[0]
    strategy_service = components[1]

    content = b"Prior research context."
    result = workflow.execute(
        _research_request(),
        context_source_name="prior_research.txt",
        context_content=content,
    )

    assert result.status is ResearchStatus.COMPLETED
    assert ingestion_service.requests == [
        (
            "prior_research.txt",
            content,
        )
    ]
    assert context_analysis_service.requests == [
        document
    ]
    assert strategy_service.contexts == [
        context
    ]


def test_workflow_rejects_partial_context_input() -> None:
    """Context source name and content must be supplied together."""

    workflow = _create_workflow()[0]

    source_only_result = workflow.execute(
        _research_request(),
        context_source_name="prior_research.txt",
    )
    content_only_result = workflow.execute(
        _research_request(),
        context_content=b"Prior research context.",
    )

    assert source_only_result.status is ResearchStatus.FAILED
    assert source_only_result.error_message == (
        "Research context source name and content "
        "must be provided together."
    )
    assert content_only_result.status is ResearchStatus.FAILED
    assert content_only_result.error_message == (
        "Research context source name and content "
        "must be provided together."
    )


def test_context_ingestion_failure_stops_workflow() -> None:
    """A context ingestion failure stops later workflow services."""

    ingestion_service = StubResearchContextIngestionService(
        _context_document(),
        ValueError("Context ingestion failed."),
    )
    context_analysis_service = (
        StubExistingResearchContextAnalysisService(
            _existing_research_context()
        )
    )

    components = _create_workflow(
        context_ingestion_service=ingestion_service,
        context_analysis_service=context_analysis_service,
    )
    workflow = components[0]
    strategy_service = components[1]
    query_service = components[2]

    result = workflow.execute(
        _research_request(),
        context_source_name="prior_research.txt",
        context_content=b"Prior research context.",
    )

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Context ingestion failed."
    assert context_analysis_service.requests == []
    assert strategy_service.requests == []
    assert query_service.requests == []


def test_context_analysis_failure_stops_workflow() -> None:
    """A context analysis failure stops later workflow services."""

    ingestion_service = StubResearchContextIngestionService(
        _context_document()
    )
    context_analysis_service = (
        StubExistingResearchContextAnalysisService(
            _existing_research_context(),
            ValueError("Context analysis failed."),
        )
    )

    components = _create_workflow(
        context_ingestion_service=ingestion_service,
        context_analysis_service=context_analysis_service,
    )
    workflow = components[0]
    strategy_service = components[1]
    query_service = components[2]

    result = workflow.execute(
        _research_request(),
        context_source_name="prior_research.txt",
        context_content=b"Prior research context.",
    )

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Context analysis failed."
    assert strategy_service.requests == []
    assert query_service.requests == []

def test_workflow_acquires_ingests_and_analyzes_retained_papers() -> None:
    """Retained papers are acquired, ingested, and analyzed."""

    reference = _source_reference()
    paper = _paper_metadata(reference)
    acquisition = _paper_acquisition(paper)
    document = _paper_document(paper)

    acquisition_service = StubResearchPaperAcquisitionService(
        {
            reference.source_id: acquisition,
        }
    )
    ingestion_service = StubResearchPaperIngestionService(
        {
            reference.source_id: document,
        }
    )
    analysis_service = StubPaperAnalysisService()

    workflow = _create_workflow(
        references=(reference,),
        papers=(paper,),
        evaluations=(
            _evaluation(paper),
        ),
        paper_acquisition_service=acquisition_service,
        paper_ingestion_service=ingestion_service,
        paper_analysis_service=analysis_service,
    )[0]

    request = _research_request()
    result = workflow.execute(request)

    assert result.status is ResearchStatus.COMPLETED
    assert acquisition_service.requests == [
        paper
    ]
    assert ingestion_service.requests == [
        acquisition
    ]
    assert analysis_service.requests == [
        (
            request,
            result.strategy,
            result.papers,
            (document,),
        )
    ]


def test_workflow_analyzes_only_selected_retained_papers() -> None:
    """Full-paper processing occurs only after relevance selection."""

    references = (
        _source_reference(
            source_id="2401.11111",
            title="Lower Relevance Paper",
        ),
        _source_reference(
            source_id="2401.22222",
            title="Highest Relevance Paper",
        ),
    )
    papers = tuple(
        _paper_metadata(reference)
        for reference in references
    )
    evaluations = (
        _evaluation(
            papers[0],
            relevance_score=0.2,
        ),
        _evaluation(
            papers[1],
            relevance_score=0.95,
        ),
    )

    selected_paper = papers[1]
    acquisition = _paper_acquisition(
        selected_paper
    )
    document = _paper_document(
        selected_paper
    )

    acquisition_service = StubResearchPaperAcquisitionService(
        {
            references[1].source_id: acquisition,
        }
    )
    ingestion_service = StubResearchPaperIngestionService(
        {
            references[1].source_id: document,
        }
    )
    analysis_service = StubPaperAnalysisService()

    workflow = _create_workflow(
        references=references,
        papers=papers,
        evaluations=evaluations,
        artifacts=(),
        paper_acquisition_service=acquisition_service,
        paper_ingestion_service=ingestion_service,
        paper_analysis_service=analysis_service,
    )[0]

    request = _research_request(
        max_results=1
    )
    result = workflow.execute(
        request
    )

    assert result.papers == (
        selected_paper,
    )
    assert acquisition_service.requests == [
        selected_paper
    ]
    assert ingestion_service.requests == [
        acquisition
    ]
    assert analysis_service.requests[0][2] == (
        selected_paper,
    )
    assert analysis_service.requests[0][3] == (
        document,
    )


def test_unavailable_full_text_uses_metadata_analysis_fallback() -> None:
    """Unavailable full text still permits retained-paper analysis."""

    reference = _source_reference()
    paper = _paper_metadata(reference)
    acquisition = _paper_acquisition(
        paper,
        acquired=False,
    )

    acquisition_service = StubResearchPaperAcquisitionService(
        {
            reference.source_id: acquisition,
        }
    )
    ingestion_service = StubResearchPaperIngestionService(
        {}
    )
    analysis_service = StubPaperAnalysisService()

    workflow = _create_workflow(
        references=(reference,),
        papers=(paper,),
        evaluations=(
            _evaluation(paper),
        ),
        paper_acquisition_service=acquisition_service,
        paper_ingestion_service=ingestion_service,
        paper_analysis_service=analysis_service,
    )[0]

    request = _research_request()
    result = workflow.execute(request)

    assert (
        result.status
        is ResearchStatus.COMPLETED_WITH_WARNINGS
    )
    assert ingestion_service.requests == []
    assert analysis_service.requests == [
        (
            request,
            result.strategy,
            result.papers,
            (),
        )
    ]
    assert result.warnings == (
        "Full text was unavailable for retained paper: "
        "Example Paper.",
    )


def test_full_text_extraction_failure_uses_metadata_fallback() -> None:
    """Unextractable acquired PDF falls back to metadata analysis."""

    reference = _source_reference()
    paper = _paper_metadata(reference)
    acquisition = _paper_acquisition(paper)

    acquisition_service = StubResearchPaperAcquisitionService(
        {
            reference.source_id: acquisition,
        }
    )
    ingestion_service = StubResearchPaperIngestionService(
        {},
        error=ValueError(
            "Research paper PDF contains no meaningful extractable text."
        ),
    )
    analysis_service = StubPaperAnalysisService()

    workflow = _create_workflow(
        references=(reference,),
        papers=(paper,),
        evaluations=(
            _evaluation(paper),
        ),
        paper_acquisition_service=acquisition_service,
        paper_ingestion_service=ingestion_service,
        paper_analysis_service=analysis_service,
    )[0]

    request = _research_request()
    result = workflow.execute(request)

    assert (
        result.status
        is ResearchStatus.COMPLETED_WITH_WARNINGS
    )
    assert analysis_service.requests == [
        (
            request,
            result.strategy,
            result.papers,
            (),
        )
    ]
    assert result.warnings == (
        "Full-text extraction failed for retained paper "
        "'Example Paper': Research paper PDF contains no "
        "meaningful extractable text.",
    )


def test_partial_paper_analysis_configuration_fails_workflow() -> None:
    """Paper analysis services must be configured as one complete set."""

    reference = _source_reference()
    paper = _paper_metadata(reference)

    workflow = _create_workflow(
        references=(reference,),
        papers=(paper,),
        evaluations=(
            _evaluation(paper),
        ),
        paper_acquisition_service=StubResearchPaperAcquisitionService(
            {
                reference.source_id: _paper_acquisition(paper),
            }
        ),
    )[0]

    result = workflow.execute(
        _research_request()
    )

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == (
        "Research paper analysis services are not fully configured."
    )


def test_paper_acquisition_failure_returns_failed_result() -> None:
    """Operational paper acquisition failures stop the workflow."""

    reference = _source_reference()
    paper = _paper_metadata(reference)

    acquisition_service = StubResearchPaperAcquisitionService(
        {},
        error=RuntimeError(
            "Research paper acquisition request failed."
        ),
    )
    ingestion_service = StubResearchPaperIngestionService(
        {}
    )
    analysis_service = StubPaperAnalysisService()

    workflow = _create_workflow(
        references=(reference,),
        papers=(paper,),
        evaluations=(
            _evaluation(paper),
        ),
        paper_acquisition_service=acquisition_service,
        paper_ingestion_service=ingestion_service,
        paper_analysis_service=analysis_service,
    )[0]

    result = workflow.execute(
        _research_request()
    )

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == (
        "Research paper acquisition request failed."
    )
    assert ingestion_service.requests == []
    assert analysis_service.requests == []


def test_paper_analysis_failure_returns_failed_result() -> None:
    """Structured retained-paper analysis failures stop the workflow."""

    reference = _source_reference()
    paper = _paper_metadata(reference)
    acquisition = _paper_acquisition(paper)
    document = _paper_document(paper)

    acquisition_service = StubResearchPaperAcquisitionService(
        {
            reference.source_id: acquisition,
        }
    )
    ingestion_service = StubResearchPaperIngestionService(
        {
            reference.source_id: document,
        }
    )
    analysis_service = StubPaperAnalysisService(
        error=ValueError(
            "Paper analysis failed."
        )
    )

    workflow = _create_workflow(
        references=(reference,),
        papers=(paper,),
        evaluations=(
            _evaluation(paper),
        ),
        paper_acquisition_service=acquisition_service,
        paper_ingestion_service=ingestion_service,
        paper_analysis_service=analysis_service,
    )[0]

    result = workflow.execute(
        _research_request()
    )

    assert result.status is ResearchStatus.FAILED
    assert result.error_message == "Paper analysis failed."


def test_legacy_workflow_skips_unconfigured_paper_analysis() -> None:
    """Existing workflow behavior remains unchanged without Task 6 services."""

    components = _create_workflow()
    result = components[0].execute(
        _research_request()
    )

    assert result.status is ResearchStatus.COMPLETED
    assert result.warnings == ()

