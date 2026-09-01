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
        self._batch_size = 1

    def evaluate(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate candidate papers for a research request."""

        if not papers:
            return ()

        evaluations: list[ResearchEvaluation] = []

        for start in range(
            0,
            len(papers),
            self._batch_size,
        ):
            batch = papers[
                start:start + self._batch_size
            ]

            evaluations.extend(
                self._evaluate_batch(
                    request=request,
                    strategy=strategy,
                    papers=batch,
                )
            )

        return tuple(evaluations)

    def _evaluate_batch(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate one bounded paper batch with one validation retry."""

        provider_request = self._build_provider_request(
            request=request,
            strategy=strategy,
            papers=papers,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_evaluations(
                papers=papers,
                provider_response=provider_response,
            )
        except ValueError as error:
            if not self._is_retryable_evaluation_error(
                error
            ):
                raise

            LOGGER.warning(
                "Research evaluation response failed source "
                "traceability or coverage validation; retrying once: %s",
                error,
            )

            if self._is_missing_evaluation_error(error):
                retained, missing_papers = (
                    self._create_partial_evaluations(
                        papers=papers,
                        provider_response=provider_response,
                    )
                )

                retry_request = self._build_provider_request(
                    request=request,
                    strategy=strategy,
                    papers=missing_papers,
                )
                retry_response = self._provider.generate(
                    retry_request
                )
                retry_evaluations = self._create_evaluations(
                    papers=missing_papers,
                    provider_response=retry_response,
                )

                evaluations_by_source_id = {
                    evaluation.paper.source_reference.source_id:
                    evaluation
                    for evaluation in (
                        *retained,
                        *retry_evaluations,
                    )
                }

                return tuple(
                    evaluations_by_source_id[
                        paper.source_reference.source_id
                    ]
                    for paper in papers
                )

        provider_response = self._provider.generate(
            provider_request
        )

        return self._create_evaluations(
            papers=papers,
            provider_response=provider_response,
        )

    def _create_partial_evaluations(
        self,
        papers: tuple[PaperMetadata, ...],
        provider_response: ProviderResponse,
    ) -> tuple[
        tuple[ResearchEvaluation, ...],
        tuple[PaperMetadata, ...],
    ]:
        """Create valid evaluations and identify missing papers."""

        structured_output = provider_response.structured_output

        if structured_output is None:
            raise ValueError(
                "Provider response did not include structured output."
            )

        items = self._require_list(
            structured_output.get("evaluations"),
            "evaluations",
        )

        paper_by_source_id = self._index_papers(papers)

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

        missing_papers = tuple(
            paper
            for source_id, paper in paper_by_source_id.items()
            if source_id not in seen_source_ids
        )

        return tuple(evaluations), missing_papers

    @staticmethod
    def _is_missing_evaluation_error(
        error: ValueError,
    ) -> bool:
        """Return whether validation failed from missing coverage."""

        return str(error).startswith(
            "Provider response did not include evaluations "
            "for source identifiers:"
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
                "source_id": source_id,
                "title": paper.title,
                "authors": list(paper.authors),
                "publication_year": paper.publication_year,
                "abstract": paper.abstract,
                "venue": paper.venue,
            }
            for source_id, paper in self._index_papers(
                papers
            ).items()
        ]

        user_prompt = json.dumps(
            {
                "research_question": request.question,
                "guidance": request.guidance,
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
                    "minItems": len(papers),
                    "maxItems": len(papers),
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "string",
                            },
                            "relevance_score": {
                                "type": [
                                    "integer",
                                    "null",
                                ],
                                "minimum": 0,
                                "maximum": 100,
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
                "Assign relevance_score as an integer from 0 to 100: "
                "90-100 directly addresses both the primary application "
                "or task and the central technical problem in the "
                "research question; 75-89 directly addresses one major "
                "dimension and provides strong, well-supported relevance "
                "to the other; 50-74 uses related methods, "
                "representations, or problem settings, but applicability "
                "to the complete research question is indirect; 25-49 "
                "primarily background, adjacent, or transferable "
                "research; 0-24 weakly related or off-topic. Do not "
                "assign a high score based primarily on keyword or "
                "topical overlap. When the supplied metadata indicates "
                "that a major dimension of the research question is "
                "absent or only indirect, the relevance score must "
                "reflect that limitation. Use the same relevance "
                "standard for every paper in the batch so scores are "
                "meaningfully comparable. Missing or limited metadata "
                "must reduce confidence and must not support an otherwise "
                "unsupported high relevance score. "
                "Distinguish source information from generated "
                "analysis. Do not invent unsupported paper content. "
                "Return one evaluation for each supplied paper. Treat "
                "each source_id as an opaque identifier and return it "
                "exactly as supplied. Do not modify, expand, normalize, "
                "format, or invent source identifiers."
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

    @staticmethod
    def _index_papers(
        papers: tuple[PaperMetadata, ...],
    ) -> dict[str, PaperMetadata]:
        """Index papers by deterministic evaluation identifiers."""

        return {
            f"paper-{index:03d}": paper
            for index, paper in enumerate(papers, start=1)
        }

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

        paper_by_source_id = self._index_papers(papers)

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

    @staticmethod
    def _is_retryable_evaluation_error(
        error: ValueError,
    ) -> bool:
        """Return whether evaluation validation permits one retry."""

        message = str(error)

        return (
            message.startswith(
                "Duplicate research evaluation source identifier:"
            )
            or message.startswith(
                "Research evaluation referenced an unknown "
                "source identifier:"
            )
            or message.startswith(
                "Provider response did not include evaluations "
                "for source identifiers:"
            )
        )

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
        """Parse and normalize an optional 0-100 relevance score."""

        LOGGER.debug(
            "Raw research relevance score: %r",
            value,
        )

        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                "Relevance score must be an integer from 0 to 100 "
                "or null."
            )

        score = float(value)

        if not score.is_integer():
            raise TypeError(
                "Relevance score must be an integer from 0 to 100 "
                "or null."
            )

        if not 0 <= score <= 100:
            raise ValueError(
                "Relevance score must be between 0 and 100."
            )

        return score / 100.0

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
