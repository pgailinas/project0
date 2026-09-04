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

from dataclasses import dataclass, field, replace
import logging
import re
import unicodedata

from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ResearchSourceService:
    """Execute research searches against supported providers."""

    providers: dict[
        str,
        ResearchSourceProviderProtocol,
    ]
    evaluation_candidate_limit: int = 24
    last_search_statistics: dict[str, int] = field(
        default_factory=dict,
        init=False,
    )

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search configured research providers for a strategy."""

        source_names = strategy.source_names or (
            "semantic_scholar",
        )

        if self.evaluation_candidate_limit < 1:
            raise ValueError(
                "Research evaluation candidate limit must be positive."
            )

        self.last_search_statistics = {}
        references: list[ResearchSourceReference] = []
        reference_groups: list[
            tuple[ResearchSourceReference, ...]
        ] = []
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
                if not self._provider_supports_query(
                    source_name,
                    query_strategy,
                ):
                    continue

                try:
                    group = tuple(
                        provider.search(query_strategy)
                    )
                    reference_groups.append(group)
                    references.extend(group)

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

        deduplicated_references = self._deduplicate_references(
            references
        )
        seed_references = tuple(
            reference
            for reference in deduplicated_references
            if self._matches_any_seed(
                reference,
                strategy.seed_terms,
            )
        )
        selected_references = self._select_balanced_candidates(
            deduplicated_references=deduplicated_references,
            reference_groups=reference_groups,
            seed_references=seed_references,
            limit=self.evaluation_candidate_limit,
        )

        self.last_search_statistics = {
            "retrieved_count": len(references),
            "deduplicated_count": len(deduplicated_references),
            "seed_preserved_count": len(seed_references),
            "evaluation_candidate_count": len(selected_references),
        }
        LOGGER.info(
            "Research source selection: retrieved=%d deduplicated=%d "
            "seed_preserved=%d evaluation_candidates=%d",
            self.last_search_statistics["retrieved_count"],
            self.last_search_statistics["deduplicated_count"],
            self.last_search_statistics["seed_preserved_count"],
            self.last_search_statistics["evaluation_candidate_count"],
        )

        return selected_references

    @staticmethod
    def _provider_supports_query(
        source_name: str,
        strategy: ResearchStrategy,
    ) -> bool:
        """Return whether a provider supports the query form."""

        if source_name.casefold() != "crossref":
            return True

        if len(strategy.search_terms) != 1:
            return True

        query = strategy.search_terms[0].strip()

        return re.fullmatch(
            r"(?:arxiv:\s*|https?://(?:www\.)?arxiv\.org/"
            r"(?:abs|pdf)/)?\d{4}\.\d{4,5}(?:v\d+)?(?:\.pdf)?",
            query,
            flags=re.IGNORECASE,
        ) is None

    @classmethod
    def _select_balanced_candidates(
        cls,
        *,
        deduplicated_references: tuple[ResearchSourceReference, ...],
        reference_groups: list[tuple[ResearchSourceReference, ...]],
        seed_references: tuple[ResearchSourceReference, ...],
        limit: int,
    ) -> tuple[ResearchSourceReference, ...]:
        """Preserve seeds, then select fairly across result groups."""

        selected = list(seed_references)
        grouped_candidates: list[list[ResearchSourceReference]] = []

        for group in reference_groups:
            candidates: list[ResearchSourceReference] = []

            for reference in group:
                canonical = next(
                    (
                        candidate
                        for candidate in deduplicated_references
                        if cls._references_match(candidate, reference)
                    ),
                    None,
                )

                if (
                    canonical is None
                    or cls._contains_reference(selected, canonical)
                    or cls._contains_reference(candidates, canonical)
                ):
                    continue

                candidates.append(canonical)

            grouped_candidates.append(candidates)

        while (
            len(selected) < limit
            and any(grouped_candidates)
        ):
            for candidates in grouped_candidates:
                while (
                    candidates
                    and cls._contains_reference(
                        selected,
                        candidates[0],
                    )
                ):
                    candidates.pop(0)

                if not candidates:
                    continue

                selected.append(candidates.pop(0))

                if len(selected) >= limit:
                    break

        return tuple(selected)

    @classmethod
    def _matches_any_seed(
        cls,
        reference: ResearchSourceReference,
        seed_terms: tuple[str, ...],
    ) -> bool:
        """Return whether a reference exactly matches a supplied seed."""

        reference_title = cls._normalize_text(reference.title)
        reference_identifiers = cls._stable_identifiers(reference)

        for seed in seed_terms:
            normalized_seed = cls._normalize_text(seed)

            if normalized_seed and normalized_seed == reference_title:
                return True

            seed_identifiers = cls._stable_identifiers(
                ResearchSourceReference(
                    source_name="seed",
                    source_id=seed,
                    title=seed,
                    source_url=seed,
                )
            )

            if seed_identifiers & reference_identifiers:
                return True

        return False

    @classmethod
    def _contains_reference(
        cls,
        references: list[ResearchSourceReference],
        candidate: ResearchSourceReference,
    ) -> bool:
        """Return whether a publication is already in a reference list."""

        return any(
            cls._references_match(reference, candidate)
            for reference in references
        )

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
        source_id_match = re.fullmatch(
            r"(?:arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?",
            reference.source_id.lower(),
        )

        if source_id_match is not None:
            identifiers.add(
                f"arxiv:{source_id_match.group(1)}"
            )

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
