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
    ExistingResearchContext,
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
        context: ExistingResearchContext | None = None,
    ) -> ResearchStrategy:
        """Build a research strategy for a request."""

        objective = self._build_objective(request)
        request_concepts = self._build_concepts(request)
        concepts = self._build_concepts(request, context)
        sub_questions = self._build_sub_questions(request)

        LOGGER.debug(
            "Research strategy: concepts=%d sub_questions=%d",
            len(concepts),
            len(sub_questions),
        )

        # Empty research requests should not generate
        # executable search strategies.
        if not objective and not request_concepts:
            return ResearchStrategy(
                concepts=(),
                search_terms=(),
                objective=None,
                sub_questions=(),
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
            search_terms=(),
            objective=objective,
            sub_questions=sub_questions,
            constraints=constraints,
            source_names=source_names,
            rationale=(
                (
                    "Research strategy derived from the submitted "
                    "research question, guidance, and existing "
                    "research context."
                )
                if context is not None
                else (
                    "Research strategy derived from the submitted "
                    "research question and guidance."
                )
            ),
        )

    @staticmethod
    def _build_objective(
        request: ResearchRequest,
    ) -> str | None:
        """Build the research objective from the submitted question."""

        question = request.question.strip()

        return question or None

    @classmethod
    def _build_concepts(
        cls,
        request: ResearchRequest,
        context: ExistingResearchContext | None = None,
    ) -> tuple[str, ...]:
        """Build ordered research concepts from request inputs."""

        concepts: list[str] = []

        for focus_area in request.focus_areas:
            normalized = focus_area.strip()

            if normalized and normalized not in concepts:
                concepts.append(normalized)

        guidance = request.guidance.strip()

        if guidance:
            for concept in guidance.split("."):
                normalized = concept.strip()

                if (
                    normalized
                    and not cls._is_constraint(normalized)
                    and not normalized.endswith("?")
                    and normalized not in concepts
                ):
                    concepts.append(normalized)

        question_concept = cls._build_question_concept(
            request.question
        )

        if question_concept and question_concept not in concepts:
            concepts.append(question_concept)

        if context is not None:
            context_findings = (
                context.stated_future_work
                + context.unresolved_questions
                + context.limitations
                + (
                    (context.research_problem,)
                    if context.research_problem is not None
                    else ()
                )
            )

            for finding in context_findings:
                normalized = finding.content.strip()

                if normalized and normalized not in concepts:
                    concepts.append(normalized)

        return tuple(concepts)

    @classmethod
    def _build_constraints(
        cls,
        request: ResearchRequest,
    ) -> tuple[str, ...]:
        """Build deterministic strategy constraints from guidance."""

        constraints: list[str] = []

        for item in request.constraints:
            normalized = item.strip()

            if normalized and normalized not in constraints:
                constraints.append(normalized)

        guidance = request.guidance.strip()

        if guidance:
            for item in guidance.split("."):
                normalized = item.strip()

                if not normalized:
                    continue

                if cls._is_constraint(normalized):
                    constraint = normalized + "."
                    if constraint not in constraints:
                        constraints.append(constraint)

        return tuple(constraints)

    @staticmethod
    def _build_sub_questions(
        request: ResearchRequest,
    ) -> tuple[str, ...]:
        """Build explicit research sub-questions from guidance."""

        sub_questions: list[str] = []

        guidance = request.guidance.strip()

        if guidance:
            for item in guidance.split("."):
                normalized = item.strip()

                if normalized.endswith("?") and normalized not in sub_questions:
                    sub_questions.append(normalized)

        return tuple(sub_questions)

    @staticmethod
    def _build_question_concept(
        question: str,
    ) -> str:
        """Build a concise search concept from the research question."""

        normalized = " ".join(question.split()).strip()
        lowered = normalized.lower()

        prefixes = (
            "find recent research on ",
            "find research on ",
            "find relevant research on ",
        )

        for prefix in prefixes:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix):]
                break

        return normalized.rstrip(".?").strip()

    @staticmethod
    def _is_constraint(
        value: str,
    ) -> bool:
        """Return whether a guidance item is a strategy constraint."""

        lowered = value.lower()

        return (
            lowered.startswith("prefer ")
            or lowered.startswith("focus ")
            or lowered.startswith("avoid ")
            or lowered.startswith("require ")
        )
