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
import re

from project0.models.research_models import (
    ExistingResearchContext,
    ResearchGuidanceRelevance,
    ResearchGuidanceSeed,
    ResearchRequest,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


class ResearchStrategyService:
    """Build structured Research Agent strategies."""

    _MAX_GUIDANCE_SEEDS = 8

    _NAMED_METHOD_CUE_PATTERN = re.compile(
        r"\b(?:assess|include|including|such as|for example|e\.g\.,?|"
        r"named methods?\s*:|methods?\s*:|papers?\s*:|"
        r"pay special attention to)\s+"
        r"([^.;!?]+)",
        flags=re.IGNORECASE,
    )

    _PROCEDURAL_GUIDANCE_PREFIXES = (
        "compare ",
        "do not ",
        "explain ",
        "for each ",
        "highlight ",
        "identify ",
        "report ",
        "search ",
        "summarize ",
    )

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
        seed_terms = self._build_seed_terms(request)
        guidance_seeds = self._build_guidance_seeds(request)
        sub_questions = self._build_sub_questions(request)

        LOGGER.debug(
            "Research strategy: concepts=%d sub_questions=%d",
            len(concepts),
            len(sub_questions),
        )

        for index, concept in enumerate(concepts):
            LOGGER.debug(
                "Research strategy concept[%d]=%s",
                index,
                concept,
            )

        # Empty research requests should not generate
        # executable search strategies.
        if not objective and not request_concepts:
            return ResearchStrategy(
                concepts=(),
                search_terms=(),
                seed_terms=(),
                guidance_seeds=(),
                objective=None,
                sub_questions=(),
                constraints=(),
                source_names=(),
                rationale=None,
                inferred_solution_search_concepts=(),
            )

        source_names = self.source_names

        constraints = self._build_constraints(
            request,
        )

        return ResearchStrategy(
            concepts=concepts,
            search_terms=(),
            seed_terms=seed_terms,
            guidance_seeds=guidance_seeds,
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
            inferred_solution_search_concepts=(
                context.inferred_solution_search_concepts
                if context is not None
                else ()
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

            if (
                normalized
                and not cls._is_constraint(normalized)
                and normalized not in concepts
            ):
                concepts.append(normalized)

        guidance = request.guidance.strip()

        if guidance:
            for concept in cls._guidance_items(guidance):
                for normalized in cls._guidance_concepts(concept):
                    if normalized not in concepts:
                        concepts.append(normalized)

        question_concept = cls._build_question_concept(
            request.question
        )

        if question_concept and question_concept not in concepts:
            concepts.append(question_concept)

        if context is not None:
            for concept in context.inferred_solution_search_concepts:
                normalized = concept.strip()

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
            for item in cls._guidance_items(guidance):
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
            for item in ResearchStrategyService._guidance_items(guidance):
                normalized = item.strip()

                if normalized.endswith("?") and normalized not in sub_questions:
                    sub_questions.append(normalized)

        return tuple(sub_questions)

    @classmethod
    def _build_seed_terms(
        cls,
        request: ResearchRequest,
    ) -> tuple[str, ...]:
        """Extract explicit publication seeds from research guidance."""

        guidance = " ".join(request.guidance.split()).strip()
        return cls._extract_seed_terms(guidance)

    @classmethod
    def _build_guidance_seeds(
        cls,
        request: ResearchRequest,
    ) -> tuple[ResearchGuidanceSeed, ...]:
        """Retain publication seeds with their explicit designation."""

        seeds: list[ResearchGuidanceSeed] = []

        for item in cls._guidance_items(request.guidance):
            relevance = (
                ResearchGuidanceRelevance.HIGH
                if re.search(
                    r"\b(?:highly relevant|high[- ]relevance)\b",
                    item,
                    flags=re.IGNORECASE,
                )
                else None
            )
            for term in cls._extract_seed_terms(item):
                candidate = ResearchGuidanceSeed(
                    term=term,
                    relevance=relevance,
                )
                if candidate not in seeds:
                    seeds.append(candidate)

        return tuple(seeds[: cls._MAX_GUIDANCE_SEEDS])

    @classmethod
    def _extract_seed_terms(
        cls,
        guidance: str,
    ) -> tuple[str, ...]:
        """Extract ordered publication titles and identifiers from text."""

        seed_terms: list[str] = []

        for match in re.finditer(
            r'["\u201c]([^"\u201d]+)["\u201d]',
            guidance,
        ):
            cls._append_unique(seed_terms, match.group(1))

        for match in re.finditer(
            r"(?:arxiv\s*:\s*)?(\d{4}\.\d{4,5})(?:v\d+)?",
            guidance,
            flags=re.IGNORECASE,
        ):
            cls._append_unique(
                seed_terms,
                f"arXiv:{match.group(1)}",
            )

        for match in re.finditer(
            r"(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)"
            r"(10\.\d{4,9}/[^\s\"<>]+)",
            guidance,
            flags=re.IGNORECASE,
        ):
            cls._append_unique(
                seed_terms,
                f"doi:{match.group(1).rstrip('.,;:)}]')}",
            )

        for match in cls._NAMED_METHOD_CUE_PATTERN.finditer(guidance):
            for candidate in re.split(
                r"\s*,\s*|\s*;\s*|\s+and\s+",
                match.group(1),
                flags=re.IGNORECASE,
            ):
                normalized = re.sub(
                    r"^(?:and|or|the|a|an)\s+",
                    "",
                    candidate.strip(" \t\r\n:()[]{}"),
                    flags=re.IGNORECASE,
                )
                if cls._is_named_method(normalized):
                    cls._append_unique(seed_terms, normalized)

        return tuple(seed_terms[: cls._MAX_GUIDANCE_SEEDS])

    @staticmethod
    def _is_named_method(value: str) -> bool:
        """Return whether a signposted list item looks like a proper name."""

        words = value.split()
        if not 1 <= len(words) <= 8:
            return False

        connecting_words = {"a", "an", "for", "in", "of", "the", "to"}
        significant_words = [
            word
            for word in words
            if word.casefold() not in connecting_words
        ]
        if not significant_words:
            return False

        return all(
            word[0].isupper()
            and any(character.isalpha() for character in word)
            for word in significant_words
        )

    @staticmethod
    def _append_unique(
        values: list[str],
        value: str,
    ) -> None:
        """Append one normalized value unless already present."""

        normalized = " ".join(value.split()).strip()

        if normalized and normalized.casefold() not in {
            item.casefold()
            for item in values
        }:
            values.append(normalized)

    @staticmethod
    def _guidance_items(
        guidance: str,
    ) -> tuple[str, ...]:
        """Split guidance sentences without treating line wraps as items."""

        normalized_guidance = " ".join(guidance.split())

        return tuple(
            item
            for item in (
                value.strip()
                for value in re.split(
                    r"(?<!\d)\.|\.(?!\d)",
                    normalized_guidance,
                )
            )
            if item
        )

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

    @classmethod
    def _guidance_concepts(
        cls,
        value: str,
    ) -> tuple[str, ...]:
        """Extract searchable subjects without retaining research commands."""

        normalized = value.strip()

        if not normalized or normalized.endswith("?"):
            return ()

        inclusion_match = re.match(
            r"include (?:approaches|methods|research|work) "
            r"(?:that |which )?(?:use|using|based on|involving) (.+)",
            normalized,
            flags=re.IGNORECASE,
        )
        if inclusion_match:
            payload = re.sub(
                r",?\s+and other (?:relevant )?(?:approaches|methods|work)"
                r"(?: discovered in the literature)?$",
                "",
                inclusion_match.group(1),
                flags=re.IGNORECASE,
            )
            return tuple(
                item
                for item in (
                    part.strip()
                    for part in re.split(r",\s*", payload)
                )
                if item
            )

        applicable_match = re.match(
            r"search (?:broadly )?for (?:approaches|methods|research|work) "
            r"applicable to (.+)",
            normalized,
            flags=re.IGNORECASE,
        )
        if applicable_match:
            return (applicable_match.group(1).strip(),)

        if cls._is_constraint(normalized):
            return ()

        return (normalized,)

    @classmethod
    def _is_constraint(
        cls,
        value: str,
    ) -> bool:
        """Return whether a guidance item is a strategy constraint."""

        lowered = value.lower()

        return (
            lowered.startswith("prefer ")
            or lowered.startswith("focus ")
            or lowered.startswith("avoid ")
            or lowered.startswith("require ")
            or lowered.startswith("prioritize ")
            or lowered.startswith(cls._PROCEDURAL_GUIDANCE_PREFIXES)
            or bool(
                re.match(
                    r"include (?:approaches|methods|research|work) "
                    r"(?:that |which )?(?:use|using|based on|involving) ",
                    lowered,
                )
            )
        )
