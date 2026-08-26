# ============================================================
# Project0 - arXiv Research Source Provider
#
# File: arxiv_source_provider.py
#
# Purpose:
#     Provide research paper search capability using the
#     arXiv public API.
#
#     This is the first-pass implementation of an external
#     Research Agent source provider.
#
# ============================================================

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET

import httpx

from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


ARXIV_API_URL = (
    "https://export.arxiv.org/api/query"
)


class ArxivSourceProvider:
    """Research source provider backed by arXiv."""

    def __init__(
        self,
        timeout_seconds: float = 60.0,
        max_results: int = 10,
        maximum_attempts: int = 3,
        retry_delay_seconds: float = 1.0,
        user_agent: str = "Project0 Research Agent",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results
        self.maximum_attempts = maximum_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.user_agent = user_agent

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search arXiv using strategy search terms."""

        query = self._build_query(strategy)

        if not query:
            return ()

        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": self.max_results,
        }

        headers = {
            "User-Agent": self.user_agent,
        }

        last_error: httpx.HTTPError | None = None

        for attempt in range(
            1,
            self.maximum_attempts + 1,
        ):
            try:
                response = httpx.get(
                    ARXIV_API_URL,
                    params=params,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                response.raise_for_status()

                return self._parse_response(
                    response.text
                )

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
                    "arXiv request attempt %d of %d failed: %s",
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

        LOGGER.error(
            "arXiv request failed after %d attempt(s): %s",
            self.maximum_attempts,
            last_error,
        )

        raise RuntimeError(
            "arXiv request failed."
        ) from last_error

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the delay before retrying an arXiv request."""

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
        """Build deterministic arXiv query text."""

        terms = []

        for term in strategy.search_terms:
            normalized = term.strip()

            if normalized and normalized not in terms:
                terms.append(normalized)

        return " ".join(terms)

    @staticmethod
    def _parse_response(
        xml_text: str,
    ) -> tuple[ResearchSourceReference, ...]:
        """Parse arXiv Atom XML response."""

        namespace = {
            "atom": (
                "http://www.w3.org/2005/Atom"
            )
        }

        root = ET.fromstring(xml_text)

        references = []

        for entry in root.findall(
            "atom:entry",
            namespace,
        ):
            paper_id = (
                entry.findtext(
                    "atom:id",
                    default="",
                    namespaces=namespace,
                )
            )

            title = (
                entry.findtext(
                    "atom:title",
                    default="",
                    namespaces=namespace,
                )
                .replace("\n", " ")
                .strip()
            )

            published = (
                entry.findtext(
                    "atom:published",
                    default="",
                    namespaces=namespace,
                )
            )

            year = None

            if published:
                try:
                    year = int(
                        published[:4]
                    )
                except ValueError:
                    year = None

            authors = tuple(
                author.findtext(
                    "atom:name",
                    default="",
                    namespaces=namespace,
                )
                for author in entry.findall(
                    "atom:author",
                    namespace,
                )
            )

            references.append(
                ResearchSourceReference(
                    source_name="arxiv",
                    source_id=paper_id,
                    title=title,
                    source_url=paper_id,
                    authors=authors,
                    publication_year=year,
                    metadata={},
                )
            )

        return tuple(references)
