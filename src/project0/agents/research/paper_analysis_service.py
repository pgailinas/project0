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

        return tuple(
            self._analyze_paper(
                request=request,
                strategy=strategy,
                paper=paper,
            )
            for paper in papers
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
                    "analysis_basis": (
                        ResearchPaperAnalysisBasis.ABSTRACT_METADATA
                    ),
                    "abstract": paper.abstract,
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
            },
            "required": [
                "content",
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

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent retained-paper "
                "analysis service. Analyze one supplied retained paper "
                "against the research question using only the supplied "
                "paper metadata and abstract. Return concise, atomic, "
                "evidence-supported findings for the paper's problem, "
                "approach, representations, modalities, learning or "
                "alignment objectives, datasets or tasks, findings, "
                "limitations, and relevance to the current research. "
                "Distinguish what the paper states from generated "
                "interpretation. Do not use outside knowledge. Do not "
                "invent unsupported paper content. Omit unsupported "
                "optional findings by returning empty arrays or null. "
                "Do not infer full-paper content, page-level provenance, "
                "or unsupported section details. Section values should "
                "be null unless the supplied metadata or abstract "
                "explicitly supports a section name. The supplied "
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
                    ResearchPaperAnalysisBasis.ABSTRACT_METADATA
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
            analysis_basis=ResearchPaperAnalysisBasis.ABSTRACT_METADATA,
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
            research_relevance=self._parse_optional_finding(
                paper=paper,
                value=structured_output.get("research_relevance"),
                field_name="research_relevance",
            ),
            warnings=self._parse_string_tuple(
                structured_output.get("warnings"),
                "warnings",
            ),
        )

    def _parse_optional_finding(
        self,
        *,
        paper: PaperMetadata,
        value: Any,
        field_name: str,
    ) -> ResearchFinding | None:
        """Parse one optional retained-paper finding."""

        if value is None:
            return None

        return self._parse_finding(
            paper=paper,
            value=value,
            field_name=field_name,
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

        return tuple(
            self._parse_finding(
                paper=paper,
                value=item,
                field_name=field_name,
            )
            for item in value
        )

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

        evidence = (
            ResearchEvidenceReference(
                source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
                source_id=paper.source_reference.source_id,
                section=section,
            ),
        )

        return ResearchFinding(
            content=content.strip(),
            evidence=evidence,
        )

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
