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

from project0.models.research_models import (
    ResearchArtifactType,
    ResearchStatus,
)


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
    artifact_title: str | None = None
    artifact_content: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchArtifactView:
    """One Research Agent artifact prepared for browser display."""

    artifact_id: str
    artifact_type: ResearchArtifactType
    title: str
    content: str
    source_ids: tuple[str, ...] = ()

    @property
    def has_sources(self) -> bool:
        """Return True when the artifact contains source references."""

        return bool(self.source_ids)


@dataclass(frozen=True, slots=True)
class ResearchWorkflowSummaryView:
    """Research workflow counts prepared for browser display."""

    source_count: int = 0
    paper_count: int = 0
    evaluation_count: int = 0
    artifact_count: int = 0


@dataclass(frozen=True, slots=True)
class ResearchAgentPageView:
    """Complete Research Agent Work Area presentation state."""

    page_status: ResearchAgentPageStatus
    status_message: str
    request_form: ResearchRequestForm
    request_id: str | None = None
    workflow_status: ResearchStatus | None = None
    results: tuple[ResearchResultView, ...] = ()
    artifacts: tuple[ResearchArtifactView, ...] = ()
    workflow_summary: ResearchWorkflowSummaryView | None = None
    warnings: tuple[str, ...] = ()
    error_message: str | None = None

    @property
    def has_results(self) -> bool:
        """Return True when the page contains research results."""

        return bool(
            self.results
            or self.artifacts
        )

    @property
    def has_warnings(self) -> bool:
        """Return True when the page contains workflow warnings."""

        return bool(self.warnings)

    @property
    def has_error(self) -> bool:
        """Return True when the page contains an error message."""

        return self.error_message is not None
