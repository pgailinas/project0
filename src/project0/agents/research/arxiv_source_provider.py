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
import re
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

        arxiv_ids = self._extract_arxiv_ids(strategy)
        query = self._build_query(strategy)

        if not query and not arxiv_ids:
            return ()

        params = (
            {
                "id_list": ",".join(arxiv_ids),
                "max_results": min(
                    self.max_results,
                    len(arxiv_ids),
                ),
            }
            if arxiv_ids
            else {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": self.max_results,
            }
        )

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
    def _extract_arxiv_ids(
        strategy: ResearchStrategy,
    ) -> tuple[str, ...]:
        """Extract exact arXiv identifiers from provider search terms."""

        identifiers: list[str] = []
        pattern = re.compile(
            r"(?:https?://(?:www\.)?arxiv\.org/"
            r"(?:abs|html|pdf)/|arxiv\s*:\s*)?"
            r"(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?",
            flags=re.IGNORECASE,
        )

        for term in strategy.search_terms:
            match = pattern.fullmatch(term.strip())

            if match is None:
                continue

            identifier = match.group(1)

            if identifier not in identifiers:
                identifiers.append(identifier)

        return tuple(identifiers)

    @staticmethod
    def _build_query(
        strategy: ResearchStrategy,
    ) -> str:
        """Build deterministic arXiv query text."""

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

            abstract = " ".join(
                entry.findtext(
                    "atom:summary",
                    default="",
                    namespaces=namespace,
                ).split()
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

            document_url = None

            for link in entry.findall(
                "atom:link",
                namespace,
            ):
                if link.get("title") == "pdf":
                    href = link.get("href")

                    if isinstance(href, str):
                        document_url = href

                    break

            metadata = {}

            if abstract:
                metadata["abstract"] = abstract

            if document_url is not None:
                metadata["document_url"] = document_url

            references.append(
                ResearchSourceReference(
                    source_name="arxiv",
                    source_id=paper_id,
                    title=title,
                    source_url=paper_id,
                    authors=authors,
                    publication_year=year,
                    metadata=metadata,
                )
            )

        return tuple(references)
