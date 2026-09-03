# ============================================================
# Project0 - Research Agent View Models
#
# File: research_agent_view_models.py
#
# Purpose:
#     Define immutable presentation models used by the
#     Research Agent browser interface.
#
#     This version introduces a consolidated researcher-facing
#     result model while preserving workflow-level models for
#     internal validation and future detailed views.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from project0.models.research_models import ResearchStatus


class ResearchAgentPageStatus(StrEnum):
    """Supported Research Agent page states."""

    READY = "ready"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ResearchRequestForm:
    """User-entered research request values."""

    question: str = ""
    guidance: str = ""
    max_results: int = 10
    context_source_name: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchSourceView:
    """One research source reference prepared for browser display."""

    source_name: str
    source_id: str
    title: str
    source_url: str | None = None
    authors: tuple[str, ...] = ()
    publication_year: int | None = None


@dataclass(frozen=True, slots=True)
class PaperMetadataView:
    """Paper metadata prepared for browser display."""

    source_id: str
    title: str
    authors: tuple[str, ...] = ()
    publication_year: int | None = None
    abstract: str | None = None
    venue: str | None = None
    doi: str | None = None
    source_url: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchEvaluationView:
    """Research paper evaluation prepared for browser display."""

    source_id: str
    title: str
    relevance_score: float | None
    relevance_summary: str
    strengths: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    research_connections: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def has_warnings(self) -> bool:
        """Return True when the evaluation contains warnings."""

        return bool(self.warnings)


@dataclass(frozen=True, slots=True)
class ResearchResultView:
    """Consolidated research result prepared for browser display."""

    rank: int
    source_id: str
    title: str
    publication_year: int | None = None
    source_name: str | None = None
    relevance_score: float | None = None
    relevance_summary: str = ""
    authors: tuple[str, ...] = ()
    abstract: str | None = None
    venue: str | None = None
    doi: str | None = None
    source_url: str | None = None
    strengths: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    research_connections: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    analysis: PaperAnalysisView | None = None


@dataclass(frozen=True, slots=True)
class ResearchEvidenceReferenceView:
    """Evidence reference prepared for browser display."""

    source_type: str
    source_id: str
    page_number: int | None = None
    section: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchFindingView:
    """Evidence-supported finding prepared for browser display."""

    content: str
    evidence: tuple[ResearchEvidenceReferenceView, ...] = ()


@dataclass(frozen=True, slots=True)
class ExistingResearchContextView:
    """Existing research context analysis prepared for browser display."""

    research_problem: ResearchFindingView | None = None
    prior_work: tuple[ResearchFindingView, ...] = ()
    implemented_approaches: tuple[ResearchFindingView, ...] = ()
    findings: tuple[ResearchFindingView, ...] = ()
    limitations: tuple[ResearchFindingView, ...] = ()
    unresolved_questions: tuple[ResearchFindingView, ...] = ()
    stated_future_work: tuple[ResearchFindingView, ...] = ()


@dataclass(frozen=True, slots=True)
class PaperAnalysisView:
    """Structured retained-paper analysis prepared for browser display."""

    source_id: str
    title: str
    analysis_basis: str
    problem: ResearchFindingView
    approach: ResearchFindingView
    representations: tuple[ResearchFindingView, ...] = ()
    modalities: tuple[ResearchFindingView, ...] = ()
    learning_objectives: tuple[ResearchFindingView, ...] = ()
    datasets_tasks: tuple[ResearchFindingView, ...] = ()
    findings: tuple[ResearchFindingView, ...] = ()
    limitations: tuple[ResearchFindingView, ...] = ()
    research_relevance: ResearchFindingView | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchSynthesisView:
    """Cross-paper synthesis prepared for browser display."""

    themes: tuple[ResearchFindingView, ...] = ()
    comparisons: tuple[ResearchFindingView, ...] = ()
    shared_limitations: tuple[ResearchFindingView, ...] = ()
    unresolved_questions: tuple[ResearchFindingView, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchDirectionView:
    """Candidate research direction prepared for browser display."""

    direction: str
    rationale: str
    context_evidence: tuple[ResearchEvidenceReferenceView, ...] = ()
    literature_evidence: tuple[ResearchEvidenceReferenceView, ...] = ()
    speculative: bool = False


@dataclass(frozen=True, slots=True)
class ResearchDirectionAnalysisView:
    """Research synthesis and candidate directions for display."""

    synthesis: ResearchSynthesisView
    candidate_directions: tuple[ResearchDirectionView, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchWorkflowSummaryView:
    """Research workflow counts prepared for browser display."""

    source_count: int = 0
    paper_count: int = 0
    evaluation_count: int = 0


@dataclass(frozen=True, slots=True)
class ResearchAgentPageView:
    """Complete Research Agent Work Area presentation state."""

    page_status: ResearchAgentPageStatus
    status_message: str
    request_form: ResearchRequestForm
    request_id: str | None = None
    workflow_status: ResearchStatus | None = None
    results: tuple[ResearchResultView, ...] = ()
    existing_research_context: ExistingResearchContextView | None = None
    direction_analysis: ResearchDirectionAnalysisView | None = None
    workflow_summary: ResearchWorkflowSummaryView | None = None
    warnings: tuple[str, ...] = ()
    error_message: str | None = None

    @property
    def has_results(self) -> bool:
        """Return True when the page contains research results."""

        return bool(
            self.results
            or self.existing_research_context
            or self.direction_analysis
        )

    @property
    def has_warnings(self) -> bool:
        """Return True when the page contains workflow warnings."""

        return bool(self.warnings)

    @property
    def has_error(self) -> bool:
        """Return True when the page contains an error message."""

        return self.error_message is not None
