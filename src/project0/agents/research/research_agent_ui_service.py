# ============================================================
# Project0 - Research Agent UI Service
#
# File: research_agent_ui_service.py
#
# Purpose:
#     Adapt Research Agent workflow results into browser-facing
#     view models used by the Dashboard interface.
#
# ============================================================

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Protocol, Sequence

from project0.agents.research.research_agent_view_models import (
    PaperMetadataView,
    ResearchAgentPageStatus,
    ResearchAgentPageView,
    ResearchArtifactView,
    ResearchEvaluationView,
    ResearchRequestForm,
    ResearchSourceView,
    ResearchWorkflowSummaryView,
)
from project0.models.research_models import (
    ResearchArtifactType,
    ResearchStatus,
)


logger = logging.getLogger(__name__)


class ResearchWorkflowPort(Protocol):
    """Minimal research workflow interface required by the UI."""

    def run_research_workflow(
        self,
        question: str,
        constraints: tuple[str, ...] = (),
        focus_areas: tuple[str, ...] = (),
        source_names: tuple[str, ...] = (),
    ) -> object:
        """Execute a research workflow and return its result."""


@dataclass(frozen=True, slots=True)
class ResearchAgentUIService:
    """Coordinate Research Agent UI requests and presentation state."""

    workflow: ResearchWorkflowPort

    def create_ready_page(self) -> ResearchAgentPageView:
        """Create the initial Research Agent page state."""

        return ResearchAgentPageView(
            page_status=ResearchAgentPageStatus.READY,
            status_message="Ready for a research request.",
            request_form=ResearchRequestForm(),
        )

    def submit_request(
        self,
        question: str,
        constraints: Sequence[str] | None = None,
        focus_areas: Sequence[str] | None = None,
        source_names: Sequence[str] | None = None,
    ) -> ResearchAgentPageView:
        """Submit a research request and return display-ready state."""

        request_form = self._build_request_form(
            question=question,
            constraints=constraints,
            focus_areas=focus_areas,
            source_names=source_names,
        )

        if not request_form.question:
            return ResearchAgentPageView(
                page_status=ResearchAgentPageStatus.FAILED,
                status_message="A research question is required.",
                request_form=request_form,
                error_message=(
                    "Enter a research question before continuing."
                ),
            )

        try:
            workflow_result = self.workflow.run_research_workflow(
                question=request_form.question,
                constraints=request_form.constraints,
                focus_areas=request_form.focus_areas,
                source_names=request_form.source_names,
            )
        except Exception as exc:
            return self._create_failure_page(
                request_form=request_form,
                message="The research workflow could not be completed.",
                error_message=str(exc),
            )

        return self._map_workflow_result(
            workflow_result=workflow_result,
            request_form=request_form,
        )

    def _build_request_form(
        self,
        question: str,
        constraints: Sequence[str] | None,
        focus_areas: Sequence[str] | None,
        source_names: Sequence[str] | None,
    ) -> ResearchRequestForm:
        """Normalize browser form values."""

        normalized_question = question.strip()
        normalized_constraints = tuple(
            value.strip()
            for value in (constraints or ())
            if value is not None and value.strip()
        )
        normalized_focus_areas = tuple(
            value.strip()
            for value in (focus_areas or ())
            if value is not None and value.strip()
        )
        normalized_source_names = tuple(
            value.strip()
            for value in (source_names or ())
            if value is not None and value.strip()
        )

        return ResearchRequestForm(
            question=normalized_question,
            constraints=normalized_constraints,
            focus_areas=normalized_focus_areas,
            source_names=normalized_source_names,
        )

    def _map_workflow_result(
        self,
        workflow_result: object,
        request_form: ResearchRequestForm,
    ) -> ResearchAgentPageView:
        """Convert a workflow result into a complete page view."""

        request_id = self._normalize_optional_text(
            self._read_value(
                workflow_result,
                "request_id",
                default=None,
            )
        )

        workflow_status = self._map_workflow_status(
            self._read_value(
                workflow_result,
                "status",
                default=None,
            )
        )

        sources = self._map_sources(
            self._read_value(
                workflow_result,
                "source_references",
                default=(),
            )
        )

        papers = self._map_papers(
            self._read_value(
                workflow_result,
                "papers",
                default=(),
            )
        )

        evaluations = self._map_evaluations(
            self._read_value(
                workflow_result,
                "evaluations",
                default=(),
            )
        )

        artifacts = self._map_artifacts(
            self._read_value(
                workflow_result,
                "artifacts",
                default=(),
            )
        )

        warnings = tuple(
            str(item)
            for item in self._read_value(
                workflow_result,
                "warnings",
                default=(),
            )
        )

        error_message = self._normalize_optional_text(
            self._read_value(
                workflow_result,
                "error_message",
                default=None,
            )
        )

        page_status = self._determine_page_status(
            workflow_status=workflow_status,
            warnings=warnings,
            error_message=error_message,
        )

        return ResearchAgentPageView(
            page_status=page_status,
            status_message=self._status_message(page_status),
            request_form=request_form,
            request_id=request_id,
            workflow_status=workflow_status,
            sources=sources,
            papers=papers,
            evaluations=evaluations,
            artifacts=artifacts,
            workflow_summary=ResearchWorkflowSummaryView(
                source_count=len(sources),
                paper_count=len(papers),
                evaluation_count=len(evaluations),
                artifact_count=len(artifacts),
            ),
            warnings=warnings,
            error_message=error_message,
        )

    def _map_sources(
        self,
        source_references: object,
    ) -> tuple[ResearchSourceView, ...]:
        """Map research sources into browser presentation state."""

        if not source_references:
            return ()

        return tuple(
            ResearchSourceView(
                source_name=str(
                    self._read_value(
                        reference,
                        "source_name",
                        default="",
                    )
                ),
                source_id=str(
                    self._read_value(
                        reference,
                        "source_id",
                        default="",
                    )
                ),
                title=str(
                    self._read_value(
                        reference,
                        "title",
                        default="",
                    )
                ),
                source_url=self._normalize_optional_text(
                    self._read_value(
                        reference,
                        "source_url",
                        default=None,
                    )
                ),
                authors=tuple(
                    str(author)
                    for author in self._read_value(
                        reference,
                        "authors",
                        default=(),
                    )
                ),
                publication_year=self._read_value(
                    reference,
                    "publication_year",
                    default=None,
                ),
            )
            for reference in source_references
        )

    def _map_papers(
        self,
        papers: object,
    ) -> tuple[PaperMetadataView, ...]:
        """Map paper metadata into browser presentation state."""

        if not papers:
            return ()

        return tuple(
            PaperMetadataView(
                source_id=str(
                    self._read_value(
                        self._read_value(
                            paper,
                            "source_reference",
                            default={},
                        ),
                        "source_id",
                        default="",
                    )
                ),
                title=str(
                    self._read_value(
                        paper,
                        "title",
                        default="",
                    )
                ),
                authors=tuple(
                    str(author)
                    for author in self._read_value(
                        paper,
                        "authors",
                        default=(),
                    )
                ),
                publication_year=self._read_value(
                    paper,
                    "publication_year",
                    default=None,
                ),
                abstract=self._normalize_optional_text(
                    self._read_value(
                        paper,
                        "abstract",
                        default=None,
                    )
                ),
                venue=self._normalize_optional_text(
                    self._read_value(
                        paper,
                        "venue",
                        default=None,
                    )
                ),
                doi=self._normalize_optional_text(
                    self._read_value(
                        paper,
                        "doi",
                        default=None,
                    )
                ),
                source_url=self._normalize_optional_text(
                    self._read_value(
                        paper,
                        "source_url",
                        default=None,
                    )
                ),
            )
            for paper in papers
        )

    def _map_evaluations(
        self,
        evaluations: object,
    ) -> tuple[ResearchEvaluationView, ...]:
        """Map research evaluations into browser presentation state."""

        if not evaluations:
            return ()

        return tuple(
            ResearchEvaluationView(
                source_id=str(
                    self._read_value(
                        self._read_value(
                            self._read_value(
                                evaluation,
                                "paper",
                                default={},
                            ),
                            "source_reference",
                            default={},
                        ),
                        "source_id",
                        default="",
                    )
                ),
                title=str(
                    self._read_value(
                        self._read_value(
                            evaluation,
                            "paper",
                            default={},
                        ),
                        "title",
                        default="",
                    )
                ),
                relevance_score=self._read_value(
                    evaluation,
                    "relevance_score",
                    default=None,
                ),
                relevance_summary=str(
                    self._read_value(
                        evaluation,
                        "relevance_summary",
                        default="",
                    )
                ),
                strengths=tuple(
                    str(item)
                    for item in self._read_value(
                        evaluation,
                        "strengths",
                        default=(),
                    )
                ),
                limitations=tuple(
                    str(item)
                    for item in self._read_value(
                        evaluation,
                        "limitations",
                        default=(),
                    )
                ),
                research_connections=tuple(
                    str(item)
                    for item in self._read_value(
                        evaluation,
                        "research_connections",
                        default=(),
                    )
                ),
                warnings=tuple(
                    str(item)
                    for item in self._read_value(
                        evaluation,
                        "warnings",
                        default=(),
                    )
                ),
            )
            for evaluation in evaluations
        )

    def _map_artifacts(
        self,
        artifacts: object,
    ) -> tuple[ResearchArtifactView, ...]:
        """Map research artifacts into browser presentation state."""

        if not artifacts:
            return ()

        return tuple(
            ResearchArtifactView(
                artifact_id=str(
                    self._read_value(
                        artifact,
                        "artifact_id",
                        default="",
                    )
                ),
                artifact_type=self._map_artifact_type(
                    self._read_value(
                        artifact,
                        "artifact_type",
                        default=ResearchArtifactType.PAPER_SUMMARY,
                    )
                ),
                title=str(
                    self._read_value(
                        artifact,
                        "title",
                        default="",
                    )
                ),
                content=str(
                    self._read_value(
                        artifact,
                        "content",
                        default="",
                    )
                ),
                source_ids=tuple(
                    str(
                        self._read_value(
                            source,
                            "source_id",
                            default="",
                        )
                    )
                    for source in self._read_value(
                        artifact,
                        "source_references",
                        default=(),
                    )
                ),
            )
            for artifact in artifacts
        )

    def _determine_page_status(
        self,
        workflow_status: ResearchStatus | None,
        warnings: tuple[str, ...],
        error_message: str | None,
    ) -> ResearchAgentPageStatus:
        """Determine the page status from a workflow result."""

        if error_message:
            return ResearchAgentPageStatus.FAILED

        if workflow_status is ResearchStatus.FAILED:
            return ResearchAgentPageStatus.FAILED

        if (
            workflow_status
            is ResearchStatus.COMPLETED_WITH_WARNINGS
        ):
            return ResearchAgentPageStatus.COMPLETED_WITH_WARNINGS

        if workflow_status is ResearchStatus.COMPLETED:
            return ResearchAgentPageStatus.COMPLETED

        if warnings:
            return ResearchAgentPageStatus.COMPLETED_WITH_WARNINGS

        return ResearchAgentPageStatus.PROCESSING

    @staticmethod
    def _map_workflow_status(
        value: object | None,
    ) -> ResearchStatus | None:
        """Convert an optional workflow status value."""

        if value is None or isinstance(value, ResearchStatus):
            return value

        try:
            return ResearchStatus(str(value))
        except ValueError:
            return None

    @staticmethod
    def _map_artifact_type(
        value: object,
    ) -> ResearchArtifactType:
        """Convert a research artifact type value."""

        if isinstance(value, ResearchArtifactType):
            return value

        try:
            return ResearchArtifactType(str(value))
        except ValueError:
            return ResearchArtifactType.PAPER_SUMMARY

    @staticmethod
    def _status_message(
        status: ResearchAgentPageStatus,
    ) -> str:
        """Return the default display message for a page status."""

        messages = {
            ResearchAgentPageStatus.READY: (
                "Ready for a research request."
            ),
            ResearchAgentPageStatus.PROCESSING: (
                "The research workflow is processing."
            ),
            ResearchAgentPageStatus.COMPLETED: (
                "The research workflow completed successfully."
            ),
            ResearchAgentPageStatus.COMPLETED_WITH_WARNINGS: (
                "The research workflow completed with warnings."
            ),
            ResearchAgentPageStatus.FAILED: (
                "The research workflow failed."
            ),
        }
        return messages[status]

    def _create_failure_page(
        self,
        request_form: ResearchRequestForm,
        message: str,
        error_message: str,
    ) -> ResearchAgentPageView:
        """Create a consistent failure page."""

        return ResearchAgentPageView(
            page_status=ResearchAgentPageStatus.FAILED,
            status_message=message,
            request_form=request_form,
            error_message=error_message,
        )

    @staticmethod
    def _normalize_optional_text(value: object | None) -> str | None:
        """Normalize an optional value to stripped text."""

        if value is None:
            return None

        text = str(value).strip()
        return text or None

    @staticmethod
    def _read_value(
        source: object,
        name: str,
        default: object = None,
    ) -> object:
        """Read a value from either an object attribute or a mapping."""

        if isinstance(source, dict):
            return source.get(name, default)

        return getattr(source, name, default)
