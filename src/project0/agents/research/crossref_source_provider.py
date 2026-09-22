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
from project0.config.settings import SETTINGS
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
    maximum_retry_delay_seconds: float = 30.0
    user_agent: str = "Project0 Research Agent"
    mailto: str | None = SETTINGS.crossref_contact_email

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
                LOGGER.debug(
                    "Skipping incomplete Crossref search result: %s",
                    error,
                )

        return tuple(references)

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the delay before retrying a Crossref request."""

        maximum_delay = max(
            self.maximum_retry_delay_seconds,
            0.0,
        )

        if isinstance(
            error,
            httpx.HTTPStatusError,
        ):
            retry_after = error.response.headers.get(
                "Retry-After"
            )

            if retry_after is not None:
                try:
                    delay = float(retry_after)
                except ValueError:
                    pass
                else:
                    return min(
                        max(delay, 0.0),
                        maximum_delay,
                    )

        return min(
            max(
                self.retry_delay_seconds
                * (2 ** (attempt - 1)),
                0.0,
            ),
            maximum_delay,
        )

    @staticmethod
    def _build_query(
        strategy: ResearchStrategy,
    ) -> str:
        """Build deterministic Crossref query text."""

        terms = []

        for term in strategy.search_terms:
            normalized = " ".join(
                term.split()[:8]
            ).strip()

            if normalized and normalized not in terms:
                terms.append(normalized)

            if len(terms) >= 4:
                break

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
            title=self._get_title(item),
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
            metadata=self._get_metadata(
                item,
                doi,
            ),
        )

    @staticmethod
    def _get_title(
        item: dict[str, Any],
    ) -> str:
        """Return the primary Crossref title."""

        value = item.get("title")

        if value is None:
            for field_name in (
                "subtitle",
                "original-title",
                "short-title",
                "container-title",
            ):
                fallback = item.get(field_name)
                if isinstance(fallback, str) and fallback.strip():
                    return fallback.strip()
                if (
                    isinstance(fallback, list)
                    and fallback
                    and isinstance(fallback[0], str)
                    and fallback[0].strip()
                ):
                    return fallback[0].strip()

        if isinstance(value, str):
            if not value.strip():
                raise TypeError(
                    "Crossref title must not be empty."
                )

            return value.strip()

        if not isinstance(value, list):
            raise TypeError(
                "Crossref title must be a list or string; "
                f"received {type(value).__name__}."
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

        if not title.strip():
            raise TypeError(
                "Crossref title must not be empty."
            )

        return title.strip()

    def _get_metadata(
        self,
        item: dict[str, Any],
        doi: str,
    ) -> dict[str, Any]:
        """Return acquisition metadata from a Crossref result."""

        metadata: dict[str, Any] = {
            "doi": doi,
        }

        links = item.get(
            "link"
        )

        if isinstance(links, list):
            for link in links:
                if not isinstance(link, dict):
                    continue

                if link.get("content-type") != "application/pdf":
                    continue

                document_url = link.get(
                    "URL"
                )

                if isinstance(document_url, str):
                    metadata["document_url"] = document_url
                    break

        return metadata

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
            return None

        date_parts = value.get("date-parts")

        if not isinstance(date_parts, list):
            return None

        if not date_parts:
            return None

        first_part = date_parts[0]

        if not isinstance(first_part, list):
            return None

        if not first_part:
            return None

        year = first_part[0]

        if not isinstance(year, int):
            return None

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
