# ============================================================
# Project0 - Paper Metadata Service
#
# File: paper_metadata_service.py
#
# Purpose:
#     Retrieve and normalize paper metadata from supported
#     external research sources for Research Agent workflows.
#
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from project0.models.research_models import (
    PaperMetadata,
    ResearchSourceReference,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PaperMetadataService:
    """Retrieve paper metadata from supported research sources."""

    semantic_scholar_base_url: str = (
        "https://api.semanticscholar.org/graph/v1"
    )
    timeout_seconds: float = 30.0

    def retrieve_metadata(
        self,
        references: tuple[ResearchSourceReference, ...],
    ) -> tuple[PaperMetadata, ...]:
        """Retrieve metadata for research source references."""

        papers: list[PaperMetadata] = []

        for reference in references:
            if reference.source_name == "semantic_scholar":
                papers.append(
                    self._retrieve_semantic_scholar_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "arxiv":
                papers.append(
                    self._create_arxiv_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "openalex":
                papers.append(
                    self._create_openalex_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "crossref":
                papers.append(
                    self._create_crossref_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "stub":
                papers.append(
                    self._create_stub_metadata(
                        reference
                    )
                )
                continue

            raise ValueError(
                "Unsupported research metadata source: "
                f"{reference.source_name}"
            )

        return tuple(papers)

    def _retrieve_semantic_scholar_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Retrieve paper metadata from Semantic Scholar."""

        endpoint = (
            f"{self.semantic_scholar_base_url.rstrip('/')}"
            f"/paper/{reference.source_id}"
        )

        params = {
            "fields": (
                "paperId,title,authors,year,abstract,"
                "venue,externalIds,url"
            ),
        }

        LOGGER.debug(
            "Semantic Scholar metadata request endpoint=%s "
            "paper_id=%s",
            endpoint,
            reference.source_id,
        )

        try:
            response = httpx.get(
                endpoint,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "Semantic Scholar metadata request failed with HTTP "
                f"status {error.response.status_code}."
            ) from error
        except httpx.RequestError as error:
            raise RuntimeError(
                "Semantic Scholar metadata service could not be reached: "
                f"{type(error).__name__}: {error}"
            ) from error

        try:
            response_data = response.json()
        except ValueError as error:
            raise ValueError(
                "Semantic Scholar metadata response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "Semantic Scholar metadata response must be a JSON object."
            )

        paper_id = self._get_required_string(
            response_data,
            "paperId",
        )

        if paper_id != reference.source_id:
            raise ValueError(
                "Semantic Scholar metadata response paperId did not "
                "match the requested source identifier."
            )

        title = self._get_required_string(
            response_data,
            "title",
        )

        authors = self._get_authors(
            response_data.get("authors")
        )

        publication_year = self._get_optional_int(
            response_data,
            "year",
        )

        abstract = self._get_optional_string(
            response_data,
            "abstract",
        )

        venue = self._get_optional_string(
            response_data,
            "venue",
        )

        source_url = self._get_optional_string(
            response_data,
            "url",
        )

        doi = self._get_doi(
            response_data.get("externalIds")
        )

        return PaperMetadata(
            source_reference=reference,
            title=title,
            authors=authors,
            publication_year=publication_year,
            abstract=abstract,
            venue=venue,
            doi=doi,
            source_url=source_url,
            metadata={
                "paper_id": paper_id,
            },
        )

    def _create_arxiv_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized arXiv source data."""

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=None,
            venue="arXiv",
            source_url=reference.source_url,
            metadata={
                "paper_id": reference.source_id,
                "source": "arxiv",
            },
        )

    def _create_openalex_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized OpenAlex source data."""

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=None,
            venue="OpenAlex",
            source_url=reference.source_url,
            metadata={
                "paper_id": reference.source_id,
                "source": "openalex",
            },
        )

    def _create_crossref_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized Crossref source data."""

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=None,
            venue="Crossref",
            doi=reference.source_id,
            source_url=reference.source_url,
            metadata={
                "paper_id": reference.source_id,
                "source": "crossref",
            },
        )

    def _create_stub_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create deterministic metadata for stub research sources."""

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=(
                "Deterministic Project0 stub metadata "
                "for acceptance testing."
            ),
            venue="Project0 Research Stub",
            source_url=reference.source_url,
            metadata={
                "paper_id": reference.source_id,
                "source": "stub",
            },
        )

    def _get_authors(
        self,
        value: Any,
    ) -> tuple[str, ...]:
        """Return normalized Semantic Scholar author names."""

        if value is None:
            return ()

        if not isinstance(value, list):
            raise TypeError(
                "Semantic Scholar metadata authors must be a list or null."
            )

        authors: list[str] = []

        for author in value:
            if not isinstance(author, dict):
                raise TypeError(
                    "Semantic Scholar metadata author must be a JSON object."
                )

            name = author.get("name")

            if not isinstance(name, str):
                raise TypeError(
                    "Semantic Scholar metadata author name must be a string."
                )

            authors.append(name)

        return tuple(authors)

    def _get_doi(
        self,
        value: Any,
    ) -> str | None:
        """Return a DOI from Semantic Scholar external identifiers."""

        if value is None:
            return None

        if not isinstance(value, dict):
            raise TypeError(
                "Semantic Scholar externalIds must be a JSON object or null."
            )

        doi = value.get("DOI")

        if doi is None:
            return None

        if not isinstance(doi, str):
            raise TypeError(
                "Semantic Scholar DOI must be a string or null."
            )

        return doi

    @staticmethod
    def _get_required_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string response field."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                "Semantic Scholar metadata "
                f"{field_name} must be a string."
            )

        return value

    @staticmethod
    def _get_optional_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str | None:
        """Return an optional string response field."""

        value = mapping.get(field_name)

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                "Semantic Scholar metadata "
                f"{field_name} must be a string or null."
            )

        return value

    @staticmethod
    def _get_optional_int(
        mapping: dict[str, Any],
        field_name: str,
    ) -> int | None:
        """Return an optional integer response field."""

        value = mapping.get(field_name)

        if value is None:
            return None

        if not isinstance(value, int):
            raise TypeError(
                "Semantic Scholar metadata "
                f"{field_name} must be an integer or null."
            )

        return value
