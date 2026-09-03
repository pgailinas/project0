# ============================================================
# Project0 - Research Source Service
#
# File: research_source_service.py
#
# Purpose:
#     Execute Research Agent source searches against configured
#     research providers and return normalized results.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, replace
import re
import unicodedata

from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


@dataclass(slots=True)
class ResearchSourceService:
    """Execute research searches against supported providers."""

    providers: dict[
        str,
        ResearchSourceProviderProtocol,
    ]

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search configured research providers for a strategy."""

        source_names = strategy.source_names or (
            "semantic_scholar",
        )

        references: list[ResearchSourceReference] = []
        failures: list[str] = []
        query_strategies = tuple(
            replace(
                strategy,
                search_terms=(query,),
            )
            for query in strategy.search_terms
        ) or (strategy,)

        for source_name in source_names:
            provider = self.providers.get(source_name)

            if provider is None:
                raise ValueError(
                    f"Unsupported research source: {source_name}"
                )

            for query_strategy in query_strategies:
                try:
                    references.extend(
                        provider.search(query_strategy)
                    )

                except RuntimeError as error:
                    failures.append(
                        f"{source_name}: {error}"
                    )
                    continue

        if not references and failures:
            raise RuntimeError(
                "All research sources failed: "
                + "; ".join(failures)
            )

        return self._deduplicate_references(references)

    @staticmethod
    def _deduplicate_references(
        references: list[ResearchSourceReference],
    ) -> tuple[ResearchSourceReference, ...]:
        """Consolidate duplicate publication versions in source order."""

        unique_references: list[ResearchSourceReference] = []

        for reference in references:
            duplicate_index = next(
                (
                    index
                    for index, existing in enumerate(unique_references)
                    if ResearchSourceService._references_match(
                        existing,
                        reference,
                    )
                ),
                None,
            )

            if duplicate_index is None:
                unique_references.append(reference)
                continue

            existing = unique_references[duplicate_index]
            if (
                ResearchSourceService._reference_richness(reference)
                > ResearchSourceService._reference_richness(existing)
            ):
                unique_references[duplicate_index] = reference

        return tuple(unique_references)

    @classmethod
    def _references_match(
        cls,
        first: ResearchSourceReference,
        second: ResearchSourceReference,
    ) -> bool:
        """Return whether two references describe the same publication."""

        if (
            first.source_name == second.source_name
            and first.source_id == second.source_id
        ):
            return True

        first_identifiers = cls._stable_identifiers(first)
        second_identifiers = cls._stable_identifiers(second)

        if first_identifiers & second_identifiers:
            return True

        if cls._normalize_text(first.title) != cls._normalize_text(
            second.title
        ):
            return False

        if (
            first.publication_year is not None
            and second.publication_year is not None
            and first.publication_year != second.publication_year
        ):
            return False

        first_authors = cls._normalized_authors(first.authors)
        second_authors = cls._normalized_authors(second.authors)

        return (
            not first_authors
            or not second_authors
            or bool(first_authors & second_authors)
        )

    @classmethod
    def _stable_identifiers(
        cls,
        reference: ResearchSourceReference,
    ) -> set[str]:
        """Extract normalized DOI and arXiv identifiers."""

        values = [reference.source_id, reference.source_url or ""]
        values.extend(
            str(value)
            for key, value in reference.metadata.items()
            if key.lower() in {
                "arxiv",
                "arxiv_id",
                "doi",
                "external_ids",
            }
        )
        text = " ".join(values).lower()
        identifiers = {
            f"arxiv:{match}"
            for match in re.findall(
                r"(?:arxiv[:./ ]*)(\d{4}\.\d{4,5})(?:v\d+)?",
                text,
            )
        }
        identifiers.update(
            f"doi:{match.rstrip('.,;)}]')}"
            for match in re.findall(
                r"10\.\d{4,9}/[^\s\"<>]+",
                text,
            )
        )
        return identifiers

    @classmethod
    def _normalized_authors(
        cls,
        authors: tuple[str, ...],
    ) -> set[str]:
        """Normalize author names for cross-provider overlap matching."""

        return {
            " ".join(sorted(cls._normalize_text(author).split()))
            for author in authors
            if cls._normalize_text(author)
        }

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize human-readable text for canonical comparison."""

        ascii_value = unicodedata.normalize(
            "NFKD",
            value,
        ).encode("ascii", "ignore").decode("ascii")
        return " ".join(
            re.findall(r"[a-z0-9]+", ascii_value.lower())
        )

    @staticmethod
    def _reference_richness(
        reference: ResearchSourceReference,
    ) -> tuple[int, int, int, int, int]:
        """Rank duplicate versions by useful normalized metadata."""

        abstract = reference.metadata.get("abstract")
        abstract_text = abstract if isinstance(abstract, str) else ""

        return (
            len(abstract_text.strip()),
            len(reference.authors),
            len(reference.metadata),
            int(reference.publication_year is not None),
            int(reference.source_url is not None),
        )
