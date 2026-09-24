# ============================================================
# Project0 - Research Workflow
#
# File: research_workflow.py
#
# Purpose:
#     Coordinate research strategy generation, research query
#     generation, external source discovery, paper metadata
#     retrieval, research evaluation, artifact generation, and
#     research workflow reporting.
#
# ============================================================

from __future__ import annotations

from datetime import UTC, datetime
import logging
from threading import Lock

from project0.config.settings import SETTINGS
from project0.interfaces.research_interfaces import (
    ExistingResearchContextAnalysisServiceProtocol,
    PaperAnalysisServiceProtocol,
    PaperMetadataServiceProtocol,
    ResearchArtifactServiceProtocol,
    ResearchContextIngestionServiceProtocol,
    ResearchEvaluationServiceProtocol,
    ResearchQueryServiceProtocol,
    ResearchDirectionAnalysisServiceProtocol,
    ResearchSourceServiceProtocol,
    ResearchStrategyServiceProtocol,
)
from project0.models.research_models import (
    ResearchMechanismMatch,
    ResearchRequest,
    ResearchResult,
    ResearchStatus,
)


logger = logging.getLogger(__name__)


EVIDENCE_CANDIDATE_LIMIT = 8

_RESEARCH_PROGRESS_LOCK = Lock()
_RESEARCH_PROGRESS: dict[str, object] = {
    "stage": "idle",
    "state": "idle",
    "request_id": None,
}


def _set_research_workflow_progress(
    stage: str,
    state: str,
    request_id: str | None,
) -> None:
    """Store the latest live Research workflow stage."""

    with _RESEARCH_PROGRESS_LOCK:
        _RESEARCH_PROGRESS.update(
            {
                "stage": stage,
                "state": state,
                "request_id": request_id,
            }
        )


def get_research_workflow_progress() -> dict[str, object]:
    """Return a thread-safe snapshot of live Research workflow progress."""

    with _RESEARCH_PROGRESS_LOCK:
        return dict(_RESEARCH_PROGRESS)


class ResearchWorkflow:
    """Coordinate the complete Research Agent workflow."""

    def __init__(
        self,
        strategy_service: ResearchStrategyServiceProtocol,
        query_service: ResearchQueryServiceProtocol,
        source_service: ResearchSourceServiceProtocol,
        metadata_service: PaperMetadataServiceProtocol,
        evaluation_service: ResearchEvaluationServiceProtocol,
        artifact_service: ResearchArtifactServiceProtocol,
        context_ingestion_service: (
            ResearchContextIngestionServiceProtocol | None
        ) = None,
        context_analysis_service: (
            ExistingResearchContextAnalysisServiceProtocol | None
        ) = None,
        paper_analysis_service: (
            PaperAnalysisServiceProtocol | None
        ) = None,
        direction_analysis_service: (
            ResearchDirectionAnalysisServiceProtocol | None
        ) = None,
        direction_analysis_enabled: bool = (
            SETTINGS.research_direction_analysis_enabled
        ),
    ) -> None:
        self._strategy_service = strategy_service
        self._query_service = query_service
        self._source_service = source_service
        self._metadata_service = metadata_service
        self._evaluation_service = evaluation_service
        self._artifact_service = artifact_service
        self._context_ingestion_service = context_ingestion_service
        self._context_analysis_service = context_analysis_service
        self._paper_analysis_service = paper_analysis_service
        self._direction_analysis_service = direction_analysis_service
        self._direction_analysis_enabled = direction_analysis_enabled

    def execute(
        self,
        request: ResearchRequest,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> ResearchResult:
        """Execute a Research Agent workflow."""

        created_at = datetime.now(UTC)
        warnings: list[str] = []
        evidence_review_enabled = False
        evidence_shortlist_count = 0
        discovery_only_count = 0
        recommended_evaluations = ()
        preliminary_evaluations = ()

        _set_research_workflow_progress(
            stage="strategy",
            state="running",
            request_id=request.request_id,
        )

        try:
            if (
                (context_source_name is None)
                != (context_content is None)
            ):
                raise ValueError(
                    "Research context source name and content "
                    "must be provided together."
                )

            context = None

            if (
                context_source_name is not None
                and context_content is not None
            ):
                if (
                    self._context_ingestion_service is None
                    or self._context_analysis_service is None
                ):
                    raise RuntimeError(
                        "Research context services are not configured."
                    )

                context_document = (
                    self._context_ingestion_service.ingest(
                        context_source_name,
                        context_content,
                    )
                )
                context = self._context_analysis_service.analyze(
                    context_document,
                    research_question=request.question,
                )

            if context is None:
                strategy = self._strategy_service.build_strategy(
                    request
                )
            else:
                strategy = self._strategy_service.build_strategy(
                    request,
                    context,
                )

            strategy = self._query_service.generate_queries(
                strategy
            )

            _set_research_workflow_progress(
                stage="source",
                state="running",
                request_id=request.request_id,
            )

            source_references = self._source_service.search(
                strategy
            )
            source_search_statistics = getattr(
                self._source_service,
                "last_search_statistics",
                {},
            )

            if not isinstance(source_search_statistics, dict):
                source_search_statistics = {}

            if source_search_statistics:
                logger.info(
                    "Research workflow source selection for request %s: %s",
                    request.request_id,
                    source_search_statistics,
                )

            if not source_references:
                warnings.append(
                    "No candidate research sources were found."
                )

            _set_research_workflow_progress(
                stage="metadata",
                state="running",
                request_id=request.request_id,
            )

            papers = self._metadata_service.retrieve_metadata(
                source_references
            )

            if len(papers) < len(source_references):
                warnings.append(
                    "Metadata could not be retrieved for one or more "
                    "research source references."
                )

            acquire_evidence = getattr(
                self._metadata_service,
                "acquire_evidence",
                None,
            )

            if callable(acquire_evidence):
                evidence_review_enabled = True
                evidence_candidates = papers

                if len(papers) > EVIDENCE_CANDIDATE_LIMIT:
                    rank_candidates = getattr(
                        self._evaluation_service,
                        "rank_candidates",
                        self._evaluation_service.evaluate,
                    )
                    preliminary_evaluations = (
                        rank_candidates(
                            request,
                            strategy,
                            papers,
                        )
                    )
                    evidence_candidates = (
                        self._select_evidence_candidates(
                            preliminary_evaluations,
                            EVIDENCE_CANDIDATE_LIMIT,
                            strategy,
                        )
                    )
                    logger.info(
                        "Research workflow evidence shortlist for request "
                        "%s: candidates=%d selected=%d",
                        request.request_id,
                        len(papers),
                        len(evidence_candidates),
                    )

                papers = acquire_evidence(
                    evidence_candidates[:EVIDENCE_CANDIDATE_LIMIT]
                )
                evidence_shortlist_count = len(papers)
                discovery_only_count = sum(
                    not paper.evidence_sections
                    for paper in papers
                )
                if discovery_only_count:
                    warnings.append(
                        f"{discovery_only_count} shortlisted paper(s) "
                        "were retained as discovery-only because usable "
                        "paper evidence was unavailable."
                    )

            _set_research_workflow_progress(
                stage="evaluation",
                state="running",
                request_id=request.request_id,
            )

            evaluate_final = getattr(
                self._evaluation_service,
                "evaluate_final",
                None,
            )
            if callable(evaluate_final):
                evaluations = evaluate_final(
                    request,
                    strategy,
                    papers,
                    preliminary_evaluations,
                )
            else:
                evaluations = self._evaluation_service.evaluate(
                    request,
                    strategy,
                    papers,
                )

            (
                source_references,
                papers,
                evaluations,
            ) = (
                self._select_evidence_results(
                    source_references=source_references,
                    evaluations=evaluations,
                    max_results=request.max_results,
                )
                if evidence_review_enabled
                else self._select_results(
                    source_references=source_references,
                    papers=papers,
                    evaluations=evaluations,
                    max_results=request.max_results,
                )
            )

            recommended_evaluations = tuple(
                evaluation
                for evaluation in evaluations
                if evaluation.is_recommended
            )

            if source_references and not evaluations:
                warnings.append(
                    "No research papers met the minimum relevance threshold."
                )
            elif (
                evidence_review_enabled
                and evaluations
                and not recommended_evaluations
            ):
                warnings.append(
                    "No evidence-reviewed papers met the recommendation "
                    f"threshold; displaying {len(evaluations)} reviewed "
                    "paper(s)."
                )

            paper_analyses = ()

            if (
                self._paper_analysis_service is not None
                and papers
            ):
                paper_analyses = self._paper_analysis_service.analyze(
                    request,
                    strategy,
                    papers,
                )

            direction_analysis = None

            if (
                self._direction_analysis_enabled
                and self._direction_analysis_service is not None
            ):
                if self._paper_analysis_service is None:
                    raise RuntimeError(
                        "Research direction analysis requires paper "
                        "analysis service."
                    )

                direction_paper_analyses = paper_analyses

                if len(direction_paper_analyses) >= 2:
                    try:
                        direction_analysis = (
                            self._direction_analysis_service.analyze(
                                request,
                                context,
                                direction_paper_analyses,
                            )
                        )
                    except (
                        OSError,
                        RuntimeError,
                        TypeError,
                        ValueError,
                    ) as error:
                        logger.warning(
                            "Research direction analysis failed for request %s: %s",
                            request.request_id,
                            error,
                        )
                        warnings.append(
                            "Research direction analysis could not be completed: "
                            f"{self._format_error_message(error)}"
                        )

            _set_research_workflow_progress(
                stage="artifacts",
                state="running",
                request_id=request.request_id,
            )

            artifacts = self._artifact_service.generate_artifacts(
                request,
                evaluations,
            )

            status = (
                ResearchStatus.COMPLETED_WITH_WARNINGS
                if warnings
                else ResearchStatus.COMPLETED
            )

            _set_research_workflow_progress(
                stage="complete",
                state=status.value,
                request_id=request.request_id,
            )

            return ResearchResult(
                request_id=request.request_id,
                status=status,
                summary=self._build_summary(
                    source_count=len(source_references),
                    paper_count=len(papers),
                    evaluation_count=len(evaluations),
                    artifact_count=len(artifacts),
                ),
                strategy=strategy,
                source_references=source_references,
                papers=papers,
                evaluations=evaluations,
                artifacts=artifacts,
                created_at=created_at,
                existing_research_context=context,
                paper_analyses=paper_analyses,
                direction_analysis=direction_analysis,
                warnings=tuple(warnings),
                metadata={
                    **(
                        {
                            "source_search": dict(
                                source_search_statistics
                            ),
                        }
                        if source_search_statistics
                        else {}
                    ),
                    **(
                        {
                            "evidence_review": {
                                "shortlisted_count": (
                                    evidence_shortlist_count
                                ),
                                "reviewed_count": len(evaluations),
                                "recommended_count": len(
                                    recommended_evaluations
                                ),
                                "discovery_only_count": (
                                    discovery_only_count
                                ),
                            },
                        }
                        if evidence_review_enabled
                        else {}
                    ),
                },
            )

        except (OSError, RuntimeError, TypeError, ValueError) as error:
            logger.exception(
                "Research workflow failed for request %s.",
                request.request_id,
            )

            _set_research_workflow_progress(
                stage="failed",
                state="failed",
                request_id=request.request_id,
            )

            return self._failed_result(
                request=request,
                created_at=created_at,
                error_message=self._format_error_message(error),
                warnings=tuple(warnings),
            )

    @staticmethod
    def _select_evidence_candidates(
        evaluations: tuple,
        limit: int,
        strategy: object,
    ) -> tuple:
        """Select a bounded evidence shortlist by preliminary relevance."""

        ranked = sorted(
            evaluations,
            key=lambda evaluation: (
                ResearchWorkflow._evidence_evaluation_tier(
                    evaluation,
                    strategy,
                ),
                -(
                    evaluation.relevance_score
                    if evaluation.relevance_score is not None
                    else float("inf")
                ),
            ),
        )

        eligible = tuple(
            evaluation.paper
            for evaluation in ranked
            if (
                evaluation.mechanism_match
                in {
                    ResearchMechanismMatch.DIRECT,
                    ResearchMechanismMatch.TRANSFERABLE,
                }
                or ResearchWorkflow._evidence_candidate_tier(
                    evaluation.paper,
                    strategy,
                ) < 2
            )
        )

        return eligible[:limit]

    @staticmethod
    def _evidence_evaluation_tier(
        evaluation: object,
        strategy: object,
    ) -> int:
        """Prioritize validated mechanism matches over lexical heuristics."""

        mechanism_match = getattr(
            evaluation,
            "mechanism_match",
            None,
        )

        if mechanism_match is ResearchMechanismMatch.DIRECT:
            return 0
        if mechanism_match is ResearchMechanismMatch.TRANSFERABLE:
            return 1

        return 2 + ResearchWorkflow._evidence_candidate_tier(
            evaluation.paper,
            strategy,
        )

    @staticmethod
    def _evidence_candidate_tier(
        paper: object,
        strategy: object,
    ) -> int:
        """Classify direct and transferable alignment evidence candidates."""

        title = str(getattr(paper, "title", "")).casefold()
        abstract = str(getattr(paper, "abstract", "") or "").casefold()
        text = f"{title} {abstract}"
        direct_video = "video" in text or "videoqa" in text
        language = any(
            term in text
            for term in ("caption", "clip", "language", "text")
        )
        representation = any(
            term in text
            for term in (
                "autoencoder",
                "embedding",
                "latent",
                "representation",
            )
        )
        transfer_mechanism = any(
            term in text
            for term in (
                "align",
                "contrastive",
                "distill",
                "mapping",
                "projection",
            )
        )
        visual = any(
            term in text
            for term in ("clip", "vision", "visual", "image")
        )
        excluded_transfer_task = any(
            term in text
            for term in (
                "audio",
                "debiasing",
                "diffusion",
                "forecasting",
                "generation",
                "generative",
            )
        )
        synthesis_candidate = any(
            term in text
            for term in (
                "diffusion",
                "generation",
                "generative",
                "synthesis",
            )
        )

        if (
            ResearchWorkflow._strategy_prioritizes_representation_learning(
                strategy
            )
            and synthesis_candidate
        ):
            return 2

        if (
            direct_video
            and language
            and representation
            and transfer_mechanism
        ):
            return 0
        if (
            visual
            and language
            and representation
            and transfer_mechanism
            and not excluded_transfer_task
        ):
            return 1
        return 2

    @staticmethod
    def _strategy_prioritizes_representation_learning(
        strategy: object,
    ) -> bool:
        """Return whether the strategy targets representations, not synthesis."""

        values = (
            *getattr(strategy, "concepts", ()),
            *getattr(strategy, "search_terms", ()),
            *getattr(strategy, "constraints", ()),
        )
        text = " ".join(str(value).casefold() for value in values)
        representation = any(
            term in text
            for term in (
                "autoencoder",
                "embedding",
                "encoder",
                "latent",
                "representation",
            )
        )
        synthesis = any(
            term in text
            for term in (
                "diffusion",
                "generation",
                "generative",
                "synthesis",
            )
        )

        return representation and not synthesis

    @staticmethod
    def _select_results(
        source_references: tuple,
        papers: tuple,
        evaluations: tuple,
        max_results: int,
    ) -> tuple[tuple, tuple, tuple]:
        """Select final research results by descending relevance."""

        if not evaluations:
            return source_references, papers, evaluations

        ranked_evaluations = tuple(
            sorted(
                evaluations,
                key=lambda evaluation: (
                    evaluation.relevance_score
                    if evaluation.relevance_score is not None
                    else float("-inf")
                ),
                reverse=True,
            )
        )

        selected_evaluations = tuple(
            evaluation
            for evaluation in ranked_evaluations
            if (
                evaluation.relevance_score is not None
                and evaluation.relevance_score >= 0.75
            )
        )[
            :max(1, max_results)
        ]
        selected_papers = tuple(
            evaluation.paper
            for evaluation in selected_evaluations
        )

        return (
            source_references,
            selected_papers,
            selected_evaluations,
        )

    @staticmethod
    def _select_evidence_results(
        source_references: tuple,
        evaluations: tuple,
        max_results: int,
    ) -> tuple[tuple, tuple, tuple]:
        """Select scored, evidence-reviewed papers in relevance order."""

        ranked_evaluations = tuple(
            sorted(
                (
                    evaluation
                    for evaluation in evaluations
                    if (
                        evaluation.paper.evidence_sections
                        and evaluation.relevance_score is not None
                    )
                ),
                key=lambda evaluation: (
                    evaluation.relevance_score
                    if evaluation.relevance_score is not None
                    else float("-inf")
                ),
                reverse=True,
            )
        )[:max(1, max_results)]

        return (
            source_references,
            tuple(
                evaluation.paper
                for evaluation in ranked_evaluations
            ),
            ranked_evaluations,
        )

    @staticmethod
    def _build_summary(
        source_count: int,
        paper_count: int,
        evaluation_count: int,
        artifact_count: int,
    ) -> str:
        """Build a summary for a completed research workflow."""

        return (
            "Research workflow completed with "
            f"{source_count} source reference(s), "
            f"{paper_count} paper metadata record(s), "
            f"{evaluation_count} evaluation(s), and "
            f"{artifact_count} artifact(s)."
        )

    @staticmethod
    def _format_error_message(
        error: Exception,
    ) -> str:
        """Convert internal exceptions into user-facing messages."""

        message = str(error)

        if "HTTP status 429" in message:
            return (
                "The configured research source is temporarily "
                "unavailable due to rate limiting. "
                "Please retry later."
            )

        return message

    @staticmethod
    def _failed_result(
        request: ResearchRequest,
        created_at: datetime,
        error_message: str,
        warnings: tuple[str, ...] = (),
    ) -> ResearchResult:
        """Return a failed research workflow result."""

        return ResearchResult(
            request_id=request.request_id,
            status=ResearchStatus.FAILED,
            summary="Research workflow failed.",
            strategy=None,
            source_references=(),
            papers=(),
            evaluations=(),
            artifacts=(),
            created_at=created_at,
            warnings=warnings,
            error_message=error_message,
        )
