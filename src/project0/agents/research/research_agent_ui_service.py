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
    ExistingResearchContextView,
    PaperAnalysisView,
    ResearchAgentPageStatus,
    ResearchAgentPageView,
    ResearchArtifactView,
    ResearchDirectionAnalysisView,
    ResearchDirectionView,
    ResearchEvidenceReferenceView,
    ResearchFindingView,
    ResearchRequestForm,
    ResearchResultView,
    ResearchSynthesisView,
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
        guidance: str = "",
        max_results: int = 10,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
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
        guidance: str | None = None,
        max_results: int = 10,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> ResearchAgentPageView:
        """Submit a research request and return display-ready state."""

        request_form = self._build_request_form(
            question=question,
            guidance=guidance,
            max_results=max_results,
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
            if (
                context_source_name is None
                and context_content is None
            ):
                workflow_result = self.workflow.run_research_workflow(
                    question=request_form.question,
                    guidance=request_form.guidance,
                    max_results=request_form.max_results,
                )
            else:
                workflow_result = self.workflow.run_research_workflow(
                    question=request_form.question,
                    guidance=request_form.guidance,
                    max_results=request_form.max_results,
                    context_source_name=context_source_name,
                    context_content=context_content,
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
        guidance: str | None,
        max_results: int,
    ) -> ResearchRequestForm:
        """Normalize browser form values."""

        return ResearchRequestForm(
            question=question.strip(),
            guidance=(guidance or "").strip(),
            max_results=max_results,
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

        source_references = self._read_value(
            workflow_result,
            "source_references",
            default=(),
        )

        papers = self._read_value(
            workflow_result,
            "papers",
            default=(),
        )

        evaluations = self._read_value(
            workflow_result,
            "evaluations",
            default=(),
        )

        workflow_artifacts = self._read_value(
            workflow_result,
            "artifacts",
            default=(),
        )

        results = self._map_results(
            source_references,
            papers,
            evaluations,
            workflow_artifacts,
        )

        artifacts = self._map_artifacts(
            workflow_artifacts,
            include_paper_summaries=False,
        )

        existing_research_context = self._map_existing_research_context(
            self._read_value(
                workflow_result,
                "existing_research_context",
                default=None,
            )
        )

        paper_analyses = self._map_paper_analyses(
            self._read_value(
                workflow_result,
                "paper_analyses",
                default=(),
            )
        )

        direction_analysis = self._map_direction_analysis(
            self._read_value(
                workflow_result,
                "direction_analysis",
                default=None,
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
            results=results,
            artifacts=artifacts,
            existing_research_context=existing_research_context,
            paper_analyses=paper_analyses,
            direction_analysis=direction_analysis,
            workflow_summary=ResearchWorkflowSummaryView(
                source_count=len(source_references),
                paper_count=len(papers),
                evaluation_count=len(evaluations),
                artifact_count=len(workflow_artifacts),
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

    def _map_results(
        self,
        sources: object,
        papers: object,
        evaluations: object,
        artifacts: object,
    ) -> tuple[ResearchResultView, ...]:
        """Combine source, metadata, and evaluation data."""

        source_items = tuple(sources or ())
        paper_items = tuple(papers or ())
        evaluation_items = tuple(evaluations or ())
        artifact_items = tuple(artifacts or ())

        results = []

        for index, paper in enumerate(paper_items, start=1):
            source_id = str(
                self._read_value(
                    self._read_value(
                        paper,
                        "source_reference",
                        default={},
                    ),
                    "source_id",
                    default="",
                )
            )

            evaluation = next(
                (
                    item
                    for item in evaluation_items
                    if str(
                        self._read_value(
                            self._read_value(
                                self._read_value(
                                    item,
                                    "paper",
                                    default={},
                                ),
                                "source_reference",
                                default={},
                            ),
                            "source_id",
                            default="",
                        )
                    )
                    == source_id
                ),
                {},
            )

            source = next(
                (
                    item
                    for item in source_items
                    if str(
                        self._read_value(
                            item,
                            "source_id",
                            default="",
                        )
                    )
                    == source_id
                ),
                {},
            )

            artifact = next(
                (
                    item
                    for item in artifact_items
                    if self._map_artifact_type(
                        self._read_value(
                            item,
                            "artifact_type",
                            default=ResearchArtifactType.PAPER_SUMMARY,
                        )
                    )
                    is ResearchArtifactType.PAPER_SUMMARY
                    and source_id
                    in tuple(
                        str(
                            self._read_value(
                                reference,
                                "source_id",
                                default="",
                            )
                        )
                        for reference in self._read_value(
                            item,
                            "source_references",
                            default=(),
                        )
                    )
                ),
                {},
            )

            results.append(
                ResearchResultView(
                    rank=index,
                    source_id=source_id,
                    title=str(
                        self._read_value(
                            paper,
                            "title",
                            default="",
                        )
                    ),
                    publication_year=self._read_value(
                        paper,
                        "publication_year",
                        default=None,
                    ),
                    source_name=self._normalize_optional_text(
                        self._read_value(
                            source,
                            "source_name",
                            default=None,
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
                    authors=tuple(
                        str(author)
                        for author in self._read_value(
                            paper,
                            "authors",
                            default=(),
                        )
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
                    source_url=(
                        self._normalize_optional_text(
                            self._read_value(
                                paper,
                                "source_url",
                                default=None,
                            )
                        )
                        or self._normalize_optional_text(
                            self._read_value(
                                source,
                                "source_url",
                                default=None,
                            )
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
                    artifact_title=self._normalize_optional_text(
                        self._read_value(
                            artifact,
                            "title",
                            default=None,
                        )
                    ),
                    artifact_content=self._normalize_optional_text(
                        self._read_value(
                            artifact,
                            "content",
                            default=None,
                        )
                    ),
                )
            )

        return tuple(results)

    def _map_artifacts(
        self,
        artifacts: object,
        include_paper_summaries: bool = True,
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
            if (
                include_paper_summaries
                or str(
                    self._read_value(
                        artifact,
                        "artifact_type",
                        default="",
                    )
                )
                != ResearchArtifactType.PAPER_SUMMARY.value
            )
        )

    def _map_existing_research_context(
        self,
        context: object | None,
    ) -> ExistingResearchContextView | None:
        """Map existing research context into presentation state."""

        if context is None:
            return None

        research_problem = self._read_value(
            context,
            "research_problem",
            default=None,
        )

        return ExistingResearchContextView(
            research_problem=(
                self._map_findings((research_problem,))[0]
                if research_problem is not None
                else None
            ),
            prior_work=self._map_findings(
                self._read_value(
                    context,
                    "prior_work",
                    default=(),
                )
            ),
            implemented_approaches=self._map_findings(
                self._read_value(
                    context,
                    "implemented_approaches",
                    default=(),
                )
            ),
            findings=self._map_findings(
                self._read_value(
                    context,
                    "findings",
                    default=(),
                )
            ),
            limitations=self._map_findings(
                self._read_value(
                    context,
                    "limitations",
                    default=(),
                )
            ),
            unresolved_questions=self._map_findings(
                self._read_value(
                    context,
                    "unresolved_questions",
                    default=(),
                )
            ),
            stated_future_work=self._map_findings(
                self._read_value(
                    context,
                    "stated_future_work",
                    default=(),
                )
            ),
        )

    def _map_paper_analyses(
        self,
        paper_analyses: object,
    ) -> tuple[PaperAnalysisView, ...]:
        """Map retained-paper analyses into presentation state."""

        return tuple(
            PaperAnalysisView(
                source_id=str(
                    self._read_value(
                        self._read_value(
                            self._read_value(
                                analysis,
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
                            analysis,
                            "paper",
                            default={},
                        ),
                        "title",
                        default="",
                    )
                ),
                analysis_basis=str(
                    self._read_value(
                        analysis,
                        "analysis_basis",
                        default="",
                    )
                ),
                problem=self._map_required_finding(
                    self._read_value(
                        analysis,
                        "problem",
                        default={},
                    )
                ),
                approach=self._map_required_finding(
                    self._read_value(
                        analysis,
                        "approach",
                        default={},
                    )
                ),
                representations=self._map_findings(
                    self._read_value(
                        analysis,
                        "representations",
                        default=(),
                    )
                ),
                modalities=self._map_findings(
                    self._read_value(
                        analysis,
                        "modalities",
                        default=(),
                    )
                ),
                learning_objectives=self._map_findings(
                    self._read_value(
                        analysis,
                        "learning_objectives",
                        default=(),
                    )
                ),
                datasets_tasks=self._map_findings(
                    self._read_value(
                        analysis,
                        "datasets_tasks",
                        default=(),
                    )
                ),
                findings=self._map_findings(
                    self._read_value(
                        analysis,
                        "findings",
                        default=(),
                    )
                ),
                limitations=self._map_findings(
                    self._read_value(
                        analysis,
                        "limitations",
                        default=(),
                    )
                ),
                warnings=tuple(
                    str(item)
                    for item in self._read_value(
                        analysis,
                        "warnings",
                        default=(),
                    )
                ),
            )
            for analysis in paper_analyses or ()
        )

    def _map_direction_analysis(
        self,
        direction_analysis: object | None,
    ) -> ResearchDirectionAnalysisView | None:
        """Map research direction analysis into presentation state."""

        if direction_analysis is None:
            return None

        synthesis = self._read_value(
            direction_analysis,
            "synthesis",
            default={},
        )

        return ResearchDirectionAnalysisView(
            synthesis=ResearchSynthesisView(
                themes=self._map_findings(
                    self._read_value(
                        synthesis,
                        "themes",
                        default=(),
                    )
                ),
                comparisons=self._map_findings(
                    self._read_value(
                        synthesis,
                        "comparisons",
                        default=(),
                    )
                ),
                shared_limitations=self._map_findings(
                    self._read_value(
                        synthesis,
                        "shared_limitations",
                        default=(),
                    )
                ),
                unresolved_questions=self._map_findings(
                    self._read_value(
                        synthesis,
                        "unresolved_questions",
                        default=(),
                    )
                ),
            ),
            candidate_directions=tuple(
                ResearchDirectionView(
                    direction=str(
                        self._read_value(
                            direction,
                            "direction",
                            default="",
                        )
                    ),
                    rationale=str(
                        self._read_value(
                            direction,
                            "rationale",
                            default="",
                        )
                    ),
                    context_evidence=self._map_evidence(
                        self._read_value(
                            direction,
                            "context_evidence",
                            default=(),
                        )
                    ),
                    literature_evidence=self._map_evidence(
                        self._read_value(
                            direction,
                            "literature_evidence",
                            default=(),
                        )
                    ),
                    speculative=bool(
                        self._read_value(
                            direction,
                            "speculative",
                            default=False,
                        )
                    ),
                )
                for direction in self._read_value(
                    direction_analysis,
                    "candidate_directions",
                    default=(),
                )
            ),
        )

    def _map_findings(
        self,
        findings: object,
    ) -> tuple[ResearchFindingView, ...]:
        """Map evidence-supported findings into presentation state."""

        mapped_findings = []

        for finding in findings or ():
            content = self._normalize_optional_text(
                self._read_value(
                    finding,
                    "content",
                    default=None,
                )
            )

            if (
                content is None
                or content.casefold() in {"null", "none"}
            ):
                continue

            mapped_findings.append(
                ResearchFindingView(
                    content=content,
                    evidence=self._map_evidence(
                        self._read_value(
                            finding,
                            "evidence",
                            default=(),
                        )
                    ),
                )
            )

        return tuple(
            mapped_findings
        )

    def _map_required_finding(
        self,
        finding: object,
    ) -> ResearchFindingView:
        """Map one required finding with an explicit unavailable value."""

        mapped_findings = self._map_findings(
            (
                finding,
            )
        )

        if mapped_findings:
            return mapped_findings[0]

        return ResearchFindingView(
            content="Not available from metadata/abstract.",
            evidence=(),
        )

    def _map_evidence(
        self,
        evidence: object,
    ) -> tuple[ResearchEvidenceReferenceView, ...]:
        """Map evidence references into presentation state."""

        return tuple(
            ResearchEvidenceReferenceView(
                source_type=str(
                    self._read_value(
                        reference,
                        "source_type",
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
                page_number=self._read_value(
                    reference,
                    "page_number",
                    default=None,
                ),
                section=self._normalize_optional_text(
                    self._read_value(
                        reference,
                        "section",
                        default=None,
                    )
                ),
            )
            for reference in evidence or ()
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
