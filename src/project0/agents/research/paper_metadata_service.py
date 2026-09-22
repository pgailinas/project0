# ============================================================
# Project0 - Paper Metadata Service
#
# File: paper_metadata_service.py
#
# Purpose:
#     Retrieve and normalize paper metadata from supported
#     external research sources for Research Agent workflows.
#
# ============================================================

from __future__ import annotations

import logging
import re
import time
from urllib.parse import urlsplit, urlunsplit
from dataclasses import dataclass, field, replace
from io import BytesIO
from typing import Any

import httpx

from project0.config.settings import SETTINGS
from project0.models.research_models import (
    PaperMetadata,
    ResearchPaperEvidenceSection,
    ResearchPaperEvidenceStatus,
    ResearchSourceReference,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PaperMetadataService:
    """Retrieve paper metadata from supported research sources."""

    semantic_scholar_base_url: str = (
        "https://api.semanticscholar.org/graph/v1"
    )
    semantic_scholar_api_key: str | None = field(
        default_factory=lambda: SETTINGS.semantic_scholar_api_key,
    )
    timeout_seconds: float = 30.0
    maximum_attempts: int = 3
    retry_delay_seconds: float = 1.0
    maximum_retry_delay_seconds: float = 30.0
    user_agent: str = "Project0 Research Agent"
    evidence_candidate_limit: int = 8
    maximum_evidence_characters: int = 24000

    def retrieve_metadata(
        self,
        references: tuple[ResearchSourceReference, ...],
    ) -> tuple[PaperMetadata, ...]:
        """Retrieve metadata for research source references."""

        papers: list[PaperMetadata] = []

        for reference in references:
            if reference.source_name == "semantic_scholar":
                papers.append(
                    self._retrieve_semantic_scholar_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "arxiv":
                papers.append(
                    self._create_arxiv_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "openalex":
                papers.append(
                    self._create_openalex_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "openreview":
                papers.append(
                    self._create_openreview_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "crossref":
                papers.append(
                    self._create_crossref_metadata(
                        reference
                    )
                )
                continue

            if reference.source_name == "stub":
                papers.append(
                    self._create_stub_metadata(
                        reference
                    )
                )
                continue

            raise ValueError(
                "Unsupported research metadata source: "
                f"{reference.source_name}"
            )

        return tuple(papers)

    def acquire_evidence(
        self,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[PaperMetadata, ...]:
        """Acquire bounded evidence for a ranked paper shortlist."""

        if self.evidence_candidate_limit < 1:
            raise ValueError(
                "Evidence candidate limit must be at least 1."
            )

        return tuple(
            self._acquire_paper_evidence(paper)
            for paper in papers[:self.evidence_candidate_limit]
        )

    def _acquire_paper_evidence(
        self,
        paper: PaperMetadata,
    ) -> PaperMetadata:
        """Acquire authoritative abstract or PDF evidence for one paper."""

        sections: list[ResearchPaperEvidenceSection] = []
        authoritative_title: str | None = None

        if paper.abstract is not None and paper.abstract.strip():
            sections.append(
                ResearchPaperEvidenceSection(
                    section="Abstract",
                    content=paper.abstract.strip(),
                )
            )

        pdf_url = self._paper_pdf_url(paper)

        if pdf_url is not None:
            try:
                authoritative_title, pdf_sections = (
                    self._retrieve_pdf_evidence(pdf_url)
                )
                sections.extend(pdf_sections)
            except (
                httpx.HTTPError,
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
            ) as error:
                LOGGER.warning(
                    "Paper evidence request failed for paper %s; "
                    "using available abstract evidence: %s",
                    paper.source_reference.source_id,
                    error,
                )

        sections = list(
            dict.fromkeys(sections)
        )
        status = (
            ResearchPaperEvidenceStatus.AVAILABLE
            if sections
            else ResearchPaperEvidenceStatus.DISCOVERY_ONLY
        )

        title = paper.title
        source_reference = paper.source_reference
        if (
            authoritative_title is not None
            and self._uses_fallback_seed_title(paper)
        ):
            title = authoritative_title
            source_reference = replace(
                source_reference,
                title=authoritative_title,
            )

        return replace(
            paper,
            source_reference=source_reference,
            title=title,
            evidence_status=status,
            evidence_sections=tuple(sections),
        )

    def _retrieve_pdf_evidence(
        self,
        pdf_url: str,
    ) -> tuple[
        str | None,
        tuple[ResearchPaperEvidenceSection, ...],
    ]:
        """Retrieve authoritative PDF title and bounded paper evidence."""

        response = httpx.get(
            pdf_url,
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout_seconds,
            follow_redirects=True,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type and not response.content.startswith(b"%PDF"):
            raise ValueError("Paper evidence response was not a PDF.")

        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError(
                "PDF evidence extraction requires pypdf."
            ) from error

        reader = PdfReader(BytesIO(response.content))
        document_title = self._normalize_pdf_document_title(
            getattr(reader.metadata, "title", None)
            if reader.metadata is not None
            else None
        )
        pages = tuple(
            (page_number, (page.extract_text() or "").strip())
            for page_number, page in enumerate(
                reader.pages,
                start=1,
            )
        )
        return document_title, self._extract_evidence_sections(pages)

    @staticmethod
    def _uses_fallback_seed_title(paper: PaperMetadata) -> bool:
        """Return whether a canonical seed still has its placeholder title."""

        return (
            paper.source_reference.metadata.get("seed_resolution")
            == "canonical_fallback"
            and re.fullmatch(
                r"arxiv:\d{4}\.\d{4,5}",
                paper.title.strip(),
                flags=re.IGNORECASE,
            )
            is not None
        )

    @staticmethod
    def _normalize_pdf_document_title(value: object) -> str | None:
        """Normalize a usable authoritative PDF document title."""

        if not isinstance(value, str):
            return None

        title = " ".join(value.split()).strip()
        if (
            not title
            or len(title) > 500
            or title.casefold() in {"untitled", "unknown"}
            or re.fullmatch(
                r"(?:arxiv:)?\d{4}\.\d{4,5}(?:v\d+)?(?:\.pdf)?",
                title,
                flags=re.IGNORECASE,
            )
            is not None
        ):
            return None

        return title

    def _extract_evidence_sections(
        self,
        pages: tuple[tuple[int, str], ...],
    ) -> tuple[ResearchPaperEvidenceSection, ...]:
        """Extract bounded evidence from relevant paper sections."""

        headings = {
            "Abstract": re.compile(r"(?im)^\s*abstract\s*$"),
            "Method": re.compile(
                r"(?im)^\s*(?:\d+(?:\.\d+)*\s+)?"
                r"(?:method|methodology|approach|model)\s*$"
            ),
            "Results": re.compile(
                r"(?im)^\s*(?:\d+(?:\.\d+)*\s+)?"
                r"(?:experiments?|results?|evaluation)\s*$"
            ),
        }
        sections: list[ResearchPaperEvidenceSection] = []
        remaining = max(self.maximum_evidence_characters, 0)

        for section_name, heading_pattern in headings.items():
            for page_number, text in pages:
                match = heading_pattern.search(text)
                if match is None:
                    continue

                content = text[match.end():].strip()
                if not content:
                    continue

                content = content[:min(remaining, 8000)].strip()
                if content:
                    sections.append(
                        ResearchPaperEvidenceSection(
                            section=section_name,
                            content=content,
                            page_number=page_number,
                        )
                    )
                    remaining -= len(content)
                break

            if remaining <= 0:
                break

        return tuple(sections)

    @staticmethod
    def _paper_pdf_url(paper: PaperMetadata) -> str | None:
        """Return an authoritative PDF URL when source metadata provides one."""

        for key in ("open_access_pdf_url", "pdf_url"):
            for metadata in (
                paper.metadata,
                paper.source_reference.metadata,
            ):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return PaperMetadataService._normalize_openreview_pdf_url(
                        value.strip(), paper.source_reference.source_name
                    )

        source_url = paper.source_url or paper.source_reference.source_url
        if (
            paper.source_reference.source_name == "arxiv"
            and isinstance(source_url, str)
            and "/abs/" in source_url
        ):
            return source_url.replace("/abs/", "/pdf/", 1)

        return None

    @staticmethod
    def _normalize_openreview_pdf_url(url: str, source_name: str) -> str:
        """Use OpenReview's public PDF host for downloadable evidence.

        OpenReview search results may return the API host (api2.openreview.net),
        whose PDF route rejects anonymous evidence requests with 403. The
        public host serves the same note PDF and keeps abstract fallback intact.
        """
        if source_name != "openreview":
            return url
        parsed = urlsplit(url)
        if parsed.hostname != "api2.openreview.net":
            return url
        return urlunsplit(("https", "openreview.net", parsed.path, parsed.query, parsed.fragment))

    def _retrieve_semantic_scholar_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Retrieve paper metadata from Semantic Scholar."""

        endpoint = (
            f"{self.semantic_scholar_base_url.rstrip('/')}"
            f"/paper/{reference.source_id}"
        )

        params = {
            "fields": (
                "paperId,title,authors,year,abstract,"
                "venue,externalIds,url,openAccessPdf"
            ),
        }

        LOGGER.debug(
            "Semantic Scholar metadata request endpoint=%s "
            "paper_id=%s",
            endpoint,
            reference.source_id,
        )

        headers = {
            "User-Agent": self.user_agent,
        }

        if self.semantic_scholar_api_key is not None:
            headers["x-api-key"] = self.semantic_scholar_api_key

        last_error: httpx.HTTPError | None = None
        response: httpx.Response | None = None

        for attempt in range(1, self.maximum_attempts + 1):
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

                if status_code != 429 and status_code < 500:
                    break

            except httpx.RequestError as error:
                last_error = error

            if attempt < self.maximum_attempts:
                LOGGER.warning(
                    "Semantic Scholar metadata request attempt %d of %d "
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

        if response is None or response.is_error:
            LOGGER.warning(
                "Semantic Scholar metadata request failed for paper %s; "
                "using source-search metadata.",
                reference.source_id,
            )
            return self._create_semantic_scholar_metadata(reference)

        try:
            response_data = response.json()
        except ValueError as error:
            raise ValueError(
                "Semantic Scholar metadata response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "Semantic Scholar metadata response must be a JSON object."
            )

        paper_id = self._get_required_string(
            response_data,
            "paperId",
        )

        if paper_id != reference.source_id:
            raise ValueError(
                "Semantic Scholar metadata response paperId did not "
                "match the requested source identifier."
            )

        title = self._get_required_string(
            response_data,
            "title",
        )

        authors = self._get_authors(
            response_data.get("authors")
        )

        publication_year = self._get_optional_int(
            response_data,
            "year",
        )

        abstract = self._get_optional_string(
            response_data,
            "abstract",
        )

        venue = self._get_optional_string(
            response_data,
            "venue",
        )

        source_url = self._get_optional_string(
            response_data,
            "url",
        )

        doi = self._get_doi(
            response_data.get("externalIds")
        )
        open_access_pdf_url = self._get_open_access_pdf_url(
            response_data.get("openAccessPdf")
        )

        return PaperMetadata(
            source_reference=reference,
            title=title,
            authors=authors,
            publication_year=publication_year,
            abstract=abstract,
            venue=venue,
            doi=doi,
            source_url=source_url,
            metadata={
                "paper_id": paper_id,
                **(
                    {"open_access_pdf_url": open_access_pdf_url}
                    if open_access_pdf_url is not None
                    else {}
                ),
            },
        )

    def _retry_delay_seconds(
        self,
        attempt: int,
        error: httpx.HTTPError | None,
    ) -> float:
        """Return the bounded delay before a metadata retry."""

        maximum_delay = max(
            self.maximum_retry_delay_seconds,
            0.0,
        )

        if isinstance(error, httpx.HTTPStatusError):
            retry_after = error.response.headers.get("Retry-After")

            if retry_after is not None:
                try:
                    delay = float(retry_after)
                except ValueError:
                    pass
                else:
                    return min(max(delay, 0.0), maximum_delay)

        return min(
            max(
                self.retry_delay_seconds * (2 ** (attempt - 1)),
                0.0,
            ),
            maximum_delay,
        )

    def _create_semantic_scholar_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from a Semantic Scholar search result."""

        abstract = reference.metadata.get("abstract")
        venue = reference.metadata.get("venue")
        doi = reference.metadata.get("doi")

        for field_name, value in (
            ("abstract", abstract),
            ("venue", venue),
            ("doi", doi),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(
                    "Semantic Scholar reference "
                    f"{field_name} metadata must be a string or null."
                )

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=abstract,
            venue=venue or "Semantic Scholar",
            doi=doi,
            source_url=reference.source_url,
            metadata={
                **self._create_source_metadata(
                    reference,
                    "semantic_scholar",
                ),
                "metadata_fallback": True,
            },
        )

    def _create_arxiv_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized arXiv source data."""

        abstract = self._get_reference_optional_string(
            reference,
            "abstract",
        )

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=abstract,
            venue="arXiv",
            source_url=reference.source_url,
            metadata=self._create_source_metadata(reference, "arxiv"),
        )

    def _create_openalex_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized OpenAlex source data."""

        abstract = reference.metadata.get("abstract")

        if abstract is not None and not isinstance(abstract, str):
            raise TypeError(
                "OpenAlex reference abstract metadata must be a string or null."
            )

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=abstract,
            venue="OpenAlex",
            source_url=reference.source_url,
            metadata=self._create_source_metadata(reference, "openalex"),
        )

    def _create_openreview_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized OpenReview source data."""

        abstract = self._get_reference_optional_string(
            reference,
            "abstract",
        )

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=abstract,
            venue="OpenReview",
            source_url=reference.source_url,
            metadata=self._create_source_metadata(reference, "openreview"),
        )

    def _create_crossref_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create metadata from normalized Crossref source data."""

        abstract = self._get_reference_optional_string(
            reference,
            "abstract",
        )

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=abstract,
            venue="Crossref",
            doi=reference.source_id,
            source_url=reference.source_url,
            metadata=self._create_source_metadata(reference, "crossref"),
        )

    @staticmethod
    def _get_reference_optional_string(
        reference: ResearchSourceReference,
        field_name: str,
    ) -> str | None:
        """Return validated optional string metadata from a source result."""

        value = reference.metadata.get(field_name)
        if value is not None and not isinstance(value, str):
            raise TypeError(
                f"{reference.source_name} reference {field_name} metadata "
                "must be a string or null."
            )
        return value

    @staticmethod
    def _create_source_metadata(
        reference: ResearchSourceReference,
        source_name: str,
    ) -> dict[str, Any]:
        """Preserve authoritative evidence locations from source metadata."""

        metadata: dict[str, Any] = {
            "paper_id": reference.source_id,
            "source": source_name,
        }
        for key in ("open_access_pdf_url", "pdf_url"):
            value = reference.metadata.get(key)
            if isinstance(value, str) and value.strip():
                metadata[key] = value.strip()
        return metadata

    def _create_stub_metadata(
        self,
        reference: ResearchSourceReference,
    ) -> PaperMetadata:
        """Create deterministic metadata for stub research sources."""

        return PaperMetadata(
            source_reference=reference,
            title=reference.title,
            authors=reference.authors,
            publication_year=reference.publication_year,
            abstract=(
                "A learned video encoder aligns its representations with "
                "a frozen CLIP vision-language teacher through feature "
                "matching in the shared embedding space."
            ),
            venue="Project0 Research Stub",
            source_url=reference.source_url,
            metadata={
                "paper_id": reference.source_id,
                "source": "stub",
            },
        )

    def _get_authors(
        self,
        value: Any,
    ) -> tuple[str, ...]:
        """Return normalized Semantic Scholar author names."""

        if value is None:
            return ()

        if not isinstance(value, list):
            raise TypeError(
                "Semantic Scholar metadata authors must be a list or null."
            )

        authors: list[str] = []

        for author in value:
            if not isinstance(author, dict):
                raise TypeError(
                    "Semantic Scholar metadata author must be a JSON object."
                )

            name = author.get("name")

            if not isinstance(name, str):
                raise TypeError(
                    "Semantic Scholar metadata author name must be a string."
                )

            authors.append(name)

        return tuple(authors)

    def _get_doi(
        self,
        value: Any,
    ) -> str | None:
        """Return a DOI from Semantic Scholar external identifiers."""

        if value is None:
            return None

        if not isinstance(value, dict):
            raise TypeError(
                "Semantic Scholar externalIds must be a JSON object or null."
            )

        doi = value.get("DOI")

        if doi is None:
            return None

        if not isinstance(doi, str):
            raise TypeError(
                "Semantic Scholar DOI must be a string or null."
            )

        return doi

    @staticmethod
    def _get_open_access_pdf_url(
        value: Any,
    ) -> str | None:
        """Return a Semantic Scholar open-access PDF URL."""

        if value is None:
            return None

        if not isinstance(value, dict):
            raise TypeError(
                "Semantic Scholar openAccessPdf must be an object or null."
            )

        url = value.get("url")
        if url is None:
            return None
        if not isinstance(url, str):
            raise TypeError(
                "Semantic Scholar openAccessPdf URL must be a string or null."
            )

        return url

    @staticmethod
    def _get_required_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string response field."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                "Semantic Scholar metadata "
                f"{field_name} must be a string."
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
                "Semantic Scholar metadata "
                f"{field_name} must be a string or null."
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
                "Semantic Scholar metadata "
                f"{field_name} must be an integer or null."
            )

        return value
