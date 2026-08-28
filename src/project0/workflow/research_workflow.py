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

from project0.interfaces.research_interfaces import (
    ExistingResearchContextAnalysisServiceProtocol,
    PaperMetadataServiceProtocol,
    ResearchArtifactServiceProtocol,
    ResearchContextIngestionServiceProtocol,
    ResearchEvaluationServiceProtocol,
    ResearchQueryServiceProtocol,
    ResearchSourceServiceProtocol,
    ResearchStrategyServiceProtocol,
)
from project0.models.research_models import (
    ResearchRequest,
    ResearchResult,
    ResearchStatus,
)


logger = logging.getLogger(__name__)


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
    ) -> None:
        self._strategy_service = strategy_service
        self._query_service = query_service
        self._source_service = source_service
        self._metadata_service = metadata_service
        self._evaluation_service = evaluation_service
        self._artifact_service = artifact_service
        self._context_ingestion_service = context_ingestion_service
        self._context_analysis_service = context_analysis_service

    def execute(
        self,
        request: ResearchRequest,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> ResearchResult:
        """Execute a Research Agent workflow."""

        created_at = datetime.now(UTC)
        warnings: list[str] = []

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
                    context_document
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

            source_references = self._source_service.search(
                strategy
            )

            if not source_references:
                warnings.append(
                    "No candidate research sources were found."
                )

            papers = self._metadata_service.retrieve_metadata(
                source_references
            )

            if len(papers) < len(source_references):
                warnings.append(
                    "Metadata could not be retrieved for one or more "
                    "research source references."
                )

            evaluations = self._evaluation_service.evaluate(
                request,
                strategy,
                papers,
            )

            (
                source_references,
                papers,
                evaluations,
            ) = self._select_results(
                source_references=source_references,
                papers=papers,
                evaluations=evaluations,
                max_results=request.max_results,
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
                warnings=tuple(warnings),
            )

        except (OSError, RuntimeError, TypeError, ValueError) as error:
            logger.exception(
                "Research workflow failed for request %s.",
                request.request_id,
            )

            return self._failed_result(
                request=request,
                created_at=created_at,
                error_message=self._format_error_message(error),
                warnings=tuple(warnings),
            )

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

        selected_evaluations = ranked_evaluations[
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
