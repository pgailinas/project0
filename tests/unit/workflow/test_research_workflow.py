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
    PaperMetadata,
    ResearchArtifact,
    ResearchArtifactType,
    ResearchEvaluation,
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

    def build_strategy(
        self,
        request: ResearchRequest,
    ) -> ResearchStrategy:
        self.requests.append(request)

        if self._error is not None:
            raise self._error

        return self._strategy


class StubResearchQueryService:
    """Return configured research queries."""

    def __init__(
        self,
        queries: tuple[str, ...] = (),
        error: Exception | None = None,
    ) -> None:
        self._queries = queries
        self._error = error
        self.requests: list[ResearchStrategy] = []

    def generate_queries(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[str, ...]:
        self.requests.append(strategy)

        if self._error is not None:
            raise self._error

        return self._queries


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


def _research_request() -> ResearchRequest:
    """Create a research request for workflow tests."""

    return ResearchRequest(
        question=(
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
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
        constraints=(
            "Focus on vision-language alignment.",
        ),
        source_names=(
            "arxiv",
        ),
        rationale="Search for relevant video representation research.",
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
) -> ResearchEvaluation:
    """Create a research evaluation for workflow tests."""

    return ResearchEvaluation(
        paper=paper,
        relevance_score=0.9,
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
        (
            "self-supervised learning",
            "video representation learning",
        ),
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
