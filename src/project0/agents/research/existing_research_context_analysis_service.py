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
        research_question: str = "",
    ) -> ExistingResearchContext:
        """Analyze a normalized existing research context document."""

        provider_request = self._build_provider_request(
            document=document,
            research_question=research_question,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_context(
                document=document,
                provider_response=provider_response,
                research_question=research_question,
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
            research_question=research_question,
        )

    def _build_provider_request(
        self,
        document: ResearchContextDocument,
        research_question: str,
    ) -> ProviderRequest:
        """Build a provider-neutral existing research context request."""

        user_prompt = json.dumps(
            {
                "document_id": document.document_id,
                "source_name": document.source_name,
                "document_type": document.document_type,
                "research_question": research_question.strip(),
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
                "inferred_solution_search_concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_representation": {
                                "type": "string",
                            },
                            "target_model_or_space": {
                                "type": "string",
                            },
                            "solution_mechanism": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "source_representation",
                            "target_model_or_space",
                            "solution_mechanism",
                        ],
                    },
                    "minItems": 3,
                    "maxItems": 3,
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
                "inferred_solution_search_concepts",
            ],
        }

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent existing research "
                "context analysis service. Analyze only the supplied "
                "document text and return structured findings describing "
                "the research problem, prior work, implemented approaches, "
                "findings, limitations, unresolved questions, and stated "
                "future work. Do not use outside knowledge to add factual "
                "claims about the document. Do not invent unsupported "
                "claims. Omit unsupported findings by "
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
                "invent page numbers or other unavailable provenance. "
                "Separately infer exactly three concise, technically "
                "distinct solution-search concepts from the document's "
                "unresolved questions, stated future work, limitations, "
                "and findings, jointly with the supplied research question. "
                "For each inferred concept, return three separate elements: "
                "the source representation or model, the target model or "
                "representation space, and a technically specific solution "
                "mechanism. Keep each field concise. "
                "Each concept must use a distinct solution mechanism; do "
                "not return alternative wording for the same mechanism. "
                "The service will combine these fields into the search phrase. "
                "These concepts may introduce established "
                "technical terminology for adjacent solution mechanisms, "
                "but must remain grounded in the documented research gap "
                "and question. Preserve specific model names and technical "
                "acronyms. When the question or document names a specific "
                "source or target, include it or an unambiguous equivalent "
                "in the applicable source or target field of every concept. "
                "Do not return broad topics such as representation "
                "learning, semantic alignment, contrastive objectives, or "
                "latent regularization without the source and target. "
                "Return them only in inferred_solution_search_concepts; "
                "do not present them as document findings or stated future "
                "work. Do not place instructions or claims in these fields."
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
        research_question: str = "",
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
            inferred_solution_search_concepts=(
                self._parse_search_concepts(
                    structured_output.get(
                        "inferred_solution_search_concepts"
                    ),
                    required_model_anchors=(
                        self._required_model_anchors(research_question)
                    ),
                    require_three=bool(research_question.strip()),
                )
            ),
        )

    @staticmethod
    def _parse_search_concepts(
        value: Any,
        required_model_anchors: tuple[str, ...] = (),
        require_three: bool = False,
    ) -> tuple[str, ...]:
        """Parse bounded inferred solution-search concepts."""

        if not isinstance(value, list):
            raise ValueError(
                "Provider field 'inferred_solution_search_concepts' "
                "must be an array."
            )

        if len(value) > 3:
            raise ValueError(
                "Provider field 'inferred_solution_search_concepts' "
                "must contain at most three items."
            )

        if require_three and len(value) != 3:
            raise ValueError(
                "Provider field 'inferred_solution_search_concepts' "
                "must contain exactly three items when a research "
                "question is supplied."
            )

        concepts: list[str] = []
        seen: set[str] = set()
        seen_mechanisms: set[str] = set()

        for item in value:
            if not isinstance(item, dict):
                raise ValueError(
                    "Provider field 'inferred_solution_search_concepts' "
                    "items must be objects."
                )

            components: list[str] = []

            for field_name in (
                "source_representation",
                "target_model_or_space",
                "solution_mechanism",
            ):
                component = item.get(field_name)

                if not isinstance(component, str) or not component.strip():
                    raise ValueError(
                        "Provider field 'inferred_solution_search_concepts' "
                        f"item field '{field_name}' must be a non-empty "
                        "string."
                    )

                normalized = " ".join(component.split()).strip()

                components.append(normalized)

            mechanism_key = components[2].casefold()

            if mechanism_key in seen_mechanisms:
                raise ValueError(
                    "Provider field 'inferred_solution_search_concepts' "
                    "items must use distinct solution mechanisms."
                )

            seen_mechanisms.add(mechanism_key)

            concept = " ".join(
                dict.fromkeys(
                    word
                    for component in components
                    for word in component.split()
                )
            )

            concept_terms = {
                term.casefold()
                for word in concept.split()
                for term in word.replace("-", " ").split()
            }
            missing_anchors = tuple(
                anchor
                for anchor in required_model_anchors
                if anchor.casefold() not in concept_terms
            )

            if missing_anchors:
                concept = " ".join(
                    (
                        *missing_anchors,
                        concept,
                    )
                )

            key = concept.casefold()

            if key not in seen:
                seen.add(key)
                concepts.append(concept)

        return tuple(concepts)

    @staticmethod
    def _required_model_anchors(
        research_question: str,
    ) -> tuple[str, ...]:
        """Extract explicit model names that every concept must preserve."""

        anchors: list[str] = []

        for raw_word in research_question.split():
            for word in raw_word.strip(",.;:?()\"'").split("-"):
                letters = "".join(
                    character
                    for character in word
                    if character.isalpha()
                )
                lowered = letters.casefold()

                if not letters:
                    continue

                if (
                    (
                        len(letters) >= 2
                        and letters.isupper()
                    )
                    or "encoder" in lowered
                    or "decoder" in lowered
                ):
                    if lowered not in {
                        anchor.casefold()
                        for anchor in anchors
                    }:
                        anchors.append(letters)

        return tuple(anchors)

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
