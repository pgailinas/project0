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
from typing import ClassVar
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

    _VISUAL_ALIGNMENT_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "clip",
            "image",
            "images",
            "multimodal",
            "video",
            "videos",
            "vision",
            "visual",
        }
    )
    _LANGUAGE_ALIGNMENT_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "caption",
            "captions",
            "clip",
            "language",
            "semantic",
            "text",
            "textual",
        }
    )
    _MECHANISM_ALIGNMENT_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "adaptation",
            "align",
            "alignment",
            "autoencoder",
            "contrastive",
            "distillation",
            "embedding",
            "embeddings",
            "latent",
            "prompting",
            "representation",
            "representations",
        }
    )
    _REPRESENTATION_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "autoencoder",
            "embedding",
            "embeddings",
            "encoder",
            "latent",
            "representation",
            "representations",
        }
    )
    _TRANSFER_MECHANISM_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "align",
            "alignment",
            "contrastive",
            "distillation",
            "distill",
            "mapping",
            "projection",
        }
    )
    _TRANSFERABLE_VISUAL_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "clip",
            "image",
            "images",
            "vision",
            "visual",
        }
    )
    _EXCLUDED_TRANSFER_TASK_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "audio",
            "debiasing",
            "diffusion",
            "forecasting",
            "generation",
            "generative",
        }
    )
    _EXPLICITLY_UNRELATED_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "audio",
            "ecg",
            "flood",
        }
    )
    _SYNTHESIS_TERMS: ClassVar[frozenset[str]] = frozenset(
        {
            "diffusion",
            "generation",
            "generative",
            "synthesis",
        }
    )

    providers: dict[
        str,
        ResearchSourceProviderProtocol,
    ]
    evaluation_candidate_limit: int = 24
    last_search_statistics: dict[str, int] = field(
        default_factory=dict,
        init=False,
    )
    last_candidate_trace: tuple[dict[str, object], ...] = field(
        default_factory=tuple,
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
        self.last_candidate_trace = ()
        references: list[ResearchSourceReference] = []
        reference_groups: list[
            tuple[ResearchSourceReference, ...]
        ] = []
        reference_group_origins: list[tuple[str, str]] = []
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
                    reference_group_origins.append(
                        (
                            source_name,
                            query_strategy.search_terms[0]
                            if len(query_strategy.search_terms) == 1
                            else "",
                        )
                    )
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
        eligible_references = self._eligible_references(
            strategy=strategy,
            references=deduplicated_references,
            seed_references=seed_references,
        )
        selected_references = self._select_balanced_candidates(
            strategy=strategy,
            deduplicated_references=eligible_references,
            reference_groups=reference_groups,
            reference_group_origins=reference_group_origins,
            seed_references=seed_references,
            limit=self.evaluation_candidate_limit,
        )
        self.last_candidate_trace = self._build_candidate_trace(
            deduplicated_references=deduplicated_references,
            reference_groups=reference_groups,
            reference_group_origins=reference_group_origins,
            seed_references=seed_references,
            eligible_references=eligible_references,
            selected_references=selected_references,
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

        for candidate in self.last_candidate_trace:
            LOGGER.debug(
                "Research candidate trace: deduplicated_rank=%d "
                "evaluation_rank=%s selection=%s title=%r "
                "canonical_source=%s source_id=%s providers=%s "
                "queries=%s identifiers=%s",
                candidate["deduplicated_rank"],
                candidate["evaluation_rank"],
                candidate["selection_status"],
                candidate["title"],
                candidate["canonical_source_name"],
                candidate["source_id"],
                candidate["retrieval_providers"],
                candidate["retrieval_queries"],
                candidate["stable_identifiers"],
            )

        return selected_references

    @classmethod
    def _build_candidate_trace(
        cls,
        *,
        deduplicated_references: tuple[ResearchSourceReference, ...],
        reference_groups: list[tuple[ResearchSourceReference, ...]],
        reference_group_origins: list[tuple[str, str]],
        seed_references: tuple[ResearchSourceReference, ...],
        selected_references: tuple[ResearchSourceReference, ...],
        eligible_references: tuple[ResearchSourceReference, ...],
    ) -> tuple[dict[str, object], ...]:
        """Describe retrieval provenance and balanced selection outcomes."""

        trace: list[dict[str, object]] = []

        for deduplicated_index, reference in enumerate(
            deduplicated_references,
            start=1,
        ):
            providers: list[str] = []
            queries: list[str] = []

            for group, (provider_name, query) in zip(
                reference_groups,
                reference_group_origins,
                strict=True,
            ):
                if not any(
                    cls._references_match(reference, candidate)
                    for candidate in group
                ):
                    continue

                if provider_name not in providers:
                    providers.append(provider_name)

                if query and query not in queries:
                    queries.append(query)

            evaluation_index = next(
                (
                    index
                    for index, selected in enumerate(
                        selected_references,
                        start=1,
                    )
                    if cls._references_match(reference, selected)
                ),
                None,
            )

            if cls._contains_reference(
                list(seed_references),
                reference,
            ):
                selection_status = "preserved_seed"
            elif evaluation_index is not None:
                selection_status = "balanced_selection"
            elif not cls._contains_reference(
                list(eligible_references),
                reference,
            ):
                selection_status = "outside_alignment_profile"
            else:
                selection_status = "outside_balanced_candidate_limit"

            trace.append(
                {
                    "deduplicated_rank": deduplicated_index,
                    "evaluation_rank": evaluation_index,
                    "selection_status": selection_status,
                    "title": reference.title,
                    "canonical_source_name": reference.source_name,
                    "source_id": reference.source_id,
                    "retrieval_providers": tuple(providers),
                    "retrieval_queries": tuple(queries),
                    "stable_identifiers": tuple(
                        sorted(cls._stable_identifiers(reference))
                    ),
                }
            )

        return tuple(trace)

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
        strategy: ResearchStrategy,
        deduplicated_references: tuple[ResearchSourceReference, ...],
        reference_groups: list[tuple[ResearchSourceReference, ...]],
        reference_group_origins: list[tuple[str, str]],
        seed_references: tuple[ResearchSourceReference, ...],
        limit: int,
    ) -> tuple[ResearchSourceReference, ...]:
        """Preserve seeds, then select relevant results fairly by group."""

        selected = list(seed_references)
        grouped_candidates: list[list[ResearchSourceReference]] = []
        anchor_terms = cls._strategy_anchor_terms(strategy)

        for group, (_, query) in zip(
            reference_groups,
            reference_group_origins,
            strict=True,
        ):
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

            candidates.sort(
                key=lambda candidate: cls._candidate_relevance_score(
                    candidate,
                    query=query,
                    anchor_terms=anchor_terms,
                ),
                reverse=True,
            )
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
    def _strategy_anchor_terms(
        cls,
        strategy: ResearchStrategy,
    ) -> set[str]:
        """Return distinctive terms repeated across strategy queries."""

        term_counts: dict[str, int] = {}

        for query in strategy.search_terms:
            for term in cls._meaningful_terms(query):
                term_counts[term] = term_counts.get(term, 0) + 1

        return {
            term
            for term, count in term_counts.items()
            if count > 1
        }

    @classmethod
    def _eligible_references(
        cls,
        *,
        strategy: ResearchStrategy,
        references: tuple[ResearchSourceReference, ...],
        seed_references: tuple[ResearchSourceReference, ...],
    ) -> tuple[ResearchSourceReference, ...]:
        """Retain candidates matching an alignment-focused strategy profile."""

        if not cls._uses_alignment_profile(strategy):
            return references

        return tuple(
            reference
            for reference in references
            if (
                cls._contains_reference(list(seed_references), reference)
                or cls._matches_alignment_profile(strategy, reference)
            )
        )

    @classmethod
    def _uses_alignment_profile(
        cls,
        strategy: ResearchStrategy,
    ) -> bool:
        """Return whether strategy anchors define shared-space alignment."""

        strategy_terms = cls._meaningful_terms(
            " ".join(
                (*strategy.search_terms, *strategy.concepts)
            )
        )

        return (
            bool(strategy_terms & cls._VISUAL_ALIGNMENT_TERMS)
            and bool(strategy_terms & cls._LANGUAGE_ALIGNMENT_TERMS)
            and bool(strategy_terms & cls._MECHANISM_ALIGNMENT_TERMS)
        )

    @classmethod
    def _matches_alignment_profile(
        cls,
        strategy: ResearchStrategy,
        reference: ResearchSourceReference,
    ) -> bool:
        """Return whether a candidate supports visual-language alignment."""

        abstract = reference.metadata.get("abstract")
        abstract_text = abstract if isinstance(abstract, str) else ""
        candidate_terms = cls._meaningful_terms(
            f"{reference.title} {abstract_text}"
        )

        has_language = bool(
            candidate_terms
            & (cls._LANGUAGE_ALIGNMENT_TERMS - {"semantic"})
        )
        has_representation = bool(
            candidate_terms & cls._REPRESENTATION_TERMS
        )
        has_transfer_mechanism = bool(
            candidate_terms & cls._TRANSFER_MECHANISM_TERMS
        )
        is_synthesis_candidate = bool(
            candidate_terms & cls._SYNTHESIS_TERMS
        )
        prioritize_representation_learning = (
            cls._strategy_prioritizes_representation_learning(strategy)
        )
        is_direct = (
            "video" in candidate_terms
            and has_language
            and has_representation
            and has_transfer_mechanism
            and not (
                prioritize_representation_learning
                and is_synthesis_candidate
            )
        )
        is_transferable = (
            bool(candidate_terms & cls._TRANSFERABLE_VISUAL_TERMS)
            and has_language
            and has_representation
            and has_transfer_mechanism
            and not (
                candidate_terms & cls._EXCLUDED_TRANSFER_TASK_TERMS
            )
            and not (
                prioritize_representation_learning
                and is_synthesis_candidate
            )
        )

        if is_direct or is_transferable:
            return True

        profile_terms = (
            cls._VISUAL_ALIGNMENT_TERMS
            | cls._LANGUAGE_ALIGNMENT_TERMS
            | cls._MECHANISM_ALIGNMENT_TERMS
        )

        if not candidate_terms & profile_terms:
            return True

        return not (
            candidate_terms
            & (cls._LANGUAGE_ALIGNMENT_TERMS - {"semantic"})
            or candidate_terms & cls._EXPLICITLY_UNRELATED_TERMS
            or (
                prioritize_representation_learning
                and is_synthesis_candidate
            )
        )

    @classmethod
    def _strategy_prioritizes_representation_learning(
        cls,
        strategy: ResearchStrategy,
    ) -> bool:
        """Return whether a strategy targets representations, not synthesis."""

        strategy_terms = cls._meaningful_terms(
            " ".join(
                (
                    *strategy.concepts,
                    *strategy.search_terms,
                    *strategy.constraints,
                )
            )
        )

        return (
            bool(strategy_terms & cls._REPRESENTATION_TERMS)
            and not bool(strategy_terms & cls._SYNTHESIS_TERMS)
        )

    @classmethod
    def _candidate_relevance_score(
        cls,
        reference: ResearchSourceReference,
        *,
        query: str,
        anchor_terms: set[str],
    ) -> tuple[int, int, int, int]:
        """Score query-derived evidence without replacing LLM evaluation."""

        title_terms = cls._meaningful_terms(reference.title)
        abstract = reference.metadata.get("abstract")
        abstract_text = abstract if isinstance(abstract, str) else ""
        content_terms = title_terms | cls._meaningful_terms(abstract_text)
        query_terms = cls._meaningful_terms(query)

        return (
            len(title_terms & anchor_terms),
            len(content_terms & anchor_terms),
            len(title_terms & query_terms),
            len(content_terms & query_terms),
        )

    @classmethod
    def _meaningful_terms(
        cls,
        value: str,
    ) -> set[str]:
        """Normalize technical terms while excluding retrieval filler."""

        stopwords = {
            "a",
            "an",
            "and",
            "for",
            "from",
            "in",
            "into",
            "its",
            "of",
            "on",
            "or",
            "the",
            "to",
            "using",
            "with",
        }

        return {
            term
            for term in cls._normalize_text(value).split()
            if len(term) > 1 and term not in stopwords
        }

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
                canonical = reference
                alternate = existing
            else:
                canonical = existing
                alternate = reference

            unique_references[duplicate_index] = replace(
                canonical,
                metadata=ResearchSourceService._merge_reference_metadata(
                    canonical.metadata,
                    alternate.metadata,
                ),
            )

        return tuple(unique_references)

    @staticmethod
    def _merge_reference_metadata(
        canonical_metadata: dict[str, object],
        alternate_metadata: dict[str, object],
    ) -> dict[str, object]:
        """Preserve complementary metadata from duplicate provider versions."""

        merged = dict(canonical_metadata)

        for key, value in alternate_metadata.items():
            existing = merged.get(key)

            if (
                key not in merged
                or existing is None
                or (
                    isinstance(existing, str)
                    and not existing.strip()
                )
            ):
                merged[key] = value

        return merged

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
            f"arxiv:{match}"
            for match in re.findall(
                r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})"
                r"(?:v\d+)?",
                text,
            )
        )

        for key, value in reference.metadata.items():
            if key.lower() not in {
                "arxiv",
                "arxiv_id",
            }:
                continue

            metadata_match = re.fullmatch(
                r"(?:arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?",
                str(value).strip(),
                flags=re.IGNORECASE,
            )

            if metadata_match is not None:
                identifiers.add(
                    f"arxiv:{metadata_match.group(1)}"
                )
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
