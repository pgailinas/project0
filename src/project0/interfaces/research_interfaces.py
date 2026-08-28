# ============================================================
# Project0 - Research Interfaces
#
# File: research_interfaces.py
#
# Purpose:
#     Define Research Agent interfaces used by Project0
#     research workflows, services, and components.
#
# ============================================================

from __future__ import annotations

from typing import Protocol

from project0.models.research_models import (
    ExistingResearchContext,
    PaperAnalysis,
    PaperMetadata,
    ResearchArtifact,
    ResearchContextDocument,
    ResearchDirectionAnalysis,
    ResearchEvaluation,
    ResearchRequest,
    ResearchResult,
    ResearchSourceReference,
    ResearchStrategy,
)


class ResearchContextIngestionServiceProtocol(Protocol):
    """Interface for research context document ingestion services."""

    def ingest(
        self,
        source_name: str,
        content: bytes,
    ) -> ResearchContextDocument:
        """Ingest and normalize an existing research document."""

        ...


class ExistingResearchContextAnalysisServiceProtocol(Protocol):
    """Interface for existing research context analysis services."""

    def analyze(
        self,
        document: ResearchContextDocument,
    ) -> ExistingResearchContext:
        """Analyze a normalized existing research document."""

        ...


class PaperAnalysisServiceProtocol(Protocol):
    """Interface for retained-paper analysis services."""

    def analyze(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[PaperAnalysis, ...]:
        """Analyze retained papers for a research request."""

        ...


class ResearchDirectionAnalysisServiceProtocol(Protocol):
    """Interface for research direction analysis services."""

    def analyze(
        self,
        request: ResearchRequest,
        context: ExistingResearchContext | None,
        paper_analyses: tuple[PaperAnalysis, ...],
    ) -> ResearchDirectionAnalysis:
        """Analyze evidence and identify research directions."""

        ...


class ResearchStrategyServiceProtocol(Protocol):
    """Interface for Research Agent strategy services."""

    def build_strategy(
        self,
        request: ResearchRequest,
        context: ExistingResearchContext | None = None,
    ) -> ResearchStrategy:
        """Build a research strategy from a research request."""

        ...


class ResearchQueryServiceProtocol(Protocol):
    """Interface for Research Agent query generation services."""

    def generate_queries(
        self,
        strategy: ResearchStrategy,
    ) -> ResearchStrategy:
        """Generate deterministic research queries."""

        ...


class ResearchSourceServiceProtocol(Protocol):
    """Interface for external research source services."""

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search configured research sources."""

        ...


class PaperMetadataServiceProtocol(Protocol):
    """Interface for paper metadata services."""

    def retrieve_metadata(
        self,
        references: tuple[ResearchSourceReference, ...],
    ) -> tuple[PaperMetadata, ...]:
        """Retrieve paper metadata for source references."""

        ...


class ResearchEvaluationServiceProtocol(Protocol):
    """Interface for Research Agent evaluation services."""

    def evaluate(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate candidate papers for a research request."""

        ...


class ResearchArtifactServiceProtocol(Protocol):
    """Interface for Research Agent artifact services."""

    def generate_artifacts(
        self,
        request: ResearchRequest,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> tuple[ResearchArtifact, ...]:
        """Generate research artifacts from evaluations."""

        ...


class ResearchWorkflowProtocol(Protocol):
    """Interface for Research Agent workflows."""

    def execute(
        self,
        request: ResearchRequest,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> ResearchResult:
        """Execute the Research Agent workflow."""

        ...
