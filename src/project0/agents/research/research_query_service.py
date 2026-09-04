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
from typing import ClassVar

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

    _DIRECTIVE_PREFIXES: ClassVar[tuple[str, ...]] = (
        "assess their applicability to ",
        "evaluate their applicability to ",
        "assess applicability to ",
        "find related or alternative methods that ",
        "find related or alternative methods ",
        "find alternative methods that ",
        "find alternative methods ",
        "find related methods that ",
        "find related methods ",
        "find methods that ",
        "find methods ",
        "include ",
        "prioritize ",
    )

    def generate_queries(
        self,
        strategy: ResearchStrategy,
    ) -> ResearchStrategy:
        """Generate deterministic research queries from a strategy."""

        seed_queries = self._deduplicate_queries(
            [
                self._normalize_query(seed)
                for seed in strategy.seed_terms
                if self._normalize_query(seed)
            ]
        )
        queries: list[str] = []
        prioritized_queries: list[str] = []
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
        directive_anchors = self._directive_anchor_terms(
            candidates
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

            query = self._build_dimension_query(normalized)

            if self._is_directive_candidate(normalized):
                query = self._anchor_directive_query(
                    query,
                    directive_anchors,
                )
                prioritized_queries.append(query)

            queries.append(query)

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

        discovery_queries = self._select_bounded_queries(
            self._deduplicate_complementary_queries(queries),
            prioritized_queries=tuple(prioritized_queries),
        )
        discovery_queries = tuple(
            query
            for query in discovery_queries
            if not any(
                self._query_overlap(
                    self._query_term_stems(query),
                    self._query_term_stems(seed_query),
                ) >= 0.60
                for seed_query in seed_queries
            )
        )

        return replace(
            strategy,
            search_terms=self._deduplicate_queries(
                [*seed_queries, *discovery_queries]
            ),
        )

    @classmethod
    def _build_dimension_query(
        cls,
        candidate: str,
    ) -> str:
        """Build one bounded query for a strategy dimension."""

        normalized = cls._normalize_query(candidate)

        if (
            len(normalized.split()) <= 8
            and not any(
                normalized.casefold().startswith(prefix)
                for prefix in cls._DIRECTIVE_PREFIXES
            )
        ):
            return normalized

        return cls._query_fragment(
            normalized,
            maximum_words=8,
        )

    @classmethod
    def _select_bounded_queries(
        cls,
        queries: tuple[str, ...],
        prioritized_queries: tuple[str, ...] = (),
    ) -> tuple[str, ...]:
        """Select at most three ordered query dimensions."""

        if len(queries) <= 3:
            return queries

        prioritized = tuple(
            query
            for query in cls._deduplicate_queries(
                list(prioritized_queries)
            )
            if query in queries
        )[:3]

        if prioritized:
            remaining = tuple(
                query
                for query in queries
                if query not in prioritized
            )

            return (
                *prioritized,
                *remaining[:3 - len(prioritized)],
            )

        return (
            queries[0],
            queries[1],
            queries[-1],
        )

    @classmethod
    def _is_directive_candidate(
        cls,
        candidate: str,
    ) -> bool:
        """Return whether guidance explicitly requests a search dimension."""

        lowered = candidate.casefold()

        return any(
            lowered.startswith(prefix)
            for prefix in cls._DIRECTIVE_PREFIXES
        )

    @classmethod
    def _directive_anchor_terms(
        cls,
        candidates: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Extract the principal target and relation from guidance."""

        for candidate in candidates:
            if not cls._is_directive_candidate(candidate):
                continue

            words = cls._query_words(candidate)
            salient_terms = cls._deduplicate_words(
                tuple(
                    word
                    for word in words
                    if cls._is_salient_term(word)
                )
            ).split()
            anchors = salient_terms[:1]

            if any(
                cls._word_stem(word) == "align"
                for word in words
            ):
                anchors.append("alignment")

            return tuple(anchors)

        return ()

    @classmethod
    def _anchor_directive_query(
        cls,
        query: str,
        anchors: tuple[str, ...],
    ) -> str:
        """Add missing primary guidance anchors to one query."""

        words = query.split()
        query_stems = {
            cls._word_stem(word)
            for word in words
        }

        for anchor in anchors:
            anchor_stem = cls._word_stem(anchor)

            if anchor_stem in query_stems:
                continue

            if len(words) >= 8:
                words.pop()

            words.append(anchor)
            query_stems.add(anchor_stem)

        return " ".join(words)

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

        compact_directive = False

        for prefix in cls._DIRECTIVE_PREFIXES:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix):]
                compact_directive = True
                break

        if compact_directive:
            lowered = normalized.casefold()

            for qualifier in (
                " even when ",
                " whether or not ",
            ):
                qualifier_index = lowered.find(qualifier)

                if qualifier_index >= 0:
                    normalized = normalized[:qualifier_index]
                    break

            lowered = normalized.casefold()

            target_separator = " with "
            target_index = lowered.find(target_separator)

            if target_index >= 0:
                method_words = cls._query_words(
                    normalized[:target_index]
                )
                target_words = cls._query_words(
                    normalized[
                        target_index + len(target_separator):
                    ]
                )
                method_words = cls._compact_directive_words(
                    method_words
                )
                target_words = cls._compact_directive_words(
                    target_words
                )

                return " ".join(
                    cls._deduplicate_words(
                        (
                            *method_words[:4],
                            *target_words[:4],
                        )
                    ).split()[:maximum_words]
                )

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

        words = cls._query_words(normalized)

        if compact_directive:
            words = cls._compact_directive_words(words)
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
    def _query_words(
        value: str,
    ) -> list[str]:
        """Return normalized query words without boundary punctuation."""

        return [
            word
            for word in (
                token.strip(",.;:?()\"'\u201c\u201d")
                for token in value.split()
            )
            if word
        ]

    @staticmethod
    def _compact_directive_words(
        words: list[str],
    ) -> list[str]:
        """Remove instruction filler without removing technical terms."""

        return [
            word
            for word in words
            if word.casefold()
            not in {
                "and",
                "newly",
                "or",
                "shared",
                "that",
                "the",
                "trained",
                "with",
            }
        ]

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
                token.strip(",.;:?()\"'\u201c\u201d").casefold()
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
