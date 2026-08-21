# ============================================================
# Project0 - Research Evaluation Service
#
# File: research_evaluation_service.py
#
# Purpose:
#     Coordinate AI-assisted paper relevance evaluation and
#     structured Research Agent evaluation result generation.
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
    PaperMetadata,
    ResearchEvaluation,
    ResearchRequest,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


class ResearchEvaluationService:
    """Execute AI-assisted research paper evaluation."""

    def __init__(
        self,
        provider: ReasoningProviderProtocol,
        model_name: str,
    ) -> None:
        """Initialize the research evaluation service dependencies."""

        self._provider = provider
        self._model_name = model_name

    def evaluate(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate candidate papers for a research request."""

        if not papers:
            return ()

        provider_request = self._build_provider_request(
            request=request,
            strategy=strategy,
            papers=papers,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        return self._create_evaluations(
            papers=papers,
            provider_response=provider_response,
        )

    def _build_provider_request(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> ProviderRequest:
        """Build a provider-neutral paper evaluation request."""

        paper_payload = [
            {
                "source_id": paper.source_reference.source_id,
                "title": paper.title,
                "authors": list(paper.authors),
                "publication_year": paper.publication_year,
                "abstract": paper.abstract,
                "venue": paper.venue,
            }
            for paper in papers
        ]

        user_prompt = json.dumps(
            {
                "research_question": request.question,
                "constraints": list(request.constraints),
                "focus_areas": list(request.focus_areas),
                "research_concepts": list(strategy.concepts),
                "papers": paper_payload,
            },
            indent=2,
        )

        response_schema = {
            "type": "object",
            "properties": {
                "evaluations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "string",
                            },
                            "relevance_score": {
                                "type": [
                                    "number",
                                    "string",
                                    "null",
                                ],
                            },
                            "relevance_summary": {
                                "type": "string",
                            },
                            "strengths": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "limitations": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "research_connections": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                            "warnings": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                            },
                        },
                        "required": [
                            "source_id",
                            "relevance_score",
                            "relevance_summary",
                            "strengths",
                            "limitations",
                            "research_connections",
                            "warnings",
                        ],
                    },
                },
            },
            "required": [
                "evaluations",
            ],
        }

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent evaluation "
                "service. Evaluate each supplied paper against the "
                "research question using only the supplied metadata. "
                "Distinguish source information from generated "
                "analysis. Do not invent unsupported paper content. "
                "Return one evaluation for each supplied paper."
            ),
            user_prompt=user_prompt,
            response_schema=response_schema,
            model_name=self._model_name,
            temperature=0.0,
            metadata={
                "research_request_id": request.request_id,
                "paper_count": len(papers),
            },
        )

    def _create_evaluations(
        self,
        papers: tuple[PaperMetadata, ...],
        provider_response: ProviderResponse,
    ) -> tuple[ResearchEvaluation, ...]:
        """Create research evaluations from a provider response."""

        structured_output = provider_response.structured_output

        if structured_output is None:
            raise ValueError(
                "Provider response did not include structured output."
            )

        items = self._require_list(
            structured_output.get("evaluations"),
            "evaluations",
        )

        paper_by_source_id = {
            paper.source_reference.source_id: paper
            for paper in papers
        }

        evaluations: list[ResearchEvaluation] = []
        seen_source_ids: set[str] = set()

        for item in items:
            mapping = self._require_mapping(
                item,
                "evaluation",
            )

            source_id = self._require_string(
                mapping,
                "source_id",
            )

            if source_id in seen_source_ids:
                raise ValueError(
                    "Duplicate research evaluation source identifier: "
                    f"{source_id}"
                )

            paper = paper_by_source_id.get(source_id)

            if paper is None:
                raise ValueError(
                    "Research evaluation referenced an unknown "
                    f"source identifier: {source_id}"
                )

            seen_source_ids.add(source_id)

            evaluations.append(
                ResearchEvaluation(
                    paper=paper,
                    relevance_score=self._parse_score(
                        mapping.get("relevance_score")
                    ),
                    relevance_summary=self._require_string(
                        mapping,
                        "relevance_summary",
                    ),
                    strengths=self._parse_string_tuple(
                        mapping.get("strengths"),
                        "strengths",
                    ),
                    limitations=self._parse_string_tuple(
                        mapping.get("limitations"),
                        "limitations",
                    ),
                    research_connections=self._parse_string_tuple(
                        mapping.get("research_connections"),
                        "research_connections",
                    ),
                    warnings=self._parse_string_tuple(
                        mapping.get("warnings"),
                        "warnings",
                    ),
                )
            )

        missing_source_ids = (
            set(paper_by_source_id) - seen_source_ids
        )

        if missing_source_ids:
            missing = ", ".join(
                sorted(missing_source_ids)
            )
            raise ValueError(
                "Provider response did not include evaluations "
                f"for source identifiers: {missing}"
            )

        return tuple(evaluations)

    def _parse_string_tuple(
        self,
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        """Parse a list of strings into a tuple."""

        items = self._require_list(
            value,
            field_name,
        )

        if not all(
            isinstance(item, str)
            for item in items
        ):
            raise TypeError(
                f"{field_name} must contain strings only."
            )

        return tuple(items)

    def _parse_score(
        self,
        value: Any,
    ) -> float | None:
        """Parse and normalize an optional relevance score."""

        LOGGER.debug(
            "Raw research relevance score: %r",
            value,
        )

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value.endswith("%"):
                value = value[:-1]

                try:
                    score = float(value) / 100.0
                except ValueError as error:
                    raise TypeError(
                        "Relevance score must be numeric or null."
                    ) from error

                return self._validate_score(
                    score
                )

            try:
                value = float(value)

            except ValueError as error:
                raise TypeError(
                    "Relevance score must be numeric or null."
                ) from error

        if not isinstance(value, (int, float)):
            raise TypeError(
                "Relevance score must be numeric or null."
            )

        score = float(value)

        if (
            1.0 < score <= 100.0
            and score.is_integer()
        ):
            score /= 100.0

        return self._validate_score(
            score
        )

    @staticmethod
    def _validate_score(
        score: float,
    ) -> float:
        """Validate normalized relevance score."""

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                "Relevance score must be between 0.0 and 1.0."
            )

        return score

    @staticmethod
    def _require_string(
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string value."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        return value

    @staticmethod
    def _require_list(
        value: Any,
        field_name: str,
    ) -> list[Any]:
        """Return a required list value."""

        if not isinstance(value, list):
            raise TypeError(
                f"{field_name} must be a list."
            )

        return value

    @staticmethod
    def _require_mapping(
        value: Any,
        field_name: str,
    ) -> dict[str, Any]:
        """Return a required mapping value."""

        if not isinstance(value, dict):
            raise TypeError(
                f"{field_name} must be an object."
            )

        return value
