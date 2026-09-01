# ============================================================
# Project0 - Research Query Service
#
# File: research_query_service.py
#
# Purpose:
#     Generate deterministic research queries from structured
#     Research Strategy inputs.
#
# ============================================================

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace

from project0.models.research_models import ResearchStrategy


@dataclass(slots=True)
class ResearchQueryService:
    """Generate provider-ready research queries.

    Version 1 behavior:
    - deterministic output
    - no external APIs
    - no LLM calls
    - no provider-specific logic
    """

    def generate_queries(
        self,
        strategy: ResearchStrategy,
    ) -> ResearchStrategy:
        """Generate deterministic research queries from a strategy."""

        queries: list[str] = []
        constraint_queries = tuple(
            self._focus_constraint_query(constraint)
            for constraint in strategy.constraints
            if self._focus_constraint_query(constraint)
        )
        candidates = (
            *strategy.search_terms,
            *strategy.concepts,
            *constraint_queries,
        )
        objective = self._normalize_query(
            strategy.objective or ""
        )

        for candidate in candidates:
            normalized = self._normalize_query(candidate)

            if not normalized:
                continue

            if (
                objective
                and normalized.rstrip(".?").casefold()
                == objective.rstrip(".?").casefold()
            ):
                continue

            queries.append(
                self._build_dimension_query(normalized)
            )

        if not queries:
            fallback_queries = [
                self._normalize_query(candidate)
                for candidate in candidates
                if self._normalize_query(candidate)
            ]

            if objective:
                fallback_queries = [
                    query
                    for query in fallback_queries
                    if query.rstrip(".?").casefold()
                    != objective.rstrip(".?").casefold()
                ]

            if fallback_queries:
                queries.append(
                    self._build_fallback_query(
                        fallback_queries
                    )
                )

        return replace(
            strategy,
            search_terms=self._select_bounded_queries(
                self._deduplicate_complementary_queries(queries)
            ),
        )

    @classmethod
    def _build_dimension_query(
        cls,
        candidate: str,
    ) -> str:
        """Build one bounded query for a strategy dimension."""

        normalized = cls._normalize_query(candidate)

        if len(normalized.split()) <= 8:
            return normalized

        return cls._query_fragment(
            normalized,
            maximum_words=8,
        )

    @staticmethod
    def _select_bounded_queries(
        queries: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Select at most three ordered query dimensions."""

        if len(queries) <= 3:
            return queries

        return (
            queries[0],
            queries[1],
            queries[-1],
        )

    @classmethod
    def _build_fallback_query(
        cls,
        candidates: list[str],
    ) -> str:
        """Build a bounded fallback from prioritized concepts."""

        if len(candidates) == 1:
            return " ".join(
                candidates[0].split()[:8]
            )

        first_fragment = cls._query_fragment(
            candidates[0],
            maximum_words=4,
        )
        shared_fragment = cls._shared_terms_fragment(
            candidates,
            excluded_words=set(first_fragment.casefold().split()),
            maximum_words=4,
        )
        domain_fragment = cls._query_fragment(
            candidates[-1],
            maximum_words=4,
        )

        combined = cls._deduplicate_words(
            (
                first_fragment,
                shared_fragment,
                domain_fragment,
            )
        )

        return " ".join(
            combined.split()[:8]
        )

    @classmethod
    def _shared_terms_fragment(
        cls,
        candidates: list[str],
        excluded_words: set[str],
        maximum_words: int,
    ) -> str:
        """Extract recurring technical terms across concepts."""

        ignored_words = {
            "a",
            "an",
            "and",
            "are",
            "be",
            "for",
            "from",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "research",
            "should",
            "that",
            "the",
            "to",
            "with",
            "work",
        }
        candidate_words: list[list[str]] = []
        term_counts: Counter[str] = Counter()
        first_positions: dict[str, int] = {}
        position = 0

        for candidate in candidates:
            words = [
                token.strip(",.;:?()").casefold()
                for token in cls._normalize_query(candidate).split()
            ]
            filtered_words = [
                word
                for word in words
                if (
                    word
                    and word not in ignored_words
                )
            ]
            candidate_words.append(filtered_words)
            term_counts.update(set(filtered_words))

            for word in filtered_words:
                if word not in first_positions:
                    first_positions[word] = position
                    position += 1

        excluded_stems = {
            cls._word_stem(word)
            for word in excluded_words
        }

        shared_words = sorted(
            (
                word
                for word, count in term_counts.items()
                if (
                    count >= 2
                    and word not in excluded_words
                    and cls._word_stem(word) not in excluded_stems
                )
            ),
            key=lambda word: (
                -term_counts[word],
                first_positions[word],
            ),
        )

        return " ".join(
            shared_words[:maximum_words]
        )

    @staticmethod
    def _word_stem(
        word: str,
    ) -> str:
        """Normalize common word endings for query deduplication."""

        normalized = word.casefold()

        for suffix in (
            "ment",
            "ing",
            "ed",
            "s",
        ):
            if (
                normalized.endswith(suffix)
                and len(normalized) > len(suffix) + 3
            ):
                return normalized[:-len(suffix)]

        return normalized

    @staticmethod
    def _deduplicate_words(
        fragments: tuple[str, ...],
    ) -> str:
        """Combine query fragments without repeated words."""

        words: list[str] = []
        seen: set[str] = set()

        for fragment in fragments:
            for word in fragment.split():
                key = word.casefold()

                if key in seen:
                    continue

                seen.add(key)
                words.append(word)

        return " ".join(words)

    @classmethod
    def _query_fragment(
        cls,
        query: str,
        maximum_words: int,
    ) -> str:
        """Extract a bounded technical phrase from a concept."""

        normalized = " ".join(query.split()).strip()
        lowered = normalized.casefold()

        prefixes = (
            "the research problem is to investigate the ",
            "the research problem is to investigate ",
            "additional research may investigate ",
            "future work should explore ",
            "future work should investigate ",
            "future research should focus on ",
            "future research should focus ",
            "future research should explore ",
            "future research should investigate ",
            "investigate ",
            "explore ",
            "how should ",
            "how can ",
            "how do ",
            "how are ",
        )

        for prefix in prefixes:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix):]
                break

        words = [
            token.strip(",.;:?()")
            for token in normalized.split()
        ]
        words = [
            word
            for word in words
            if word
        ]
        salient_words = cls._deduplicate_words(
            tuple(
                word
                for word in words
                if cls._is_salient_term(word)
            )
        ).split()[:2]
        base_word_count = max(
            maximum_words - len(salient_words),
            0,
        )
        selected_words = cls._deduplicate_words(
            (
                *words[:base_word_count],
                *salient_words,
            )
        ).split()[:maximum_words]

        while (
            selected_words
            and selected_words[-1].casefold()
            in {
                "and",
                "or",
                "rather",
                "than",
            }
        ):
            selected_words.pop()

        return " ".join(selected_words)

    @staticmethod
    def _is_salient_term(
        term: str,
    ) -> bool:
        """Return whether a term carries acronym-like domain detail."""

        letters = [
            character
            for character in term
            if character.isalpha()
        ]

        if len(letters) < 2:
            return False

        return (
            all(character.isupper() for character in letters)
            or any(character.isupper() for character in term[1:])
        )

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:
        """Normalize query whitespace."""

        return " ".join(query.split()).strip()

    @staticmethod
    def _focus_constraint_query(
        constraint: str,
    ) -> str:
        """Return a query phrase from a Focus on constraint."""

        normalized = " ".join(constraint.split()).strip()

        if not normalized.casefold().startswith("focus on "):
            return ""

        return normalized[9:].rstrip(".?").strip()

    @staticmethod
    def _deduplicate_queries(
        queries: list[str],
    ) -> tuple[str, ...]:
        """Remove duplicate queries while preserving order."""

        unique_queries: list[str] = []
        seen: set[str] = set()

        for query in queries:
            if query in seen:
                continue

            seen.add(query)
            unique_queries.append(query)

        return tuple(unique_queries)

    @classmethod
    def _deduplicate_complementary_queries(
        cls,
        queries: list[str],
    ) -> tuple[str, ...]:
        """Remove duplicate and substantially overlapping queries."""

        unique_queries: list[str] = []

        for query in cls._deduplicate_queries(queries):
            query_terms = cls._query_term_stems(query)

            if not query_terms:
                continue

            if any(
                cls._query_overlap(
                    query_terms,
                    cls._query_term_stems(existing_query),
                ) >= 0.75
                for existing_query in unique_queries
            ):
                continue

            unique_queries.append(query)

        return tuple(unique_queries)

    @classmethod
    def _query_term_stems(
        cls,
        query: str,
    ) -> set[str]:
        """Return meaningful normalized terms for query comparison."""

        ignored_words = {
            "a",
            "an",
            "and",
            "are",
            "be",
            "for",
            "from",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "the",
            "to",
            "with",
        }

        return {
            cls._word_stem(word)
            for word in (
                token.strip(",.;:?()").casefold()
                for token in query.split()
            )
            if word and word not in ignored_words
        }

    @staticmethod
    def _query_overlap(
        first_terms: set[str],
        second_terms: set[str],
    ) -> float:
        """Return overlap relative to the smaller query dimension."""

        if not first_terms or not second_terms:
            return 0.0

        return (
            len(first_terms & second_terms)
            / min(len(first_terms), len(second_terms))
        )
