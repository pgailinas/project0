# ============================================================
# Project0 - Semantic Scholar Source Provider
#
# File: semantic_scholar_source_provider.py
#
# Purpose:
#     Implement Semantic Scholar research source provider used by
#     Project0 Research Agent source services.
#
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SemanticScholarSourceProvider(
    ResearchSourceProviderProtocol,
):
    """Search Semantic Scholar for research references."""

    semantic_scholar_base_url: str = (
        "https://api.semanticscholar.org/graph/v1"
    )
    timeout_seconds: float = 30.0
    maximum_results: int = 10

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search Semantic Scholar for references."""

        if not strategy.search_terms:
            return ()

        query = " ".join(strategy.search_terms)

        endpoint = (
            f"{self.semantic_scholar_base_url.rstrip('/')}"
            "/paper/search"
        )

        params = {
            "query": query,
            "limit": self.maximum_results,
            "fields": "paperId,title,authors,year,url",
        }

        LOGGER.debug(
            "Semantic Scholar request endpoint=%s query=%s limit=%d",
            endpoint,
            query,
            self.maximum_results,
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
                "Semantic Scholar request failed with HTTP status "
                f"{error.response.status_code}."
            ) from error

        except httpx.RequestError as error:
            raise RuntimeError(
                "Semantic Scholar service could not be reached: "
                f"{type(error).__name__}: {error}"
            ) from error

        try:
            response_data = response.json()

        except ValueError as error:
            raise ValueError(
                "Semantic Scholar response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "Semantic Scholar response must be a JSON object."
            )

        data = response_data.get("data")

        if not isinstance(data, list):
            raise TypeError(
                "Semantic Scholar response did not include a data list."
            )

        references = [
            self._build_reference(item)
            for item in data
        ]

        return tuple(references)

    def _build_reference(
        self,
        item: Any,
    ) -> ResearchSourceReference:
        """Normalize one Semantic Scholar search result."""

        if not isinstance(item, dict):
            raise TypeError(
                "Semantic Scholar search result must be a JSON object."
            )

        return ResearchSourceReference(
            source_name="semantic_scholar",
            source_id=self._get_required_string(
                item,
                "paperId",
            ),
            title=self._get_required_string(
                item,
                "title",
            ),
            source_url=self._get_optional_string(
                item,
                "url",
            ),
            authors=self._get_authors(
                item.get("authors")
            ),
            publication_year=self._get_optional_int(
                item,
                "year",
            ),
            metadata={},
        )

    def _get_authors(
        self,
        value: Any,
    ) -> tuple[str, ...]:
        """Return normalized author names."""

        if value is None:
            return ()

        if not isinstance(value, list):
            raise TypeError(
                "Semantic Scholar authors must be a list or null."
            )

        authors = []

        for author in value:
            if not isinstance(author, dict):
                raise TypeError(
                    "Semantic Scholar author must be a JSON object."
                )

            name = author.get("name")

            if not isinstance(name, str):
                raise TypeError(
                    "Semantic Scholar author name must be a string."
                )

            authors.append(name)

        return tuple(authors)

    @staticmethod
    def _get_required_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string response field."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                f"Semantic Scholar {field_name} must be a string."
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
                f"Semantic Scholar {field_name} must be a string or null."
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
                f"Semantic Scholar {field_name} must be an integer or null."
            )

        return value
