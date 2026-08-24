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
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results

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

        try:
            response = httpx.get(
                ARXIV_API_URL,
                params=params,
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.HTTPError as error:
            LOGGER.error(
                "arXiv request failed: %s",
                error,
            )
            raise RuntimeError(
                "arXiv request failed."
            ) from error

        return self._parse_response(
            response.text
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
