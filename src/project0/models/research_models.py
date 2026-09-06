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


class ResearchContextDocumentType(StrEnum):
    """Supported existing research context document types."""

    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"


class ResearchContextExtractionStatus(StrEnum):
    """Supported research context extraction states."""

    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class ResearchEvidenceSourceType(StrEnum):
    """Supported Research Agent evidence source types."""

    CONTEXT_DOCUMENT = "context_document"
    RESEARCH_PAPER = "research_paper"


class ResearchPaperAnalysisBasis(StrEnum):
    """Supported retained research paper analysis evidence bases."""

    ABSTRACT_METADATA = "abstract_metadata"


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
    seed_terms: tuple[str, ...] = ()
    objective: str | None = None
    sub_questions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    source_names: tuple[str, ...] = ()
    rationale: str | None = None
    inferred_solution_search_concepts: tuple[str, ...] = ()


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
class ResearchContextDocument:
    """Normalized document supplied as existing research context."""

    source_name: str
    document_type: ResearchContextDocumentType
    extraction_method: str
    extracted_text: str
    extraction_status: ResearchContextExtractionStatus
    warnings: tuple[str, ...] = ()
    page_count: int | None = None
    document_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class ResearchEvidenceReference:
    """Reference to evidence supporting Research Agent analysis."""

    source_type: ResearchEvidenceSourceType
    source_id: str
    page_number: int | None = None
    section: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchFinding:
    """One evidence-supported Research Agent finding."""

    content: str
    evidence: tuple[ResearchEvidenceReference, ...] = ()


@dataclass(frozen=True, slots=True)
class ExistingResearchContext:
    """Structured analysis of supplied existing research."""

    research_problem: ResearchFinding | None = None
    prior_work: tuple[ResearchFinding, ...] = ()
    implemented_approaches: tuple[ResearchFinding, ...] = ()
    findings: tuple[ResearchFinding, ...] = ()
    limitations: tuple[ResearchFinding, ...] = ()
    unresolved_questions: tuple[ResearchFinding, ...] = ()
    stated_future_work: tuple[ResearchFinding, ...] = ()
    inferred_solution_search_concepts: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PaperAnalysis:
    """Structured technical analysis of one retained paper."""

    paper: PaperMetadata
    problem: ResearchFinding
    approach: ResearchFinding
    analysis_basis: ResearchPaperAnalysisBasis = (
        ResearchPaperAnalysisBasis.ABSTRACT_METADATA
    )
    representations: tuple[ResearchFinding, ...] = ()
    modalities: tuple[ResearchFinding, ...] = ()
    learning_objectives: tuple[ResearchFinding, ...] = ()
    datasets_tasks: tuple[ResearchFinding, ...] = ()
    findings: tuple[ResearchFinding, ...] = ()
    limitations: tuple[ResearchFinding, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchSynthesis:
    """Cross-paper Research Agent synthesis."""

    themes: tuple[ResearchFinding, ...] = ()
    comparisons: tuple[ResearchFinding, ...] = ()
    shared_limitations: tuple[ResearchFinding, ...] = ()
    unresolved_questions: tuple[ResearchFinding, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchDirection:
    """One candidate evidence-grounded research direction."""

    direction: str
    rationale: str
    context_evidence: tuple[ResearchEvidenceReference, ...] = ()
    literature_evidence: tuple[ResearchEvidenceReference, ...] = ()
    speculative: bool = False


@dataclass(frozen=True, slots=True)
class ResearchDirectionAnalysis:
    """Cross-paper synthesis and candidate research directions."""

    synthesis: ResearchSynthesis
    candidate_directions: tuple[ResearchDirection, ...] = ()


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
    existing_research_context: ExistingResearchContext | None = None
    paper_analyses: tuple[PaperAnalysis, ...] = ()
    direction_analysis: ResearchDirectionAnalysis | None = None
    warnings: tuple[str, ...] = ()
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
