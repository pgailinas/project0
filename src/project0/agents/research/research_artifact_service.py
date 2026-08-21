# ============================================================
# Project0 - Research Artifact Service
#
# File: research_artifact_service.py
#
# Purpose:
#     Generate structured Research Agent artifacts from paper
#     evaluations while preserving source references.
#
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass

from project0.models.research_models import (
    ResearchArtifact,
    ResearchArtifactType,
    ResearchEvaluation,
    ResearchRequest,
    ResearchSourceReference,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ResearchArtifactService:
    """Generate structured artifacts from research evaluations."""

    def generate_artifacts(
        self,
        request: ResearchRequest,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> tuple[ResearchArtifact, ...]:
        """Generate Research Agent artifacts for a research request."""

        if not evaluations:
            return ()

        artifacts: list[ResearchArtifact] = []

        for evaluation in evaluations:
            artifacts.append(
                self._build_paper_summary_artifact(
                    evaluation
                )
            )

        artifacts.append(
            self._build_literature_comparison_artifact(
                evaluations
            )
        )

        artifacts.append(
            self._build_research_gap_artifact(
                request,
                evaluations,
            )
        )

        artifacts.append(
            self._build_experiment_proposal_artifact(
                request,
                evaluations,
            )
        )

        LOGGER.debug(
            "Research artifacts generated: count=%d",
            len(artifacts),
        )

        return tuple(artifacts)

    def _build_paper_summary_artifact(
        self,
        evaluation: ResearchEvaluation,
    ) -> ResearchArtifact:
        """Build a paper summary artifact from one evaluation."""

        paper = evaluation.paper

        content_lines = [
            f"Paper: {paper.title}",
            "",
            "Relevance:",
            evaluation.relevance_summary,
            "",
            "Strengths:",
            *self._format_items(evaluation.strengths),
            "",
            "Limitations:",
            *self._format_items(evaluation.limitations),
            "",
            "Research Connections:",
            *self._format_items(
                evaluation.research_connections
            ),
        ]

        if evaluation.warnings:
            content_lines.extend(
                [
                    "",
                    "Warnings:",
                    *self._format_items(
                        evaluation.warnings
                    ),
                ]
            )

        return ResearchArtifact(
            artifact_type=ResearchArtifactType.PAPER_SUMMARY,
            title=f"{paper.title} Summary",
            content="\n".join(content_lines),
            source_references=(
                paper.source_reference,
            ),
            metadata={
                "relevance_score": (
                    evaluation.relevance_score
                ),
            },
        )

    def _build_literature_comparison_artifact(
        self,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> ResearchArtifact:
        """Build a literature comparison artifact."""

        content_lines = [
            "Literature Comparison",
            "",
        ]

        for evaluation in evaluations:
            content_lines.extend(
                [
                    f"Paper: {evaluation.paper.title}",
                    (
                        "Relevance Score: "
                        f"{evaluation.relevance_score}"
                    ),
                    (
                        "Relevance Summary: "
                        f"{evaluation.relevance_summary}"
                    ),
                    "",
                ]
            )

        return ResearchArtifact(
            artifact_type=(
                ResearchArtifactType.LITERATURE_COMPARISON
            ),
            title="Literature Comparison",
            content="\n".join(content_lines).rstrip(),
            source_references=self._collect_source_references(
                evaluations
            ),
        )

    def _build_research_gap_artifact(
        self,
        request: ResearchRequest,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> ResearchArtifact:
        """Build a research gap artifact."""

        limitations = self._collect_unique_items(
            tuple(
                limitation
                for evaluation in evaluations
                for limitation in evaluation.limitations
            )
        )

        connections = self._collect_unique_items(
            tuple(
                connection
                for evaluation in evaluations
                for connection in evaluation.research_connections
            )
        )

        content_lines = [
            f"Research Question: {request.question}",
            "",
            "Observed Limitations:",
            *self._format_items(limitations),
            "",
            "Potential Research Opportunities:",
            *self._format_items(connections),
        ]

        return ResearchArtifact(
            artifact_type=ResearchArtifactType.RESEARCH_GAP,
            title="Research Gap Analysis",
            content="\n".join(content_lines),
            source_references=self._collect_source_references(
                evaluations
            ),
        )

    def _build_experiment_proposal_artifact(
        self,
        request: ResearchRequest,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> ResearchArtifact:
        """Build an experiment proposal artifact."""

        connections = self._collect_unique_items(
            tuple(
                connection
                for evaluation in evaluations
                for connection in evaluation.research_connections
            )
        )

        content_lines = [
            f"Research Question: {request.question}",
            "",
            "Experiment Directions:",
            *self._format_items(connections),
        ]

        return ResearchArtifact(
            artifact_type=(
                ResearchArtifactType.EXPERIMENT_PROPOSAL
            ),
            title="Experiment Proposal",
            content="\n".join(content_lines),
            source_references=self._collect_source_references(
                evaluations
            ),
        )

    @staticmethod
    def _collect_source_references(
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> tuple[ResearchSourceReference, ...]:
        """Collect unique source references in evaluation order."""

        references: list[ResearchSourceReference] = []
        seen: set[tuple[str, str]] = set()

        for evaluation in evaluations:
            reference = evaluation.paper.source_reference

            key = (
                reference.source_name,
                reference.source_id,
            )

            if key in seen:
                continue

            seen.add(key)
            references.append(reference)

        return tuple(references)

    @staticmethod
    def _collect_unique_items(
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Collect unique string values in source order."""

        unique_values: list[str] = []

        for value in values:
            if value not in unique_values:
                unique_values.append(value)

        return tuple(unique_values)

    @staticmethod
    def _format_items(
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Format values as simple artifact list items."""

        if not values:
            return ("- None identified.",)

        return tuple(
            f"- {value}"
            for value in values
        )
