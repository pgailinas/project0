# ============================================================
# Project0 - OpenAlex Research Source Provider
#
# File: openalex_source_provider.py
#
# Purpose:
#     Implement OpenAlex research source provider used by
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
class OpenAlexSourceProvider(
    ResearchSourceProviderProtocol,
):
    """Search OpenAlex for research references."""

    openalex_base_url: str = "https://api.openalex.org"
    timeout_seconds: float = 30.0
    maximum_results: int = 10
    maximum_attempts: int = 3
    retry_delay_seconds: float = 1.0
    user_agent: str = "Project0 Research Agent"
    api_key: str | None = None

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search OpenAlex for references."""

        query = self._build_query(strategy)

        if not query:
            return ()

        endpoint = (
            f"{self.openalex_base_url.rstrip('/')}"
            "/works"
        )

        params: dict[str, Any] = {
            "search": query,
            "per_page": self.maximum_results,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        headers = {
            "User-Agent": self.user_agent,
        }

        LOGGER.debug(
            "OpenAlex request endpoint=%s query=%s limit=%d",
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
                    "OpenAlex request attempt %d of %d failed: %s",
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
                "OpenAlex request failed."
            ) from last_error

        try:
            response_data = response.json()

        except ValueError as error:
            raise ValueError(
                "OpenAlex response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "OpenAlex response must be a JSON object."
            )

        results = response_data.get("results")

        if not isinstance(results, list):
            raise TypeError(
                "OpenAlex response did not include a results list."
            )

        references = [
            self._build_reference(item)
            for item in results
        ]

        return tuple(references)

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the delay before retrying an OpenAlex request."""

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
        """Build deterministic OpenAlex query text."""

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
        """Normalize one OpenAlex search result."""

        if not isinstance(item, dict):
            raise TypeError(
                "OpenAlex search result must be a JSON object."
            )

        return ResearchSourceReference(
            source_name="openalex",
            source_id=self._get_required_string(
                item,
                "id",
            ),
            title=self._get_required_string(
                item,
                "title",
            ),
            source_url=self._get_source_url(
                item,
            ),
            authors=self._get_authors(
                item.get("authorships")
            ),
            publication_year=self._get_optional_int(
                item,
                "publication_year",
            ),
            metadata=self._get_metadata(
                item,
            ),
        )

    def _get_metadata(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        """Return acquisition metadata from an OpenAlex result."""

        metadata: dict[str, Any] = {}

        primary_location = item.get(
            "primary_location"
        )

        if isinstance(primary_location, dict):
            document_url = primary_location.get(
                "pdf_url"
            )

            if isinstance(document_url, str):
                metadata["document_url"] = document_url

        doi = item.get(
            "doi"
        )

        if isinstance(doi, str):
            metadata["doi"] = doi

        return metadata

    def _get_source_url(
        self,
        item: dict[str, Any],
    ) -> str | None:
        """Return the preferred OpenAlex source URL."""

        primary_location = item.get(
            "primary_location"
        )

        if isinstance(primary_location, dict):
            landing_page_url = (
                primary_location.get(
                    "landing_page_url"
                )
            )

            if isinstance(
                landing_page_url,
                str,
            ):
                return landing_page_url

        doi = item.get("doi")

        if isinstance(doi, str):
            return doi

        return self._get_optional_string(
            item,
            "id",
        )

    def _get_authors(
        self,
        value: Any,
    ) -> tuple[str, ...]:
        """Return normalized OpenAlex author names."""

        if value is None:
            return ()

        if not isinstance(value, list):
            raise TypeError(
                "OpenAlex authorships must be a list or null."
            )

        authors = []

        for authorship in value:
            if not isinstance(
                authorship,
                dict,
            ):
                raise TypeError(
                    "OpenAlex authorship must be a JSON object."
                )

            author = authorship.get(
                "author"
            )

            if not isinstance(
                author,
                dict,
            ):
                raise TypeError(
                    "OpenAlex author must be a JSON object."
                )

            name = author.get(
                "display_name"
            )

            if not isinstance(
                name,
                str,
            ):
                raise TypeError(
                    "OpenAlex author display_name must be a string."
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
                f"OpenAlex {field_name} must be a string."
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
                f"OpenAlex {field_name} must be a string or null."
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
                f"OpenAlex {field_name} must be an integer or null."
            )

        return value
