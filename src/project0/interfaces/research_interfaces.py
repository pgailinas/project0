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
    PaperMetadata,
    ResearchArtifact,
    ResearchEvaluation,
    ResearchRequest,
    ResearchResult,
    ResearchSourceReference,
    ResearchStrategy,
)


class ResearchStrategyServiceProtocol(Protocol):
    """Interface for Research Agent strategy services."""

    def build_strategy(
        self,
        request: ResearchRequest,
    ) -> ResearchStrategy:
        """Build a research strategy from a research request."""

        ...


class ResearchQueryServiceProtocol(Protocol):
    """Interface for Research Agent query generation services."""

    def generate_queries(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[str, ...]:
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
    ) -> ResearchResult:
        """Execute the Research Agent workflow."""

        ...
