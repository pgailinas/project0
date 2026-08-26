# ============================================================
# Project0 - Crossref Research Source Provider
#
# File: crossref_source_provider.py
#
# Purpose:
#     Implement Crossref research source provider used by
#     Project0 Research Agent source services.
#
# ============================================================

from __future__ import annotations

import logging
import time
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
class CrossrefSourceProvider(
    ResearchSourceProviderProtocol,
):
    """Search Crossref for research references."""

    crossref_base_url: str = "https://api.crossref.org"
    timeout_seconds: float = 30.0
    maximum_results: int = 10
    maximum_attempts: int = 3
    retry_delay_seconds: float = 1.0
    user_agent: str = "Project0 Research Agent"
    mailto: str | None = None

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search Crossref for references."""

        query = self._build_query(strategy)

        if not query:
            return ()

        endpoint = (
            f"{self.crossref_base_url.rstrip('/')}"
            "/works"
        )

        params: dict[str, Any] = {
            "query": query,
            "rows": self.maximum_results,
        }

        if self.mailto:
            params["mailto"] = self.mailto

        headers = {
            "User-Agent": self.user_agent,
        }

        LOGGER.debug(
            "Crossref request endpoint=%s query=%s limit=%d",
            endpoint,
            query,
            self.maximum_results,
        )

        last_error: httpx.HTTPError | None = None
        response: httpx.Response | None = None

        for attempt in range(
            1,
            self.maximum_attempts + 1,
        ):
            try:
                response = httpx.get(
                    endpoint,
                    params=params,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                break

            except httpx.HTTPStatusError as error:
                last_error = error
                status_code = error.response.status_code

                if (
                    status_code != 429
                    and status_code < 500
                ):
                    break

            except httpx.RequestError as error:
                last_error = error

            except httpx.HTTPError as error:
                last_error = error
                break

            if attempt < self.maximum_attempts:
                LOGGER.warning(
                    "Crossref request attempt %d of %d failed: %s",
                    attempt,
                    self.maximum_attempts,
                    last_error,
                )

                time.sleep(
                    self._retry_delay_seconds(
                        attempt=attempt,
                        error=last_error,
                    )
                )

        if (
            response is None
            or response.is_error
        ):
            raise RuntimeError(
                "Crossref request failed."
            ) from last_error

        try:
            response_data = response.json()

        except ValueError as error:
            raise ValueError(
                "Crossref response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "Crossref response must be a JSON object."
            )

        message = response_data.get("message")

        if not isinstance(message, dict):
            raise TypeError(
                "Crossref response did not include a message object."
            )

        items = message.get("items")

        if not isinstance(items, list):
            raise TypeError(
                "Crossref response did not include an items list."
            )

        references = []

        for item in items:
            try:
                references.append(
                    self._build_reference(item)
                )
            except TypeError as error:
                LOGGER.warning(
                    "Skipping invalid Crossref search result: %s",
                    error,
                )

        return tuple(references)

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the delay before retrying a Crossref request."""

        if isinstance(
            error,
            httpx.HTTPStatusError,
        ):
            retry_after = error.response.headers.get(
                "Retry-After"
            )

            if retry_after is not None:
                try:
                    return float(retry_after)
                except ValueError:
                    pass

        return (
            self.retry_delay_seconds
            * (2 ** (attempt - 1))
        )

    @staticmethod
    def _build_query(
        strategy: ResearchStrategy,
    ) -> str:
        """Build deterministic Crossref query text."""

        terms = []

        for term in strategy.search_terms:
            normalized = term.strip()

            if normalized and normalized not in terms:
                terms.append(normalized)

        return " ".join(terms)

    def _build_reference(
        self,
        item: Any,
    ) -> ResearchSourceReference:
        """Normalize one Crossref search result."""

        if not isinstance(item, dict):
            raise TypeError(
                "Crossref search result must be a JSON object."
            )

        doi = self._get_required_string(
            item,
            "DOI",
        )

        return ResearchSourceReference(
            source_name="crossref",
            source_id=doi,
            title=self._get_title(
                item.get("title")
            ),
            source_url=self._get_source_url(
                item,
                doi,
            ),
            authors=self._get_authors(
                item.get("author")
            ),
            publication_year=self._get_publication_year(
                item
            ),
            metadata={},
        )

    @staticmethod
    def _get_title(
        value: Any,
    ) -> str:
        """Return the primary Crossref title."""

        if not isinstance(value, list):
            raise TypeError(
                "Crossref title must be a list."
            )

        if not value:
            raise TypeError(
                "Crossref title list must not be empty."
            )

        title = value[0]

        if not isinstance(title, str):
            raise TypeError(
                "Crossref title must contain strings."
            )

        return title

    @staticmethod
    def _get_source_url(
        item: dict[str, Any],
        doi: str,
    ) -> str:
        """Return the preferred Crossref source URL."""

        url = item.get("URL")

        if isinstance(url, str):
            return url

        return f"https://doi.org/{doi}"

    @staticmethod
    def _get_authors(
        value: Any,
    ) -> tuple[str, ...]:
        """Return normalized Crossref author names."""

        if value is None:
            return ()

        if not isinstance(value, list):
            raise TypeError(
                "Crossref authors must be a list or null."
            )

        authors = []

        for author in value:
            if not isinstance(author, dict):
                raise TypeError(
                    "Crossref author must be a JSON object."
                )

            given = author.get("given")
            family = author.get("family")

            if given is not None and not isinstance(given, str):
                raise TypeError(
                    "Crossref author given name must be a string or null."
                )

            if family is not None and not isinstance(family, str):
                raise TypeError(
                    "Crossref author family name must be a string or null."
                )

            name_parts = tuple(
                part
                for part in (
                    given,
                    family,
                )
                if part
            )

            if name_parts:
                authors.append(
                    " ".join(name_parts)
                )

        return tuple(authors)

    def _get_publication_year(
        self,
        item: dict[str, Any],
    ) -> int | None:
        """Return the best available Crossref publication year."""

        for field_name in (
            "published-print",
            "published-online",
            "issued",
        ):
            year = self._get_date_year(
                item.get(field_name)
            )

            if year is not None:
                return year

        return None

    @staticmethod
    def _get_date_year(
        value: Any,
    ) -> int | None:
        """Return a year from a Crossref date-parts object."""

        if value is None:
            return None

        if not isinstance(value, dict):
            raise TypeError(
                "Crossref date value must be a JSON object or null."
            )

        date_parts = value.get("date-parts")

        if not isinstance(date_parts, list):
            raise TypeError(
                "Crossref date-parts must be a list."
            )

        if not date_parts:
            return None

        first_part = date_parts[0]

        if not isinstance(first_part, list):
            raise TypeError(
                "Crossref date-parts entry must be a list."
            )

        if not first_part:
            return None

        year = first_part[0]

        if not isinstance(year, int):
            raise TypeError(
                "Crossref publication year must be an integer."
            )

        return year

    @staticmethod
    def _get_required_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string response field."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                f"Crossref {field_name} must be a string."
            )

        return value
