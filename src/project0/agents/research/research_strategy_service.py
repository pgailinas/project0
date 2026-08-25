# ============================================================
# Project0 - Research Strategy Service
#
# File: research_strategy_service.py
#
# Purpose:
#     Build structured research strategies from Research Agent
#     requests using deterministic request data.
#
# ============================================================

from __future__ import annotations

import logging

from project0.models.research_models import (
    ResearchRequest,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


class ResearchStrategyService:
    """Build structured Research Agent strategies."""

    def __init__(
        self,
        source_names: tuple[str, ...],
    ) -> None:
        """Initialize the strategy service configuration."""

        self.source_names = source_names

    def build_strategy(
        self,
        request: ResearchRequest,
    ) -> ResearchStrategy:
        """Build a research strategy for a request."""

        concepts = self._build_concepts(request)
        search_terms = self._build_search_terms(
            request,
            concepts,
        )

        LOGGER.debug(
            "Research strategy: concepts=%d search_terms=%d",
            len(concepts),
            len(search_terms),
        )

        # Empty research requests should not generate
        # executable search strategies.
        if not concepts and not search_terms:
            return ResearchStrategy(
                concepts=(),
                search_terms=(),
                constraints=(),
                source_names=(),
                rationale=None,
            )

        source_names = self.source_names

        constraints = self._build_constraints(
            request,
        )

        return ResearchStrategy(
            concepts=concepts,
            search_terms=search_terms,
            constraints=constraints,
            source_names=source_names,
            rationale=(
                "Research strategy derived from the submitted "
                "research question and guidance."
            ),
        )

    @staticmethod
    def _build_concepts(
        request: ResearchRequest,
    ) -> tuple[str, ...]:
        """Build ordered research concepts from request inputs."""

        concepts: list[str] = []

        guidance = request.guidance.strip()

        if guidance:
            for concept in guidance.split("."):
                normalized = concept.strip()

                if normalized and normalized not in concepts:
                    concepts.append(normalized)

        question = request.question.strip()

        if question and question not in concepts:
            concepts.append(question)

        return tuple(concepts)

    @staticmethod
    def _build_constraints(
        request: ResearchRequest,
    ) -> tuple[str, ...]:
        """Build deterministic strategy constraints from guidance."""

        constraints: list[str] = []

        guidance = request.guidance.strip()

        if guidance:
            for item in guidance.split("."):
                normalized = item.strip()

                if not normalized:
                    continue

                lowered = normalized.lower()

                if (
                    lowered.startswith("prefer ")
                    or lowered.startswith("focus ")
                    or lowered.startswith("avoid ")
                    or lowered.startswith("require ")
                ):
                    constraint = normalized + "."
                    if constraint not in constraints:
                        constraints.append(constraint)

        return tuple(constraints)

    @staticmethod
    def _build_search_terms(
        request: ResearchRequest,
        concepts: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Build deterministic search terms from research concepts."""

        search_terms: list[str] = []

        for concept in concepts:
            if concept not in search_terms:
                search_terms.append(concept)

        question = request.question.strip()

        if question and question not in search_terms:
            search_terms.append(question)

        return tuple(search_terms)
