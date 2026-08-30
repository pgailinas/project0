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
        candidates = (
            *strategy.search_terms,
            *strategy.concepts,
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
                and normalized.casefold()
                == objective.casefold()
            ):
                continue

            if len(normalized.split()) > 8:
                continue

            queries.append(normalized)

            if len(queries) >= 4:
                break

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
                    if query.casefold()
                    != objective.casefold()
                ]

            if fallback_queries:
                shortest_query = min(
                    fallback_queries,
                    key=lambda query: (
                        len(query.split()),
                        len(query),
                    ),
                )
                queries.append(
                    " ".join(
                        shortest_query.split()[:8]
                    )
                )

        return replace(
            strategy,
            search_terms=self._deduplicate_queries(queries),
        )

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:
        """Normalize query whitespace."""

        return " ".join(query.split()).strip()

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
