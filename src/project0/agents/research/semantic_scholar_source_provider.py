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
class SemanticScholarSourceProvider(
    ResearchSourceProviderProtocol,
):
    """Search Semantic Scholar for research references."""

    semantic_scholar_base_url: str = (
        "https://api.semanticscholar.org/graph/v1"
    )
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

        headers = {
            "User-Agent": self.user_agent,
        }

        if self.api_key is not None:
            headers["x-api-key"] = self.api_key

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

            if attempt < self.maximum_attempts:
                LOGGER.warning(
                    "Semantic Scholar request attempt %d of %d "
                    "failed: %s",
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
            if isinstance(
                last_error,
                httpx.HTTPStatusError,
            ):
                raise RuntimeError(
                    "Semantic Scholar request failed with HTTP status "
                    f"{last_error.response.status_code}."
                ) from last_error

            raise RuntimeError(
                "Semantic Scholar service could not be reached: "
                f"{type(last_error).__name__}: {last_error}"
            ) from last_error

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

        if (
            data is None
            and response_data.get("total") == 0
        ):
            return ()

        if not isinstance(data, list):
            raise TypeError(
                "Semantic Scholar response did not include a data list."
            )

        references = [
            self._build_reference(item)
            for item in data
        ]

        return tuple(references)

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the delay before retrying a Semantic Scholar request."""

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
