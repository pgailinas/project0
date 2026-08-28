# ============================================================
# Project0 - Existing Research Context Analysis Service
#
# File: existing_research_context_analysis_service.py
#
# Purpose:
#     Analyze normalized existing research context documents
#     into structured Research Agent context findings.
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
    ExistingResearchContext,
    ResearchContextDocument,
    ResearchEvidenceReference,
    ResearchEvidenceSourceType,
    ResearchFinding,
)


LOGGER = logging.getLogger(__name__)


class ExistingResearchContextAnalysisService:
    """Execute AI-assisted existing research context analysis."""

    def __init__(
        self,
        provider: ReasoningProviderProtocol,
        model_name: str,
    ) -> None:
        """Initialize the research context analysis dependencies."""

        self._provider = provider
        self._model_name = model_name

    def analyze(
        self,
        document: ResearchContextDocument,
    ) -> ExistingResearchContext:
        """Analyze a normalized existing research context document."""

        provider_request = self._build_provider_request(
            document=document,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_context(
                document=document,
                provider_response=provider_response,
            )
        except ValueError as error:
            if not self._is_retryable_analysis_error(
                error
            ):
                raise

            LOGGER.warning(
                "Existing research context analysis response failed "
                "structural or traceability validation; retrying once: %s",
                error,
            )

        provider_response = self._provider.generate(
            provider_request
        )

        return self._create_context(
            document=document,
            provider_response=provider_response,
        )

    def _build_provider_request(
        self,
        document: ResearchContextDocument,
    ) -> ProviderRequest:
        """Build a provider-neutral existing research context request."""

        user_prompt = json.dumps(
            {
                "document_id": document.document_id,
                "source_name": document.source_name,
                "document_type": document.document_type,
                "extracted_text": document.extracted_text,
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

        response_schema = {
            "type": "object",
            "properties": {
                "research_problem": {
                    "anyOf": [
                        finding_schema,
                        {
                            "type": "null",
                        },
                    ],
                },
                "prior_work": {
                    "type": "array",
                    "items": finding_schema,
                },
                "implemented_approaches": {
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
                "unresolved_questions": {
                    "type": "array",
                    "items": finding_schema,
                },
                "stated_future_work": {
                    "type": "array",
                    "items": finding_schema,
                },
            },
            "required": [
                "research_problem",
                "prior_work",
                "implemented_approaches",
                "findings",
                "limitations",
                "unresolved_questions",
                "stated_future_work",
            ],
        }

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent existing research "
                "context analysis service. Analyze only the supplied "
                "document text and return structured findings describing "
                "the research problem, prior work, implemented approaches, "
                "findings, limitations, unresolved questions, and stated "
                "future work. Do not use outside knowledge. Do not invent "
                "unsupported claims. Omit unsupported findings by "
                "returning empty arrays, and return null when the research "
                "problem is not supported. Distinguish what the document "
                "states from what could merely be inferred. In particular, "
                "do not convert your own recommendations into stated "
                "future work. Preserve technical meaning and keep each "
                "finding concise and atomic. The supplied document_id is "
                "an opaque identifier for traceability; do not modify, "
                "expand, normalize, format, or invent it. Section values "
                "may identify a recognizable document section when the "
                "supplied text supports one; otherwise return null. Do not "
                "invent page numbers or other unavailable provenance."
            ),
            user_prompt=user_prompt,
            response_schema=response_schema,
            model_name=self._model_name,
            temperature=0.0,
            metadata={
                "research_context_document_id": document.document_id,
                "source_name": document.source_name,
            },
        )

    def _create_context(
        self,
        document: ResearchContextDocument,
        provider_response: ProviderResponse,
    ) -> ExistingResearchContext:
        """Create structured existing research context from a response."""

        structured_output = provider_response.structured_output

        if structured_output is None:
            raise ValueError(
                "Provider response did not include structured output."
            )

        if not isinstance(structured_output, dict):
            raise ValueError(
                "Provider structured output must be an object."
            )

        return ExistingResearchContext(
            research_problem=self._parse_optional_finding(
                document=document,
                value=structured_output.get("research_problem"),
                field_name="research_problem",
            ),
            prior_work=self._parse_findings(
                document=document,
                value=structured_output.get("prior_work"),
                field_name="prior_work",
            ),
            implemented_approaches=self._parse_findings(
                document=document,
                value=structured_output.get("implemented_approaches"),
                field_name="implemented_approaches",
            ),
            findings=self._parse_findings(
                document=document,
                value=structured_output.get("findings"),
                field_name="findings",
            ),
            limitations=self._parse_findings(
                document=document,
                value=structured_output.get("limitations"),
                field_name="limitations",
            ),
            unresolved_questions=self._parse_findings(
                document=document,
                value=structured_output.get("unresolved_questions"),
                field_name="unresolved_questions",
            ),
            stated_future_work=self._parse_findings(
                document=document,
                value=structured_output.get("stated_future_work"),
                field_name="stated_future_work",
            ),
        )

    def _parse_optional_finding(
        self,
        *,
        document: ResearchContextDocument,
        value: Any,
        field_name: str,
    ) -> ResearchFinding | None:
        """Parse one optional research context finding."""

        if value is None:
            return None

        return self._parse_finding(
            document=document,
            value=value,
            field_name=field_name,
        )

    def _parse_findings(
        self,
        *,
        document: ResearchContextDocument,
        value: Any,
        field_name: str,
    ) -> tuple[ResearchFinding, ...]:
        """Parse a list of research context findings."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        return tuple(
            self._parse_finding(
                document=document,
                value=item,
                field_name=field_name,
            )
            for item in value
        )

    def _parse_finding(
        self,
        *,
        document: ResearchContextDocument,
        value: Any,
        field_name: str,
    ) -> ResearchFinding:
        """Parse one evidence-backed research context finding."""

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

        section = value.get("section")

        if section is not None and not isinstance(section, str):
            raise ValueError(
                f"Provider field '{field_name}' finding section "
                "must be a string or null."
            )

        if isinstance(section, str):
            section = section.strip() or None

        evidence = ResearchEvidenceReference(
            source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
            source_id=document.document_id,
            section=section,
        )

        return ResearchFinding(
            content=content.strip(),
            evidence=(evidence,),
        )

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
