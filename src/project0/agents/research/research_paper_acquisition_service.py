# ============================================================
# Project0 - Research Paper Acquisition Service
#
# File: research_paper_acquisition_service.py
#
# Purpose:
#     Acquire accessible full-text PDF content for retained
#     Research Agent papers.
#
# ============================================================

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from project0.models.research_models import (
    PaperMetadata,
    ResearchPaperAcquisition,
    ResearchPaperAcquisitionStatus,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ResearchPaperAcquisitionService:
    """Acquire accessible full-text PDF content for retained papers."""

    timeout_seconds: float = 30.0
    maximum_attempts: int = 3
    retry_delay_seconds: float = 1.0
    user_agent: str = "Project0 Research Agent"

    def acquire(
        self,
        paper: PaperMetadata,
    ) -> ResearchPaperAcquisition:
        """Acquire accessible full-text PDF content for one paper."""

        candidate_urls = self._get_candidate_urls(
            paper
        )

        if not candidate_urls:
            return ResearchPaperAcquisition(
                paper=paper,
                source_url=None,
                content=None,
                acquisition_status=(
                    ResearchPaperAcquisitionStatus.UNAVAILABLE
                ),
                warnings=(
                    "No full-text acquisition URL was available.",
                ),
            )

        warnings: list[str] = []

        for candidate_url in candidate_urls:
            response = self._retrieve_candidate(
                candidate_url
            )

            if response is None:
                warnings.append(
                    "Full-text PDF was not available from "
                    f"{candidate_url}."
                )
                continue

            content_type = response.headers.get(
                "Content-Type"
            )

            if not self._is_pdf_content_type(
                content_type
            ):
                warnings.append(
                    "Full-text candidate did not return PDF "
                    f"content: {candidate_url}."
                )
                continue

            if not response.content.startswith(
                b"%PDF-"
            ):
                warnings.append(
                    "Full-text candidate did not contain a valid "
                    f"PDF signature: {candidate_url}."
                )
                continue

            return ResearchPaperAcquisition(
                paper=paper,
                source_url=str(response.url),
                content=response.content,
                acquisition_status=(
                    ResearchPaperAcquisitionStatus.ACQUIRED
                ),
                content_type=content_type,
                warnings=tuple(warnings),
            )

        return ResearchPaperAcquisition(
            paper=paper,
            source_url=None,
            content=None,
            acquisition_status=(
                ResearchPaperAcquisitionStatus.UNAVAILABLE
            ),
            warnings=tuple(warnings),
        )

    def _retrieve_candidate(
        self,
        candidate_url: str,
    ) -> httpx.Response | None:
        """Retrieve one candidate full-text document."""

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
                    candidate_url,
                    headers=headers,
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                )

                if response.status_code in {
                    401,
                    403,
                    404,
                    410,
                }:
                    return None

                response.raise_for_status()

                return response

            except httpx.HTTPStatusError as error:
                last_error = error
                status_code = error.response.status_code

                if (
                    status_code != 429
                    and status_code < 500
                ):
                    return None

            except httpx.RequestError as error:
                last_error = error

            if attempt < self.maximum_attempts:
                LOGGER.warning(
                    "Research paper acquisition attempt %d of %d "
                    "failed for %s: %s",
                    attempt,
                    self.maximum_attempts,
                    candidate_url,
                    last_error,
                )

                time.sleep(
                    self.retry_delay_seconds
                    * (2 ** (attempt - 1))
                )

        raise RuntimeError(
            "Research paper acquisition request failed."
        ) from last_error

    @staticmethod
    def _get_candidate_urls(
        paper: PaperMetadata,
    ) -> tuple[str, ...]:
        """Return deterministic candidate URLs for full-text acquisition."""

        candidate_urls: list[str] = []

        for metadata in (
            paper.metadata,
            paper.source_reference.metadata,
        ):
            document_url = metadata.get(
                "document_url"
            )

            if (
                isinstance(document_url, str)
                and document_url
                and document_url not in candidate_urls
            ):
                candidate_urls.append(
                    document_url
                )

        doi = paper.doi

        if doi is None:
            for metadata in (
                paper.metadata,
                paper.source_reference.metadata,
            ):
                metadata_doi = metadata.get(
                    "doi"
                )

                if isinstance(metadata_doi, str):
                    doi = metadata_doi
                    break

        if isinstance(doi, str) and doi:
            doi_url = (
                doi
                if doi.startswith(
                    ("http://", "https://")
                )
                else f"https://doi.org/{doi}"
            )

            if doi_url not in candidate_urls:
                candidate_urls.append(
                    doi_url
                )

        if (
            isinstance(paper.source_url, str)
            and paper.source_url
            and paper.source_url not in candidate_urls
        ):
            candidate_urls.append(
                paper.source_url
            )

        return tuple(candidate_urls)

    @staticmethod
    def _is_pdf_content_type(
        content_type: str | None,
    ) -> bool:
        """Return whether an HTTP content type identifies PDF content."""

        if content_type is None:
            return False

        media_type = content_type.split(
            ";",
            maxsplit=1,
        )[0].strip().lower()

        return media_type == "application/pdf"
