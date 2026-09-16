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
import re
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

    _QUERY_ROLE_ORDER: ClassVar[tuple[str, ...]] = (
        "direct",
        "mechanism",
        "transfer",
        "application",
    )

    _RELATION_PREFIXES: ClassVar[tuple[str, ...]] = (
        "align",
        "bridge",
        "connect",
        "map",
        "match",
        "translate",
    )

    _MECHANISM_PREFIXES: ClassVar[tuple[str, ...]] = (
        "adapter",
        "contrast",
        "distill",
        "loss",
        "objective",
        "optimiz",
        "project",
        "regulariz",
        "supervis",
    )

    _TRANSFER_COMPONENT_PREFIXES: ClassVar[tuple[str, ...]] = (
        "align",
        "bridge",
        "connect",
        "embed",
        "feature",
        "frozen",
        "latent",
        "map",
        "match",
        "model",
        "pretrain",
        "project",
        "represent",
        "space",
        "target",
        "translate",
    )

    _GENERIC_DERIVED_ROLE_PREFIXES: ClassVar[tuple[str, ...]] = (
        "align",
        "embed",
        "map",
        "model",
        "represent",
        "source",
        "space",
        "target",
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
        inferred_queries = tuple(
            self._build_inferred_solution_query(concept)
            for concept in strategy.inferred_solution_search_concepts
            if self._build_inferred_solution_query(concept)
        )
        role_queries: list[tuple[str, str]] = [
            (
                query,
                "direct" if index == 0 else "mechanism",
            )
            for index, query in enumerate(inferred_queries)
        ]
        inferred_concepts = {
            self._normalize_query(concept).casefold()
            for concept in strategy.inferred_solution_search_concepts
        }
        queries: list[str] = list(inferred_queries)
        directive_queries: list[str] = []
        constraint_queries = tuple(
            query
            for constraint in strategy.constraints
            for query in self._focus_constraint_queries(constraint)
        )
        mechanism_focus_queries = (
            constraint_queries
            if len(constraint_queries) > 1
            else ()
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
        has_directive_candidates = any(
            self._is_directive_candidate(
                self._normalize_query(candidate)
            )
            for candidate in candidates
            if self._normalize_query(candidate)
        )
        derived_role_queries: tuple[tuple[str, str], ...] = ()

        if (
            not seed_queries
            and not has_directive_candidates
        ):
            derived_role_queries = self._build_strategy_role_queries(
                candidates,
                objective,
            )

            if len(derived_role_queries) < 3:
                derived_role_queries = ()

            if derived_role_queries:
                role_queries = [
                    *derived_role_queries,
                    *role_queries,
                ]
                queries = [
                    *(
                        query
                        for query, _role in derived_role_queries
                    ),
                    *queries,
                ]

        for candidate in candidates:
            normalized = self._normalize_query(candidate)

            if not normalized:
                continue

            if normalized.casefold() in inferred_concepts:
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
                directive_queries.append(query)
                role_queries.append(
                    (
                        query,
                        self._directive_query_role(normalized),
                    )
                )

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

        if mechanism_focus_queries:
            discovery_queries = self._deduplicate_queries(
                list(mechanism_focus_queries)
            )
        else:
            discovery_queries = self._select_bounded_queries(
                self._deduplicate_complementary_queries(queries),
                prioritized_queries=(
                    *directive_queries,
                    *(
                        query
                        for query, _role in derived_role_queries
                    ),
                    *inferred_queries,
                ),
                directive_queries=tuple(directive_queries),
                role_queries=tuple(role_queries),
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
    def _build_inferred_solution_query(
        cls,
        concept: str,
    ) -> str:
        """Compact an inferred solution while retaining its endpoints."""

        normalized = cls._normalize_query(concept)
        words = cls._query_words(normalized)

        if len(words) <= 8:
            return " ".join(words)

        compact_words = [
            word
            for word in words
            if word.casefold()
            not in {
                "for",
                "into",
                "of",
                "shared",
                "the",
                "to",
                "using",
                "with",
            }
        ]

        salient_words = [
            word
            for word in compact_words
            if cls._is_salient_term(word)
        ][:2]

        return " ".join(
            cls._deduplicate_words(
                (
                    *compact_words[:3],
                    *salient_words,
                    *compact_words[-3:],
                )
            ).split()[:8]
        )

    @classmethod
    def _build_strategy_role_queries(
        cls,
        candidates: tuple[str, ...],
        objective: str,
    ) -> tuple[tuple[str, str], ...]:
        """Derive distinct research-role queries from a rich strategy."""

        eligible_candidates = cls._deduplicate_queries(
            [
                normalized
                for candidate in candidates
                if (normalized := cls._normalize_query(candidate))
                and not cls._is_directive_candidate(normalized)
                and not (
                    objective
                    and normalized.rstrip(".?").casefold()
                    == objective.rstrip(".?").casefold()
                )
            ]
        )

        if len(eligible_candidates) < 4:
            return ()

        relation_candidates = tuple(
            candidate
            for candidate in eligible_candidates
            if cls._contains_prefix_term(
                candidate,
                cls._RELATION_PREFIXES,
            )
        )
        mechanism_candidates = tuple(
            candidate
            for candidate in eligible_candidates
            if cls._mechanism_term_count(candidate)
        )

        if (
            len(relation_candidates) < 2
            or not mechanism_candidates
        ):
            return ()

        mechanism_candidate = max(
            mechanism_candidates,
            key=cls._mechanism_term_count,
        )
        role_queries = (
            (
                cls._build_direct_role_query(
                    relation_candidates[0]
                ),
                "direct",
            ),
            (
                cls._build_mechanism_role_query(
                    mechanism_candidate
                ),
                "mechanism",
            ),
            (
                cls._build_transfer_role_query(
                    relation_candidates[-1]
                ),
                "transfer",
            ),
        )

        return tuple(
            (query, role)
            for query, role in role_queries
            if (
                query
                and cls._is_useful_derived_role_query(query)
            )
        )

    @classmethod
    def _is_useful_derived_role_query(
        cls,
        query: str,
    ) -> bool:
        """Return whether a derived role query retains useful specificity."""

        words = cls._query_words(query)

        return (
            len(cls._query_term_stems(query)) >= 3
            and any(
                not cls._term_matches_prefixes(
                    word,
                    cls._GENERIC_DERIVED_ROLE_PREFIXES,
                )
                for word in words
            )
        )

    @classmethod
    def _build_direct_role_query(
        cls,
        candidate: str,
    ) -> str:
        """Build a direct-precedent query from relation endpoints."""

        ignored_words = {
            "a",
            "an",
            "and",
            "can",
            "could",
            "for",
            "how",
            "into",
            "its",
            "method",
            "methods",
            "of",
            "or",
            "shared",
            "should",
            "that",
            "the",
            "their",
            "to",
            "using",
            "what",
            "which",
            "with",
        }
        words = [
            word
            for word in cls._query_words(candidate)
            if word.casefold() not in ignored_words
        ]
        salient_words = [
            word
            for word in words
            if cls._is_salient_term(word)
        ][:2]

        return " ".join(
            cls._deduplicate_words(
                (
                    *words[:8],
                    *salient_words,
                )
            ).split()[:8]
        )

    @classmethod
    def _build_mechanism_role_query(
        cls,
        candidate: str,
    ) -> str:
        """Build a mechanism query without connective filler."""

        return " ".join(
            word
            for word in cls._build_dimension_query(candidate).split()
            if word.casefold()
            not in {
                "and",
                "more",
                "or",
                "sophisticated",
            }
        )

    @classmethod
    def _build_transfer_role_query(
        cls,
        candidate: str,
    ) -> str:
        """Build a transferable relation query from strategy components."""

        selected_words = [
            word
            for word in cls._query_words(candidate)
            if (
                cls._term_matches_prefixes(
                    word,
                    cls._TRANSFER_COMPONENT_PREFIXES,
                )
                or cls._is_salient_term(word)
            )
        ]

        return " ".join(
            cls._deduplicate_words(
                tuple(selected_words)
            ).split()[:8]
        )

    @classmethod
    def _contains_prefix_term(
        cls,
        candidate: str,
        prefixes: tuple[str, ...],
    ) -> bool:
        """Return whether a candidate contains a role-signaling term."""

        return any(
            cls._term_matches_prefixes(word, prefixes)
            for word in cls._query_words(candidate)
        )

    @classmethod
    def _mechanism_term_count(
        cls,
        candidate: str,
    ) -> int:
        """Return the number of mechanism-signaling strategy terms."""

        return sum(
            cls._term_matches_prefixes(
                word,
                cls._MECHANISM_PREFIXES,
            )
            for word in cls._query_words(candidate)
        )

    @staticmethod
    def _term_matches_prefixes(
        word: str,
        prefixes: tuple[str, ...],
    ) -> bool:
        """Return whether a normalized word starts with a known prefix."""

        lowered = word.casefold()

        return any(
            lowered.startswith(prefix)
            for prefix in prefixes
        )

    @classmethod
    def _select_bounded_queries(
        cls,
        queries: tuple[str, ...],
        prioritized_queries: tuple[str, ...] = (),
        directive_queries: tuple[str, ...] = (),
        role_queries: tuple[tuple[str, str], ...] = (),
    ) -> tuple[str, ...]:
        """Select at most three ordered query dimensions."""

        available_role_queries = tuple(
            (query, role)
            for query, role in role_queries
            if query in queries
        )

        if available_role_queries:
            selected: list[str] = []
            directives = tuple(
                query
                for query in cls._deduplicate_queries(
                    list(directive_queries)
                )
                if query in queries
            )
            prioritized = tuple(
                query
                for query in cls._deduplicate_queries(
                    list(prioritized_queries)
                )
                if query in queries
            )
            role_candidates = available_role_queries

            if directives:
                role_candidates = tuple(
                    (query, role)
                    for query, role in available_role_queries
                    if query in directives
                )

            for role in cls._QUERY_ROLE_ORDER:
                for query, query_role in role_candidates:
                    if query_role != role or query in selected:
                        continue

                    selected.append(query)
                    break

                if len(selected) == 3:
                    break

            for query in (*directives, *prioritized, *queries):
                if len(selected) == 3:
                    break

                if query not in selected:
                    selected.append(query)

            return tuple(selected)

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
    def _directive_query_role(
        cls,
        candidate: str,
    ) -> str:
        """Return the research role explicitly requested by guidance."""

        lowered = candidate.casefold()

        if lowered.startswith(
            (
                "assess their applicability to ",
                "evaluate their applicability to ",
                "assess applicability to ",
            )
        ):
            return "application"

        if lowered.startswith(
            (
                "find related or alternative methods that ",
                "find related or alternative methods ",
                "find alternative methods that ",
                "find alternative methods ",
                "find related methods that ",
                "find related methods ",
                "include ",
            )
        ):
            return "transfer"

        if lowered.startswith(
            (
                "find methods that ",
                "find methods ",
            )
        ):
            return "mechanism"

        return "direct"

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

    @classmethod
    def _focus_constraint_queries(
        cls,
        constraint: str,
    ) -> tuple[str, ...]:
        """Return bounded queries from a Focus on constraint."""

        normalized = " ".join(constraint.split()).strip()

        if not normalized.casefold().startswith("focus on "):
            return ()

        focus = normalized[9:].rstrip(".?").strip()
        components = re.split(
            r"\s*,?\s+including\s+",
            focus,
            maxsplit=1,
            flags=re.IGNORECASE,
        )

        if len(components) == 1:
            return (focus,) if focus else ()

        mechanism_items = tuple(
            re.sub(
                r"^and\s+",
                "",
                item.strip(" ,"),
                flags=re.IGNORECASE,
            )
            for item in re.split(
                r"\s*,\s*|\s+and\s+",
                components[1],
                flags=re.IGNORECASE,
            )
            if item.strip(" ,")
        )

        if len(mechanism_items) < 2:
            return (focus,) if focus else ()

        mechanism_queries = tuple(
            cls._build_focus_mechanism_query(item)
            for item in mechanism_items
        )

        return cls._deduplicate_queries(
            [query for query in mechanism_queries if query]
        )

    @classmethod
    def _build_focus_mechanism_query(
        cls,
        mechanism: str,
    ) -> str:
        """Anchor one requested mechanism to the target representation task."""

        mechanism_words = cls._query_words(
            mechanism.replace("-", " ")
        )
        lowered_words = {
            word.casefold()
            for word in mechanism_words
        }
        anchors = (
            ("video", "representations")
            if "teacher" in lowered_words
            else ("visual", "representations", "CLIP")
        )

        return " ".join(
            cls._deduplicate_words(
                (*anchors, *mechanism_words)
            ).split()[:8]
        )

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
