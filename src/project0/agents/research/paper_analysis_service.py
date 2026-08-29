# ============================================================
# Project0 - Paper Analysis Service
#
# File: paper_analysis_service.py
#
# Purpose:
#     Analyze retained research papers into structured,
#     evidence-supported Research Agent paper analyses.
#
# ============================================================

from __future__ import annotations

import json
import logging
from typing import Any

from project0.interfaces.reasoning_interfaces import (
    ReasoningProviderProtocol,
)
from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.models.research_models import (
    PaperAnalysis,
    PaperMetadata,
    ResearchEvidenceReference,
    ResearchEvidenceSourceType,
    ResearchFinding,
    ResearchPaperAnalysisBasis,
    ResearchPaperDocument,
    ResearchRequest,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


class PaperAnalysisService:
    """Execute AI-assisted structured retained-paper analysis."""

    def __init__(
        self,
        provider: ReasoningProviderProtocol,
        model_name: str,
    ) -> None:
        """Initialize the retained-paper analysis dependencies."""

        self._provider = provider
        self._model_name = model_name

    def analyze(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
        paper_documents: tuple[ResearchPaperDocument, ...] = (),
    ) -> tuple[PaperAnalysis, ...]:
        """Analyze retained papers for a research request."""

        if not papers:
            return ()

        document_by_source_id = self._index_documents(
            papers=papers,
            paper_documents=paper_documents,
        )

        return tuple(
            self._analyze_paper(
                request=request,
                strategy=strategy,
                paper=paper,
                document=document_by_source_id.get(
                    paper.source_reference.source_id
                ),
            )
            for paper in papers
        )

    def _analyze_paper(
        self,
        *,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        paper: PaperMetadata,
        document: ResearchPaperDocument | None,
    ) -> PaperAnalysis:
        """Analyze one retained paper with one validation retry."""

        provider_request = self._build_provider_request(
            request=request,
            strategy=strategy,
            paper=paper,
            document=document,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_analysis(
                paper=paper,
                document=document,
                provider_response=provider_response,
            )
        except ValueError as error:
            if not self._is_retryable_analysis_error(
                error
            ):
                raise

            LOGGER.warning(
                "Paper analysis response failed structural or "
                "provenance validation; retrying once: %s",
                error,
            )

        provider_response = self._provider.generate(
            provider_request
        )

        return self._create_analysis(
            paper=paper,
            document=document,
            provider_response=provider_response,
        )

    def _build_provider_request(
        self,
        *,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        paper: PaperMetadata,
        document: ResearchPaperDocument | None,
    ) -> ProviderRequest:
        """Build a provider-neutral retained-paper analysis request."""

        source_id = paper.source_reference.source_id

        if document is not None:
            evidence_basis = {
                "analysis_basis": ResearchPaperAnalysisBasis.FULL_TEXT,
                "document_id": document.document_id,
                "pages": [
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                    }
                    for page in document.pages
                ],
            }
        else:
            evidence_basis = {
                "analysis_basis": (
                    ResearchPaperAnalysisBasis.ABSTRACT_METADATA
                ),
                "abstract": paper.abstract,
            }

        user_prompt = json.dumps(
            {
                "research_question": request.question,
                "guidance": request.guidance,
                "research_concepts": list(strategy.concepts),
                "paper": {
                    "source_id": source_id,
                    "title": paper.title,
                    "authors": list(paper.authors),
                    "publication_year": paper.publication_year,
                    "venue": paper.venue,
                    "doi": paper.doi,
                    **evidence_basis,
                },
            },
            indent=2,
        )

        finding_schema = {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                },
                "page_numbers": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "section": {
                    "type": [
                        "string",
                        "null",
                    ],
                },
            },
            "required": [
                "content",
                "page_numbers",
                "section",
            ],
        }

        optional_finding_schema = {
            "anyOf": [
                finding_schema,
                {
                    "type": "null",
                },
            ],
        }

        response_schema = {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "string",
                },
                "problem": finding_schema,
                "approach": finding_schema,
                "representations": {
                    "type": "array",
                    "items": finding_schema,
                },
                "modalities": {
                    "type": "array",
                    "items": finding_schema,
                },
                "learning_objectives": {
                    "type": "array",
                    "items": finding_schema,
                },
                "datasets_tasks": {
                    "type": "array",
                    "items": finding_schema,
                },
                "findings": {
                    "type": "array",
                    "items": finding_schema,
                },
                "limitations": {
                    "type": "array",
                    "items": finding_schema,
                },
                "research_relevance": optional_finding_schema,
                "warnings": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": [
                "source_id",
                "problem",
                "approach",
                "representations",
                "modalities",
                "learning_objectives",
                "datasets_tasks",
                "findings",
                "limitations",
                "research_relevance",
                "warnings",
            ],
        }

        if document is not None:
            evidence_instructions = (
                "The supplied paper includes page-preserving full text. "
                "Every substantive finding must cite one or more supplied "
                "page numbers that directly support it. Use only page "
                "numbers present in the supplied pages. Section values may "
                "identify a recognizable paper section when supported by "
                "the page text; otherwise return null."
            )
        else:
            evidence_instructions = (
                "The supplied paper does not include full text. Analyze "
                "only the supplied metadata and abstract. Return an empty "
                "page_numbers array for every finding and do not invent "
                "page-level provenance. Section values should be null "
                "unless the supplied abstract or metadata explicitly "
                "supports a section name."
            )

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent retained-paper "
                "analysis service. Analyze one supplied retained paper "
                "against the research question. Return concise, atomic, "
                "evidence-supported findings for the paper's problem, "
                "approach, representations, modalities, learning or "
                "alignment objectives, datasets or tasks, findings, "
                "limitations, and relevance to the current research. "
                "Distinguish what the paper states from generated "
                "interpretation. Do not use outside knowledge. Do not "
                "invent unsupported paper content. Omit unsupported "
                "optional findings by returning empty arrays or null. "
                "The supplied source_id is an opaque identifier and must "
                "be returned exactly as supplied. Do not modify, expand, "
                "normalize, format, or invent source identifiers. "
                + evidence_instructions
            ),
            user_prompt=user_prompt,
            response_schema=response_schema,
            model_name=self._model_name,
            temperature=0.0,
            metadata={
                "research_request_id": request.request_id,
                "paper_source_id": source_id,
                "analysis_basis": (
                    ResearchPaperAnalysisBasis.FULL_TEXT
                    if document is not None
                    else ResearchPaperAnalysisBasis.ABSTRACT_METADATA
                ),
            },
        )

    def _create_analysis(
        self,
        *,
        paper: PaperMetadata,
        document: ResearchPaperDocument | None,
        provider_response: ProviderResponse,
    ) -> PaperAnalysis:
        """Create one structured retained-paper analysis."""

        structured_output = provider_response.structured_output

        if structured_output is None:
            raise ValueError(
                "Provider response did not include structured output."
            )

        if not isinstance(structured_output, dict):
            raise ValueError(
                "Provider structured output must be an object."
            )

        source_id = structured_output.get(
            "source_id"
        )

        if not isinstance(source_id, str):
            raise ValueError(
                "Provider field 'source_id' must be a string."
            )

        expected_source_id = (
            paper.source_reference.source_id
        )

        if source_id != expected_source_id:
            raise ValueError(
                "Paper analysis referenced an unknown source "
                f"identifier: {source_id}"
            )

        analysis_basis = (
            ResearchPaperAnalysisBasis.FULL_TEXT
            if document is not None
            else ResearchPaperAnalysisBasis.ABSTRACT_METADATA
        )

        warnings = list(
            self._parse_string_tuple(
                structured_output.get("warnings"),
                "warnings",
            )
        )

        if document is None:
            warnings.insert(
                0,
                "Full text was unavailable; analysis is limited to "
                "paper metadata and abstract.",
            )

        return PaperAnalysis(
            paper=paper,
            problem=self._parse_finding(
                paper=paper,
                document=document,
                value=structured_output.get("problem"),
                field_name="problem",
            ),
            approach=self._parse_finding(
                paper=paper,
                document=document,
                value=structured_output.get("approach"),
                field_name="approach",
            ),
            analysis_basis=analysis_basis,
            representations=self._parse_findings(
                paper=paper,
                document=document,
                value=structured_output.get("representations"),
                field_name="representations",
            ),
            modalities=self._parse_findings(
                paper=paper,
                document=document,
                value=structured_output.get("modalities"),
                field_name="modalities",
            ),
            learning_objectives=self._parse_findings(
                paper=paper,
                document=document,
                value=structured_output.get("learning_objectives"),
                field_name="learning_objectives",
            ),
            datasets_tasks=self._parse_findings(
                paper=paper,
                document=document,
                value=structured_output.get("datasets_tasks"),
                field_name="datasets_tasks",
            ),
            findings=self._parse_findings(
                paper=paper,
                document=document,
                value=structured_output.get("findings"),
                field_name="findings",
            ),
            limitations=self._parse_findings(
                paper=paper,
                document=document,
                value=structured_output.get("limitations"),
                field_name="limitations",
            ),
            research_relevance=self._parse_optional_finding(
                paper=paper,
                document=document,
                value=structured_output.get("research_relevance"),
                field_name="research_relevance",
            ),
            warnings=tuple(warnings),
        )

    def _parse_optional_finding(
        self,
        *,
        paper: PaperMetadata,
        document: ResearchPaperDocument | None,
        value: Any,
        field_name: str,
    ) -> ResearchFinding | None:
        """Parse one optional retained-paper finding."""

        if value is None:
            return None

        return self._parse_finding(
            paper=paper,
            document=document,
            value=value,
            field_name=field_name,
        )

    def _parse_findings(
        self,
        *,
        paper: PaperMetadata,
        document: ResearchPaperDocument | None,
        value: Any,
        field_name: str,
    ) -> tuple[ResearchFinding, ...]:
        """Parse a list of retained-paper findings."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        return tuple(
            self._parse_finding(
                paper=paper,
                document=document,
                value=item,
                field_name=field_name,
            )
            for item in value
        )

    def _parse_finding(
        self,
        *,
        paper: PaperMetadata,
        document: ResearchPaperDocument | None,
        value: Any,
        field_name: str,
    ) -> ResearchFinding:
        """Parse one evidence-backed retained-paper finding."""

        if not isinstance(value, dict):
            raise ValueError(
                f"Provider field '{field_name}' findings must be objects."
            )

        content = value.get("content")

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                f"Provider field '{field_name}' finding content "
                "must be a non-empty string."
            )

        page_numbers = value.get(
            "page_numbers"
        )

        if not isinstance(page_numbers, list):
            raise ValueError(
                f"Provider field '{field_name}' finding page_numbers "
                "must be an array."
            )

        if (
            any(
                isinstance(page_number, bool)
                or not isinstance(page_number, int)
                for page_number in page_numbers
            )
        ):
            raise ValueError(
                f"Provider field '{field_name}' finding page_numbers "
                "must contain integers only."
            )

        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError(
                f"Provider field '{field_name}' finding page_numbers "
                "must not contain duplicates."
            )

        section = value.get(
            "section"
        )

        if section is not None and not isinstance(section, str):
            raise ValueError(
                f"Provider field '{field_name}' finding section "
                "must be a string or null."
            )

        if isinstance(section, str):
            section = section.strip() or None

        source_id = paper.source_reference.source_id

        if document is None:
            if page_numbers:
                raise ValueError(
                    f"Provider field '{field_name}' invented page "
                    "provenance for metadata-only analysis."
                )

            evidence = (
                ResearchEvidenceReference(
                    source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
                    source_id=source_id,
                    section=section,
                ),
            )
        else:
            valid_page_numbers = {
                page.page_number
                for page in document.pages
            }

            if not page_numbers:
                raise ValueError(
                    f"Provider field '{field_name}' full-text finding "
                    "must cite at least one page."
                )

            invalid_page_numbers = [
                page_number
                for page_number in page_numbers
                if page_number not in valid_page_numbers
            ]

            if invalid_page_numbers:
                invalid = ", ".join(
                    str(page_number)
                    for page_number in invalid_page_numbers
                )
                raise ValueError(
                    f"Provider field '{field_name}' referenced unknown "
                    f"paper page numbers: {invalid}"
                )

            evidence = tuple(
                ResearchEvidenceReference(
                    source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
                    source_id=source_id,
                    page_number=page_number,
                    section=section,
                )
                for page_number in page_numbers
            )

        return ResearchFinding(
            content=content.strip(),
            evidence=evidence,
        )

    def _index_documents(
        self,
        *,
        papers: tuple[PaperMetadata, ...],
        paper_documents: tuple[ResearchPaperDocument, ...],
    ) -> dict[str, ResearchPaperDocument]:
        """Validate and index supplied full-text paper documents."""

        paper_by_source_id = {
            paper.source_reference.source_id: paper
            for paper in papers
        }

        document_by_source_id: dict[
            str,
            ResearchPaperDocument,
        ] = {}

        for document in paper_documents:
            source_id = (
                document.paper.source_reference.source_id
            )

            if source_id not in paper_by_source_id:
                raise ValueError(
                    "Paper analysis received a document for an unknown "
                    f"source identifier: {source_id}"
                )

            if source_id in document_by_source_id:
                raise ValueError(
                    "Paper analysis received duplicate documents for "
                    f"source identifier: {source_id}"
                )

            expected_paper = paper_by_source_id[
                source_id
            ]

            if document.paper != expected_paper:
                raise ValueError(
                    "Paper analysis document metadata did not match "
                    f"retained paper source identifier: {source_id}"
                )

            document_by_source_id[
                source_id
            ] = document

        return document_by_source_id

    @staticmethod
    def _parse_string_tuple(
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        """Parse a list of strings into a tuple."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        if not all(
            isinstance(item, str)
            for item in value
        ):
            raise ValueError(
                f"Provider field '{field_name}' must contain strings only."
            )

        return tuple(value)

    @staticmethod
    def _is_retryable_analysis_error(
        error: ValueError,
    ) -> bool:
        """Return whether one structured-output retry is appropriate."""

        message = str(error)

        return (
            "structured output" in message.lower()
            or "provider field" in message.lower()
            or message.startswith(
                "Paper analysis referenced an unknown source identifier:"
            )
        )
