# ============================================================
# Project0 - OpenReview Research Source Provider
#
# File: openreview_source_provider.py
#
# Purpose:
#     Implement OpenReview research source provider used by
#     Project0 Research Agent source services.
#
# ============================================================

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
class OpenReviewSourceProvider(
    ResearchSourceProviderProtocol,
):
    """Search OpenReview for research references."""

    openreview_base_url: str = "https://api2.openreview.net"
    timeout_seconds: float = 30.0
    maximum_results: int = 10
    maximum_attempts: int = 3
    retry_delay_seconds: float = 1.0
    user_agent: str = "Project0 Research Agent"

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search OpenReview for references."""

        query = self._build_query(strategy)

        if not query:
            return ()

        endpoint = (
            f"{self.openreview_base_url.rstrip('/')}"
            "/notes/search"
        )

        params: dict[str, Any] = {
            "query": query,
            "content": "title",
            "source": "forum",
            "limit": self.maximum_results * 5,
        }

        headers = {
            "User-Agent": self.user_agent,
        }

        LOGGER.debug(
            "OpenReview request endpoint=%s query=%s limit=%d",
            endpoint,
            query,
            self.maximum_results * 5,
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
                    "OpenReview request attempt %d of %d failed: %s",
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
                "OpenReview request failed."
            ) from last_error

        try:
            response_data = response.json()

        except ValueError as error:
            raise ValueError(
                "OpenReview response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "OpenReview response must be a JSON object."
            )

        notes = response_data.get("notes")

        if not isinstance(notes, list):
            raise TypeError(
                "OpenReview response did not include a notes list."
            )

        references = [
            self._build_reference(note)
            for note in notes
            if self._is_submission_note(note)
        ]

        return tuple(
            references[:self.maximum_results]
        )

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the delay before retrying an OpenReview request."""

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
        """Build deterministic OpenReview query text."""

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
    def _is_submission_note(
        note: Any,
    ) -> bool:
        """Return whether an OpenReview note is a paper submission."""

        if not isinstance(note, dict):
            return False

        if note.get("replyto") is not None:
            return False

        invitations = note.get("invitations")

        if not isinstance(invitations, list):
            return False

        return any(
            isinstance(invitation, str)
            and "/-/Submission" in invitation
            for invitation in invitations
        )

    def _build_reference(
        self,
        note: Any,
    ) -> ResearchSourceReference:
        """Normalize one OpenReview search result."""

        if not isinstance(note, dict):
            raise TypeError(
                "OpenReview search result must be a JSON object."
            )

        note_id = self._get_required_string(
            note,
            "id",
        )

        content = note.get("content")

        if not isinstance(content, dict):
            raise TypeError(
                "OpenReview content must be a JSON object."
            )

        return ResearchSourceReference(
            source_name="openreview",
            source_id=note_id,
            title=self._get_content_string(
                content,
                "title",
            ),
            source_url=(
                f"https://openreview.net/forum?id={note_id}"
            ),
            authors=self._get_authors(
                content.get("authors")
            ),
            publication_year=self._get_publication_year(
                note
            ),
            metadata=self._get_metadata(
                content,
            ),
        )

    def _get_metadata(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        """Return acquisition metadata from an OpenReview result."""

        metadata: dict[str, Any] = {}

        abstract = content.get(
            "abstract"
        )

        if isinstance(abstract, dict):
            value = abstract.get(
                "value"
            )

            if isinstance(value, str):
                metadata["abstract"] = value

        pdf = content.get(
            "pdf"
        )

        if isinstance(pdf, dict):
            value = pdf.get(
                "value"
            )

            if isinstance(value, str):
                if value.startswith("http"):
                    metadata["pdf_url"] = value
                elif value.startswith("/"):
                    metadata["pdf_url"] = (
                        f"https://openreview.net{value}"
                    )

        return metadata

    def _get_content_string(
        self,
        content: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required OpenReview content string."""

        field = content.get(field_name)

        if not isinstance(field, dict):
            raise TypeError(
                f"OpenReview {field_name} must be a JSON object."
            )

        value = field.get("value")

        if not isinstance(value, str):
            raise TypeError(
                f"OpenReview {field_name} value must be a string."
            )

        return value

    def _get_authors(
        self,
        value: Any,
    ) -> tuple[str, ...]:
        """Return normalized OpenReview author names."""

        if value is None:
            return ()

        if not isinstance(value, dict):
            raise TypeError(
                "OpenReview authors must be a JSON object or null."
            )

        authors = value.get("value")

        if authors is None:
            return ()

        if not isinstance(authors, list):
            raise TypeError(
                "OpenReview authors value must be a list or null."
            )

        normalized_authors = []

        for author in authors:
            if not isinstance(author, str):
                raise TypeError(
                    "OpenReview author name must be a string."
                )

            normalized_authors.append(author)

        return tuple(normalized_authors)

    def _get_publication_year(
        self,
        note: dict[str, Any],
    ) -> int | None:
        """Return the best available OpenReview publication year."""

        for field_name in (
            "pdate",
            "cdate",
        ):
            value = note.get(field_name)

            if value is None:
                continue

            if not isinstance(value, int):
                raise TypeError(
                    f"OpenReview {field_name} must be an integer or null."
                )

            return datetime.fromtimestamp(
                value / 1000,
                tz=timezone.utc,
            ).year

        return None

    @staticmethod
    def _get_required_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string response field."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                f"OpenReview {field_name} must be a string."
            )

        return value
