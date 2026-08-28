# ============================================================
# Project0 - Research Models
#
# File: research_models.py
#
# Purpose:
#     Define Research Agent data models used by Project0
#     research workflows, services, and interfaces.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ResearchStatus(StrEnum):
    """Supported research workflow states."""

    PENDING = "pending"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class ResearchArtifactType(StrEnum):
    """Supported Research Agent artifact types."""

    PAPER_SUMMARY = "paper_summary"
    LITERATURE_COMPARISON = "literature_comparison"
    RESEARCH_GAP = "research_gap"
    EXPERIMENT_PROPOSAL = "experiment_proposal"


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """A request for Research Agent processing."""

    question: str
    guidance: str = ""
    max_results: int = 10
    constraints: tuple[str, ...] = ()
    focus_areas: tuple[str, ...] = ()
    source_names: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class ResearchStrategy:
    """A structured strategy derived from a research request."""

    concepts: tuple[str, ...]
    search_terms: tuple[str, ...]
    objective: str | None = None
    sub_questions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    source_names: tuple[str, ...] = ()
    rationale: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchSourceReference:
    """A normalized reference returned by an external research source."""

    source_name: str
    source_id: str
    title: str
    source_url: str | None = None
    authors: tuple[str, ...] = ()
    publication_year: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PaperMetadata:
    """Normalized metadata for one candidate research paper."""

    source_reference: ResearchSourceReference
    title: str
    authors: tuple[str, ...] = ()
    publication_year: int | None = None
    abstract: str | None = None
    venue: str | None = None
    doi: str | None = None
    source_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResearchEvaluation:
    """Research relevance evaluation for one candidate paper."""

    paper: PaperMetadata
    relevance_score: float | None
    relevance_summary: str
    strengths: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    research_connections: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchArtifact:
    """A structured Research Agent output artifact."""

    artifact_type: ResearchArtifactType
    title: str
    content: str
    source_references: tuple[ResearchSourceReference, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    artifact_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class ResearchResult:
    """Result of a Research Agent workflow request."""

    request_id: str
    status: ResearchStatus
    summary: str
    strategy: ResearchStrategy | None
    source_references: tuple[ResearchSourceReference, ...]
    papers: tuple[PaperMetadata, ...]
    evaluations: tuple[ResearchEvaluation, ...]
    artifacts: tuple[ResearchArtifact, ...]
    created_at: datetime
    warnings: tuple[str, ...] = ()
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
