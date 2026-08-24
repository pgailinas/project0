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
    PaperMetadataServiceProtocol,
    ResearchArtifactServiceProtocol,
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
    ) -> None:
        self._strategy_service = strategy_service
        self._query_service = query_service
        self._source_service = source_service
        self._metadata_service = metadata_service
        self._evaluation_service = evaluation_service
        self._artifact_service = artifact_service

    def execute(
        self,
        request: ResearchRequest,
    ) -> ResearchResult:
        """Execute a Research Agent workflow."""

        created_at = datetime.now(UTC)
        warnings: list[str] = []

        try:
            strategy = self._strategy_service.build_strategy(
                request
            )

            self._query_service.generate_queries(
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
