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

from dataclasses import dataclass

from project0.models.research_models import (
    ResearchArtifact,
    ResearchArtifactType,
    ResearchEvaluation,
    ResearchRequest,
)


@dataclass(slots=True)
class ResearchArtifactService:
    """Generate non-displayed legacy artifacts for workflow compatibility."""

    def generate_artifacts(
        self,
        request: ResearchRequest,
        evaluations: tuple[ResearchEvaluation, ...],
    ) -> tuple[ResearchArtifact, ...]:
        """Generate legacy artifacts without placing them in the UI package."""

        if not evaluations:
            return ()

        comparison_lines = ["Literature Comparison", ""]
        for evaluation in evaluations:
            comparison_lines.extend(
                [
                    f"Paper: {evaluation.paper.title}",
                    f"Relevance Score: {evaluation.relevance_score}",
                    f"Relevance Summary: {evaluation.relevance_summary}",
                    "",
                ]
            )

        limitations = tuple(
            dict.fromkeys(
                limitation
                for evaluation in evaluations
                for limitation in evaluation.limitations
            )
        )
        connections = tuple(
            dict.fromkeys(
                connection
                for evaluation in evaluations
                for connection in evaluation.research_connections
            )
        )
        format_items = lambda values: tuple(
            f"- {value}" for value in values
        ) or ("- None identified.",)

        return (
            ResearchArtifact(
                artifact_type=ResearchArtifactType.LITERATURE_COMPARISON,
                title="Literature Comparison",
                content="\n".join(comparison_lines).rstrip(),
                source_references=(),
            ),
            ResearchArtifact(
                artifact_type=ResearchArtifactType.RESEARCH_GAP,
                title="Research Gap Analysis",
                content="\n".join(
                    (
                        f"Research Question: {request.question}",
                        "",
                        "Observed Limitations:",
                        *format_items(limitations),
                        "",
                        "Potential Research Opportunities:",
                        *format_items(connections),
                    )
                ),
                source_references=(),
            ),
            ResearchArtifact(
                artifact_type=ResearchArtifactType.EXPERIMENT_PROPOSAL,
                title="Experiment Proposal",
                content="\n".join(
                    (
                        f"Research Question: {request.question}",
                        "",
                        "Experiment Directions:",
                        *format_items(connections),
                    )
                ),
                source_references=(),
            ),
        )
