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
    ResearchPaperEvidenceSection,
    ResearchPaperEvidenceStatus,
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
    ) -> tuple[PaperAnalysis, ...]:
        """Analyze retained papers for a research request."""

        if not papers:
            return ()

        analyses = []

        for paper in papers:
            if (
                paper.evidence_status
                == ResearchPaperEvidenceStatus.DISCOVERY_ONLY
                and not paper.abstract
            ):
                LOGGER.info(
                    "Skipping discovery-only paper analysis for source %s.",
                    paper.source_reference.source_id,
                )
                continue

            try:
                analysis = self._analyze_paper(
                    request=request,
                    strategy=strategy,
                    paper=paper,
                )
            except ValueError as error:
                LOGGER.warning(
                    "Skipping retained-paper analysis for source %s "
                    "after structural validation failed: %s",
                    paper.source_reference.source_id,
                    error,
                )
                continue

            analyses.append(
                analysis
            )

        return tuple(
            analyses
        )

    def _analyze_paper(
        self,
        *,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        paper: PaperMetadata,
    ) -> PaperAnalysis:
        """Analyze one retained paper with one validation retry."""

        provider_request = self._build_provider_request(
            request=request,
            strategy=strategy,
            paper=paper,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_analysis(
                paper=paper,
                provider_response=provider_response,
            )
        except ValueError as error:
            if not self._is_retryable_analysis_error(
                error
            ):
                raise

            LOGGER.warning(
                "Paper analysis response failed structural "
                "validation; retrying once: %s",
                error,
            )

        provider_response = self._provider.generate(
            provider_request
        )

        return self._create_analysis(
            paper=paper,
            provider_response=provider_response,
        )

    def _build_provider_request(
        self,
        *,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        paper: PaperMetadata,
    ) -> ProviderRequest:
        """Build a provider-neutral retained-paper analysis request."""

        source_id = paper.source_reference.source_id
        evidence_sections = self._evidence_sections(paper)
        analysis_basis = (
            ResearchPaperAnalysisBasis.PAPER_CONTENT
            if any(
                section.page_number is not None
                for section in evidence_sections
            )
            else ResearchPaperAnalysisBasis.ABSTRACT_METADATA
        )

        user_prompt = json.dumps(
            {
                "paper": {
                    "source_id": source_id,
                    "title": paper.title,
                    "authors": list(paper.authors),
                    "publication_year": paper.publication_year,
                    "venue": paper.venue,
                    "doi": paper.doi,
                    "analysis_basis": (
                        analysis_basis
                    ),
                    "abstract": paper.abstract,
                    "evidence_sections": [
                        {
                            "section": section.section,
                            "page_number": section.page_number,
                            "content": section.content,
                        }
                        for section in evidence_sections
                    ],
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
                "section": {
                    "type": [
                        "string",
                        "null",
                    ],
                },
                "page_number": {
                    "type": [
                        "integer",
                        "null",
                    ],
                },
            },
            "required": [
                "content",
                "section",
                "page_number",
            ],
        }

        response_schema = {
            "type": "object",
            "properties": {
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
                "warnings": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": [
                "problem",
                "approach",
                "representations",
                "modalities",
                "learning_objectives",
                "datasets_tasks",
                "findings",
                "limitations",
                "warnings",
            ],
        }

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent retained-paper "
                "analysis service. Analyze one supplied retained paper "
                "using only the supplied bounded evidence sections and "
                "paper metadata. "
                "Return concise, atomic, evidence-supported findings "
                "for the paper's problem, approach, representations, "
                "modalities, learning or alignment objectives, datasets "
                "or tasks, findings, and limitations. Distinguish what "
                "the paper states from generated interpretation. Do not "
                "use outside knowledge. Do not invent unsupported paper "
                "content. Omit unsupported optional findings by "
                "returning empty arrays. "
                "Every finding must cite a supplied section and its supplied "
                "page number when present. Cite Abstract with a null page "
                "number for abstract-backed findings. Do not infer full-paper content "
                "or unsupported section details. The supplied "
                "source_id identifies the paper being analyzed and is "
                "context only. Do not return or generate source "
                "identifiers in the analysis response."
            ),
            user_prompt=user_prompt,
            response_schema=response_schema,
            model_name=self._model_name,
            temperature=0.0,
            metadata={
                "research_request_id": request.request_id,
                "paper_source_id": source_id,
                "analysis_basis": (
                    analysis_basis
                ),
            },
        )

    def _create_analysis(
        self,
        *,
        paper: PaperMetadata,
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

        return PaperAnalysis(
            paper=paper,
            problem=self._parse_finding(
                paper=paper,
                value=structured_output.get("problem"),
                field_name="problem",
            ),
            approach=self._parse_finding(
                paper=paper,
                value=structured_output.get("approach"),
                field_name="approach",
            ),
            analysis_basis=(
                ResearchPaperAnalysisBasis.PAPER_CONTENT
                if any(
                    section.page_number is not None
                    for section in self._evidence_sections(paper)
                )
                else ResearchPaperAnalysisBasis.ABSTRACT_METADATA
            ),
            representations=self._parse_findings(
                paper=paper,
                value=structured_output.get("representations"),
                field_name="representations",
            ),
            modalities=self._parse_findings(
                paper=paper,
                value=structured_output.get("modalities"),
                field_name="modalities",
            ),
            learning_objectives=self._parse_findings(
                paper=paper,
                value=structured_output.get("learning_objectives"),
                field_name="learning_objectives",
            ),
            datasets_tasks=self._parse_findings(
                paper=paper,
                value=structured_output.get("datasets_tasks"),
                field_name="datasets_tasks",
            ),
            findings=self._parse_findings(
                paper=paper,
                value=structured_output.get("findings"),
                field_name="findings",
            ),
            limitations=self._parse_findings(
                paper=paper,
                value=structured_output.get("limitations"),
                field_name="limitations",
            ),
            warnings=self._parse_string_tuple(
                structured_output.get("warnings"),
                "warnings",
            ),
        )

    def _parse_findings(
        self,
        *,
        paper: PaperMetadata,
        value: Any,
        field_name: str,
    ) -> tuple[ResearchFinding, ...]:
        """Parse a list of retained-paper findings."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        findings: list[ResearchFinding] = []

        for item in value:
            try:
                finding = self._parse_finding(
                    paper=paper,
                    value=item,
                    field_name=field_name,
                )
            except ValueError as error:
                LOGGER.warning(
                    "Skipping invalid optional retained-paper finding for "
                    "field '%s': %s",
                    field_name,
                    error,
                )
                continue

            findings.append(finding)

        return tuple(findings)

    def _parse_finding(
        self,
        *,
        paper: PaperMetadata,
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

        page_number = value.get("page_number")
        if page_number is not None and (
            isinstance(page_number, bool)
            or not isinstance(page_number, int)
            or page_number < 1
        ):
            raise ValueError(
                f"Provider field '{field_name}' finding page_number "
                "must be a positive integer or null."
            )

        evidence_sections = {
            (item.section.lower(), item.page_number)
            for item in self._evidence_sections(paper)
        }
        if (
            section is None
            and page_number is None
            and ("abstract", None) in evidence_sections
        ):
            section = "Abstract"
        if (
            section is None
            or (section.lower(), page_number) not in evidence_sections
        ):
            raise ValueError(
                f"Provider field '{field_name}' finding must cite a "
                "supplied evidence section and page number when present."
            )

        evidence = (
            ResearchEvidenceReference(
                source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
                source_id=paper.source_reference.source_id,
                page_number=page_number,
                section=section,
            ),
        )

        return ResearchFinding(
            content=content.strip(),
            evidence=evidence,
        )

    @staticmethod
    def _evidence_sections(
        paper: PaperMetadata,
    ) -> tuple[ResearchPaperEvidenceSection, ...]:
        """Return explicit evidence or a compatible abstract section."""

        evidence_sections = paper.evidence_sections

        if (
            paper.abstract is not None
            and paper.abstract.strip()
            and not any(
                item.section.lower() == "abstract"
                for item in evidence_sections
            )
        ):
            return (
                ResearchPaperEvidenceSection(
                    section="Abstract",
                    content=paper.abstract.strip(),
                ),
                *evidence_sections,
            )

        return evidence_sections

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
        )
