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
import re
from dataclasses import dataclass
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
    ResearchMechanismMatch,
    ResearchPaperEvidenceStatus,
    ResearchEvaluation,
    ResearchRequest,
    ResearchStrategy,
)


LOGGER = logging.getLogger(__name__)


HIGH_RELEVANCE_SCORE = 0.75
MECHANISM_SCORE_BANDS = {
    ResearchMechanismMatch.DIRECT: (0.75, 1.0),
    ResearchMechanismMatch.TRANSFERABLE: (0.50, 0.74),
    ResearchMechanismMatch.ADJACENT: (0.25, 0.49),
    ResearchMechanismMatch.NONE: (0.0, 0.24),
}
HIGH_RELEVANCE_CONTRADICTION_MARKERS = (
    "no concrete transfer path",
    "no metadata-supported transfer path",
    "without a concrete transfer path",
    "does not provide a concrete transfer path",
    "cannot support a concrete transfer path",
    "insufficient metadata",
)


@dataclass(frozen=True, slots=True)
class _MechanismReconciliation:
    """Evidence-derived correction to one provider mechanism decision."""

    mechanism_match: ResearchMechanismMatch
    relevance_score: float | None
    relevance_summary: str
    research_connections: tuple[str, ...]
    source_mechanism: str
    target_problem_dimension: str
    required_adaptation: str
    evidence_support: tuple[str, ...]
    warning: str | None = None


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
        self._batch_size = 3

    def evaluate(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate candidate papers for a research request."""

        return self._evaluate(
            request=request,
            strategy=strategy,
            papers=papers,
            preliminary=False,
        )

    def rank_candidates(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
    ) -> tuple[ResearchEvaluation, ...]:
        """Rank candidates from metadata before evidence acquisition."""

        return self._evaluate(
            request=request,
            strategy=strategy,
            papers=papers,
            preliminary=True,
        )

    def _evaluate(
        self,
        *,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
        preliminary: bool,
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate papers for preliminary ranking or final selection."""

        if not papers:
            return ()

        evaluable_papers = tuple(
            paper
            for paper in papers
            if preliminary or not self._is_discovery_only(paper)
        )
        evaluations: list[ResearchEvaluation] = []

        for start in range(
            0,
            len(evaluable_papers),
            self._batch_size,
        ):
            batch = evaluable_papers[
                start:start + self._batch_size
            ]

            evaluations.extend(
                self._evaluate_batch(
                    request=request,
                    strategy=strategy,
                    papers=batch,
                    preliminary=preliminary,
                )
            )

        return tuple(
            next(
                (
                    evaluation
                    for evaluation in evaluations
                    if evaluation.paper is paper
                ),
                self._discovery_only_evaluation(paper),
            )
            for paper in papers
        )

    @staticmethod
    def _is_discovery_only(paper: PaperMetadata) -> bool:
        """Return whether a paper lacks usable analysis evidence."""

        return (
            paper.evidence_status
            == ResearchPaperEvidenceStatus.DISCOVERY_ONLY
            and not paper.abstract
            and not paper.evidence_sections
        )

    @staticmethod
    def _discovery_only_evaluation(
        paper: PaperMetadata,
    ) -> ResearchEvaluation:
        """Create a non-scored discovery record without model inference."""

        return ResearchEvaluation(
            paper=paper,
            relevance_score=None,
            relevance_summary=(
                "Discovery-only candidate; usable paper evidence was "
                "not available for relevance assessment."
            ),
            limitations=(
                "No authoritative abstract or bounded paper content was "
                "available.",
            ),
            warnings=(
                "Excluded from evidence-based scoring.",
            ),
        )

    def _evaluate_batch(
        self,
        request: ResearchRequest,
        strategy: ResearchStrategy,
        papers: tuple[PaperMetadata, ...],
        preliminary: bool = False,
    ) -> tuple[ResearchEvaluation, ...]:
        """Evaluate one bounded paper batch with one validation retry."""

        provider_request = self._build_provider_request(
            request=request,
            strategy=strategy,
            papers=papers,
            preliminary=preliminary,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_evaluations(
                papers=papers,
                provider_response=provider_response,
                enforce_evidence=not preliminary,
                evaluation_attempt="initial",
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
            retained, missing_papers = self._create_partial_evaluations(
                papers=papers,
                provider_response=provider_response,
                enforce_evidence=not preliminary,
                tolerate_identifier_errors=True,
                evaluation_attempt="initial_recovery",
            )

        if not missing_papers:
            return retained

        retry_request = self._build_provider_request(
            request=request,
            strategy=strategy,
            papers=missing_papers,
            preliminary=preliminary,
        )
        retry_response = self._provider.generate(
            retry_request
        )

        try:
            retry_evaluations = self._create_evaluations(
                papers=missing_papers,
                provider_response=retry_response,
                enforce_evidence=not preliminary,
                evaluation_attempt="retry",
            )
            unresolved_papers = ()
        except ValueError as error:
            if not self._is_retryable_evaluation_error(error):
                raise

            LOGGER.warning(
                "Research evaluation retry remained invalid; preserving "
                "valid evaluations and marking unresolved papers unscored: %s",
                error,
            )
            retry_evaluations, unresolved_papers = (
                self._create_partial_evaluations(
                    papers=missing_papers,
                    provider_response=retry_response,
                    enforce_evidence=not preliminary,
                    tolerate_identifier_errors=True,
                    evaluation_attempt="retry_recovery",
                )
            )

        evaluations_by_paper = {
            id(evaluation.paper): evaluation
            for evaluation in (
                *retained,
                *retry_evaluations,
            )
        }
        evaluations_by_paper.update(
            {
                id(paper): self._invalid_response_evaluation(paper)
                for paper in unresolved_papers
            }
        )

        return tuple(
            evaluations_by_paper[id(paper)]
            for paper in papers
        )

    def _create_partial_evaluations(
        self,
        papers: tuple[PaperMetadata, ...],
        provider_response: ProviderResponse,
        enforce_evidence: bool = True,
        tolerate_identifier_errors: bool = False,
        evaluation_attempt: str = "initial",
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
                if tolerate_identifier_errors:
                    LOGGER.warning(
                        "Ignoring duplicate research evaluation identifier "
                        "during partial recovery: %s",
                        source_id,
                    )
                    continue
                raise ValueError(
                    "Duplicate research evaluation source identifier: "
                    f"{source_id}"
                )

            paper = paper_by_source_id.get(source_id)

            if paper is None:
                if tolerate_identifier_errors:
                    LOGGER.warning(
                        "Ignoring unknown research evaluation identifier "
                        "during partial recovery: %s",
                        source_id,
                    )
                    continue
                raise ValueError(
                    "Research evaluation referenced an unknown "
                    f"source identifier: {source_id}"
                )

            try:
                evaluation = self._create_evaluation(
                    paper=paper,
                    mapping=mapping,
                    enforce_evidence=enforce_evidence,
                    evaluation_attempt=evaluation_attempt,
                    batch_source_id=source_id,
                )
            except ValueError as error:
                if (
                    not tolerate_identifier_errors
                    or not self._is_retryable_evaluation_error(error)
                ):
                    raise
                LOGGER.warning(
                    "Ignoring invalid research evaluation during partial "
                    "recovery for identifier %s: %s",
                    source_id,
                    error,
                )
                continue

            evaluations.append(evaluation)
            seen_source_ids.add(source_id)

        missing_papers = tuple(
            paper
            for source_id, paper in paper_by_source_id.items()
            if source_id not in seen_source_ids
        )

        return tuple(evaluations), missing_papers

    @staticmethod
    def _invalid_response_evaluation(
        paper: PaperMetadata,
    ) -> ResearchEvaluation:
        """Return an unscored result after persistent response corruption."""

        return ResearchEvaluation(
            paper=paper,
            relevance_score=None,
            relevance_summary=(
                "The paper could not be scored because the evaluation "
                "response did not preserve its supplied identifier."
            ),
            limitations=(
                "Evidence-based relevance assessment was unavailable.",
            ),
            warnings=(
                "Excluded from scoring after an invalid evaluation response.",
            ),
        )

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
        preliminary: bool = False,
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
                "evidence_status": (
                    "pending_acquisition"
                    if preliminary
                    else paper.evidence_status
                ),
                "evidence_sections": [
                    {
                        "section": section.section,
                        "page_number": section.page_number,
                        "content": section.content,
                    }
                    for section in paper.evidence_sections
                ],
            }
            for source_id, paper in self._index_papers(
                papers
            ).items()
        ]

        user_prompt = json.dumps(
            {
                "evaluation_stage": (
                    "preliminary_metadata_ranking"
                    if preliminary
                    else "final_evidence_evaluation"
                ),
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
                            "mechanism_match": {
                                "type": "string",
                                "enum": [
                                    match.value
                                    for match in ResearchMechanismMatch
                                ],
                            },
                            "source_mechanism": {
                                "type": "string",
                            },
                            "target_problem_dimension": {
                                "type": "string",
                            },
                            "required_adaptation": {
                                "type": "string",
                            },
                            "evidence_support": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
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
                            "mechanism_match",
                            "source_mechanism",
                            "target_problem_dimension",
                            "required_adaptation",
                            "evidence_support",
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
                + (
                    "This is preliminary metadata ranking before evidence "
                    "acquisition. Rank comparative promise from the title, "
                    "abstract, and source metadata. Do not treat the current "
                    "evidence_status as a final discovery-only decision. "
                    if preliminary
                    else
                    "This is final evidence-based evaluation after evidence "
                    "acquisition. "
                )
                +
                "When bounded evidence sections are supplied, base the "
                "evaluation on that evidence. "
                + (
                    ""
                    if preliminary
                    else
                    "A discovery-only paper lacks usable content and cannot "
                    "receive a score of 75 or higher. "
                )
                +
                "Assign relevance_score as an integer from 0 to 100: "
                "90-100 directly addresses both the primary application "
                "or task and the central technical problem in the "
                "research question; 75-89 directly addresses a major "
                "technical dimension and either addresses the application "
                "or provides a concrete, metadata-supported transfer path "
                "from a different application, task, or modality; 50-74 "
                "uses a related mechanism with a plausible but incomplete "
                "transfer path; 25-49 is primarily background or adjacent "
                "research without a specific mechanism-to-problem mapping; "
                "0-24 is weakly related or off-topic. "
                "Before assigning the score, classify mechanism_match as "
                "direct, transferable, adjacent, or none. Use direct only "
                "when the paper's demonstrated mechanism directly addresses "
                "the target problem dimension; use transferable when the "
                "same mechanism is demonstrated in another modality or task "
                "and has a concrete adaptation path; use adjacent for useful "
                "background without a specific mechanism-to-problem mapping; "
                "use none for off-topic work. The classification fixes the "
                "allowed score band: direct 75-100, transferable 50-74, "
                "adjacent 25-49, and none 0-24. "
                "Populate source_mechanism with the paper's actual training "
                "objective or transformation, target_problem_dimension with "
                "the exact research limitation it addresses, "
                "required_adaptation with what must change for the target "
                "setting (or state that none is needed), and evidence_support "
                "with one or more concise facts grounded in the supplied "
                "metadata or evidence sections. For direct and transferable "
                "matches, all four fields must be substantive. "
                "Evaluate the central "
                "technical mechanism before literal task, dataset, or model "
                "name overlap. Do not require a paper to use the same "
                "architecture label as the research question when its "
                "objective and transformation operate on the corresponding "
                "learned representation. In particular, training a student "
                "visual or video encoder to match token-level or feature-level "
                "targets from a frozen vision-language teacher is a concrete "
                "mechanism for aligning learned representations with that "
                "teacher's shared embedding space; do not classify such a "
                "paper as background merely because it uses terms such as "
                "ViT, masked modeling, teacher-student learning, or "
                "distillation instead of autoencoder. A paper applying that "
                "mechanism directly to video addresses a major technical "
                "dimension and ordinarily belongs in the 75-89 band when the "
                "metadata supports the mapping. The analogous mechanism "
                "demonstrated only on images ordinarily belongs in the 50-74 "
                "band unless the supplied evidence establishes a concrete "
                "video transfer path sufficient for a higher score. General "
                "CLIP adaptation, broad multimodal learning, or thematic "
                "alignment terminology without training an external learned "
                "representation into the frozen teacher space remains below "
                "50. Treat explicit seed status or user preference as a "
                "request for careful evaluation, not as evidence and not as "
                "an automatic score increase. Evaluate "
                "transferability explicitly: a different application, "
                "task, or modality must not by itself cap relevance below "
                "75 when the supplied metadata supports an analogous "
                "representation, objective, architecture, or transformation "
                "that directly addresses the central technical problem. "
                "For every score of 50 or higher, research_connections must "
                "identify the paper's source mechanism, the corresponding "
                "dimension of the research question, and any adaptation "
                "needed. If the supplied metadata cannot support that "
                "mapping, assign a score below 50. Do not "
                "assign a high score based primarily on keyword or "
                "topical overlap. "
                "For every score of 75 or higher, state that complete "
                "mechanism-to-question mapping explicitly in "
                "research_connections. Do not assign a score of 75 or "
                "higher when relevance_summary or research_connections says "
                "that a concrete or metadata-supported transfer path is "
                "absent, unclear, or unsupported. "
                "When the supplied metadata indicates that neither a major "
                "dimension nor a concrete transfer "
                "path is present, the relevance score must reflect that "
                "limitation. Use the same relevance "
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
        enforce_evidence: bool = True,
        evaluation_attempt: str = "initial",
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
                self._create_evaluation(
                    paper=paper,
                    mapping=mapping,
                    enforce_evidence=enforce_evidence,
                    evaluation_attempt=evaluation_attempt,
                    batch_source_id=source_id,
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
            or message.startswith(
                "High relevance score requires a concrete, "
                "metadata-supported transfer path:"
            )
            or message.startswith(
                "Mechanism match and relevance score disagree:"
            )
            or message.startswith(
                "Direct or transferable mechanism match requires "
                "structured evidence:"
            )
        )

    def _create_evaluation(
        self,
        paper: PaperMetadata,
        mapping: dict[str, Any],
        enforce_evidence: bool = True,
        evaluation_attempt: str = "initial",
        batch_source_id: str = "unknown",
    ) -> ResearchEvaluation:
        """Create one validated research evaluation."""

        relevance_score = self._parse_score(
            mapping.get("relevance_score")
        )
        relevance_summary = self._require_string(
            mapping,
            "relevance_summary",
        )
        research_connections = self._parse_string_tuple(
            mapping.get("research_connections"),
            "research_connections",
        )
        mechanism_match = self._parse_mechanism_match(
            mapping.get("mechanism_match")
        )
        source_mechanism = self._require_string(
            mapping,
            "source_mechanism",
        )
        target_problem_dimension = self._require_string(
            mapping,
            "target_problem_dimension",
        )
        required_adaptation = self._require_string(
            mapping,
            "required_adaptation",
        )
        evidence_support = self._parse_string_tuple(
            mapping.get("evidence_support"),
            "evidence_support",
        )
        warnings = self._parse_string_tuple(
            mapping.get("warnings"),
            "warnings",
        )

        reconciliation = self._reconcile_mechanism_with_paper_evidence(
            paper=paper,
            mechanism_match=mechanism_match,
            relevance_score=relevance_score,
            relevance_summary=relevance_summary,
            research_connections=research_connections,
            source_mechanism=source_mechanism,
            target_problem_dimension=target_problem_dimension,
            required_adaptation=required_adaptation,
            evidence_support=evidence_support,
        )
        mechanism_match = reconciliation.mechanism_match
        relevance_score = reconciliation.relevance_score
        relevance_summary = reconciliation.relevance_summary
        research_connections = reconciliation.research_connections
        source_mechanism = reconciliation.source_mechanism
        target_problem_dimension = (
            reconciliation.target_problem_dimension
        )
        required_adaptation = reconciliation.required_adaptation
        evidence_support = reconciliation.evidence_support
        if reconciliation.warning is not None:
            warnings = (*warnings, reconciliation.warning)

        validation_error: ValueError | None = None
        try:
            self._validate_mechanism_score_band(
                paper=paper,
                relevance_score=relevance_score,
                mechanism_match=mechanism_match,
            )
            self._validate_structured_mechanism_evidence(
                paper=paper,
                mechanism_match=mechanism_match,
                source_mechanism=source_mechanism,
                target_problem_dimension=target_problem_dimension,
                required_adaptation=required_adaptation,
                evidence_support=evidence_support,
            )

            if enforce_evidence:
                self._validate_high_relevance_transfer_path(
                    paper=paper,
                    relevance_score=relevance_score,
                    relevance_summary=relevance_summary,
                    research_connections=research_connections,
                )
        except ValueError as error:
            validation_error = error

        self._log_evaluation_trace(
            paper=paper,
            batch_source_id=batch_source_id,
            evaluation_attempt=evaluation_attempt,
            enforce_evidence=enforce_evidence,
            relevance_score=relevance_score,
            mechanism_match=mechanism_match,
            source_mechanism=source_mechanism,
            target_problem_dimension=target_problem_dimension,
            required_adaptation=required_adaptation,
            evidence_support=evidence_support,
            validation_error=validation_error,
        )

        if validation_error is not None:
            raise validation_error

        return ResearchEvaluation(
            paper=paper,
            relevance_score=relevance_score,
            relevance_summary=relevance_summary,
            strengths=self._parse_string_tuple(
                mapping.get("strengths"),
                "strengths",
            ),
            limitations=self._parse_string_tuple(
                mapping.get("limitations"),
                "limitations",
            ),
            research_connections=research_connections,
            warnings=warnings,
            mechanism_match=mechanism_match,
            source_mechanism=source_mechanism,
            target_problem_dimension=target_problem_dimension,
            required_adaptation=required_adaptation,
            evidence_support=evidence_support,
        )

    @classmethod
    def _reconcile_mechanism_with_paper_evidence(
        cls,
        *,
        paper: PaperMetadata,
        mechanism_match: ResearchMechanismMatch,
        relevance_score: float | None,
        relevance_summary: str,
        research_connections: tuple[str, ...],
        source_mechanism: str,
        target_problem_dimension: str,
        required_adaptation: str,
        evidence_support: tuple[str, ...],
    ) -> _MechanismReconciliation:
        """Correct provider labels contradicted by explicit paper evidence."""

        evidence_text = cls._paper_mechanism_evidence_text(paper)
        inferred_match = cls._infer_mechanism_match(evidence_text)

        if inferred_match is None or inferred_match is mechanism_match:
            return _MechanismReconciliation(
                mechanism_match=mechanism_match,
                relevance_score=relevance_score,
                relevance_summary=relevance_summary,
                research_connections=research_connections,
                source_mechanism=source_mechanism,
                target_problem_dimension=target_problem_dimension,
                required_adaptation=required_adaptation,
                evidence_support=evidence_support,
            )

        corrected_score = cls._score_for_inferred_match(
            relevance_score,
            inferred_match,
        )
        grounded_support = cls._select_mechanism_evidence(
            paper,
        )
        original_match = mechanism_match

        if inferred_match is ResearchMechanismMatch.DIRECT:
            source_mechanism = (
                "A learned video representation is aligned to a pretrained "
                "foundation-model teacher through token, feature, latent, "
                "or representation matching."
            )
            target_problem_dimension = (
                "Semantic alignment of learned video representations with "
                "a pretrained vision-language embedding space."
            )
            required_adaptation = (
                "Apply the demonstrated video alignment objective to the "
                "target video encoder."
            )
            relevance_summary = (
                "Supplied paper evidence describes a direct teacher-target "
                "alignment mechanism for learned video representations."
            )
        elif inferred_match is ResearchMechanismMatch.TRANSFERABLE:
            source_mechanism = (
                "A learned visual representation is aligned to a pretrained "
                "foundation-model teacher through token, feature, latent, "
                "or representation matching."
            )
            target_problem_dimension = (
                "Semantic alignment of a learned representation with a "
                "pretrained vision-language embedding space."
            )
            required_adaptation = (
                "Extend the demonstrated image alignment objective to "
                "temporally aggregated video representations."
            )
            relevance_summary = (
                "Supplied paper evidence describes a transferable "
                "teacher-target alignment mechanism demonstrated on images."
            )
        else:
            relevance_summary = (
                "Supplied paper evidence supports adjacent vision-language "
                "research but not an external-representation-to-teacher "
                "alignment mechanism."
            )

        connection = (
            "Deterministic evidence screening maps the paper to the "
            f"{inferred_match.value} mechanism band."
        )
        warning = (
            "Mechanism classification corrected deterministically from "
            f"'{original_match.value}' to '{inferred_match.value}' using "
            "supplied paper evidence."
        )
        LOGGER.warning(
            "%s Paper: %s",
            warning,
            paper.title,
        )

        return _MechanismReconciliation(
            mechanism_match=inferred_match,
            relevance_score=corrected_score,
            relevance_summary=relevance_summary,
            research_connections=(*research_connections, connection),
            source_mechanism=source_mechanism,
            target_problem_dimension=target_problem_dimension,
            required_adaptation=required_adaptation,
            evidence_support=grounded_support or evidence_support,
            warning=warning,
        )

    @staticmethod
    def _paper_mechanism_evidence_text(paper: PaperMetadata) -> str:
        """Return normalized title, abstract, and acquired evidence text."""

        parts = [paper.title, paper.abstract or ""]
        parts.extend(section.content for section in paper.evidence_sections)
        return " ".join(part for part in parts if part).lower()

    @staticmethod
    def _infer_mechanism_match(
        evidence_text: str,
    ) -> ResearchMechanismMatch | None:
        """Infer a mechanism band from explicit, general evidence signals."""

        if not evidence_text.strip():
            return None

        has_foundation_target = any(
            marker in evidence_text
            for marker in (
                "clip",
                "foundation model",
                "foundation-model",
                "ifm",
            )
        )
        has_teacher_target_relation = any(
            marker in evidence_text
            for marker in (
                "teacher",
                "frozen",
                "alignment target",
                "prediction target",
                "clip latent as target",
                "clip features as target",
                "clip supervision",
                "semantic guidance",
            )
        ) or re.search(
            r"clip.{0,50}(?:as (?:a |the )?target|target feature)",
            evidence_text,
        ) is not None
        has_alignment_objective = (
            any(
                marker in evidence_text
                for marker in (
                    "align",
                    "distill",
                    "mimic",
                    "matching",
                    "match ",
                    "predict",
                )
            )
            and any(
                marker in evidence_text
                for marker in (
                    "token",
                    "feature",
                    "latent",
                    "representation",
                    "embedding",
                )
            )
        )
        has_external_representation = any(
            marker in evidence_text
            for marker in (
                "autoencoder",
                "student",
                "from scratch",
                "vision transformer",
                "vit model",
                "vit encoder",
                "video encoder",
                "visual encoder",
                "learned representation",
                "unmasked token",
                "masked image modeling",
                "masked video modeling",
            )
        )

        has_complete_mapping = all(
            (
                has_foundation_target,
                has_teacher_target_relation,
                has_alignment_objective,
                has_external_representation,
            )
        )
        if has_complete_mapping:
            if "video" in evidence_text:
                return ResearchMechanismMatch.DIRECT
            return ResearchMechanismMatch.TRANSFERABLE

        has_adjacent_connection = (
            has_foundation_target
            and any(
                marker in evidence_text
                for marker in (
                    "align",
                    "representation",
                    "embedding",
                    "contrastive",
                    "multimodal",
                    "multi-modal",
                    "adaptation",
                    "consistency",
                )
            )
        )
        if has_adjacent_connection:
            return ResearchMechanismMatch.ADJACENT

        return None

    @staticmethod
    def _score_for_inferred_match(
        relevance_score: float | None,
        inferred_match: ResearchMechanismMatch,
    ) -> float:
        """Clamp a provider score into the evidence-derived score band."""

        minimum, maximum = MECHANISM_SCORE_BANDS[inferred_match]
        if relevance_score is None:
            return minimum
        return min(max(relevance_score, minimum), maximum)

    @staticmethod
    def _select_mechanism_evidence(
        paper: PaperMetadata,
    ) -> tuple[str, ...]:
        """Select concise source sentences supporting mechanism inference."""

        source_text = " ".join(
            part
            for part in (
                paper.abstract or "",
                *(section.content for section in paper.evidence_sections),
            )
            if part
        )
        sentences = tuple(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", source_text)
            if sentence.strip()
        )
        selected = tuple(
            sentence
            for sentence in sentences
            if any(
                marker in sentence.lower()
                for marker in (
                    "align",
                    "teacher",
                    "clip",
                    "distill",
                    "latent",
                    "token",
                )
            )
        )
        return selected[:2] or sentences[:1]

    @staticmethod
    def _log_evaluation_trace(
        *,
        paper: PaperMetadata,
        batch_source_id: str,
        evaluation_attempt: str,
        enforce_evidence: bool,
        relevance_score: float | None,
        mechanism_match: ResearchMechanismMatch,
        source_mechanism: str,
        target_problem_dimension: str,
        required_adaptation: str,
        evidence_support: tuple[str, ...],
        validation_error: ValueError | None,
    ) -> None:
        """Log the complete structured mechanism decision for diagnosis."""

        LOGGER.debug(
            "Research evaluation trace: stage=%s attempt=%s "
            "batch_source_id=%s paper_source=%s title=%r "
            "mechanism_match=%s relevance_score=%s "
            "source_mechanism=%r target_problem_dimension=%r "
            "required_adaptation=%r evidence_support=%r "
            "validation_status=%s validation_error=%r",
            "final" if enforce_evidence else "preliminary",
            evaluation_attempt,
            batch_source_id,
            paper.source_reference.source_id,
            paper.title,
            mechanism_match.value,
            relevance_score,
            source_mechanism,
            target_problem_dimension,
            required_adaptation,
            evidence_support,
            "invalid" if validation_error is not None else "valid",
            str(validation_error) if validation_error is not None else None,
        )

    @staticmethod
    def _parse_mechanism_match(value: Any) -> ResearchMechanismMatch:
        """Parse the required mechanism-match classification."""

        if not isinstance(value, str):
            raise TypeError("mechanism_match must be a string.")

        try:
            return ResearchMechanismMatch(value)
        except ValueError as error:
            supported = ", ".join(
                match.value for match in ResearchMechanismMatch
            )
            raise ValueError(
                "mechanism_match must be one of: " + supported
            ) from error

    @staticmethod
    def _validate_mechanism_score_band(
        paper: PaperMetadata,
        relevance_score: float | None,
        mechanism_match: ResearchMechanismMatch,
    ) -> None:
        """Require the numeric score to agree with mechanism strength."""

        if relevance_score is None:
            return

        minimum, maximum = MECHANISM_SCORE_BANDS[mechanism_match]
        if minimum <= relevance_score <= maximum:
            return

        raise ValueError(
            "Mechanism match and relevance score disagree: "
            f"{paper.title!r} classified as {mechanism_match.value!r} "
            f"but received {round(relevance_score * 100)}; expected "
            f"{round(minimum * 100)}-{round(maximum * 100)}."
        )

    @staticmethod
    def _validate_structured_mechanism_evidence(
        paper: PaperMetadata,
        mechanism_match: ResearchMechanismMatch,
        source_mechanism: str,
        target_problem_dimension: str,
        required_adaptation: str,
        evidence_support: tuple[str, ...],
    ) -> None:
        """Require an auditable mapping for meaningful mechanism matches."""

        if mechanism_match not in {
            ResearchMechanismMatch.DIRECT,
            ResearchMechanismMatch.TRANSFERABLE,
        }:
            return

        values = (
            source_mechanism,
            target_problem_dimension,
            required_adaptation,
        )
        if all(value.strip() for value in values) and any(
            item.strip() for item in evidence_support
        ):
            return

        raise ValueError(
            "Direct or transferable mechanism match requires structured "
            f"evidence: {paper.title!r}."
        )

    @staticmethod
    def _validate_high_relevance_transfer_path(
        paper: PaperMetadata,
        relevance_score: float | None,
        relevance_summary: str,
        research_connections: tuple[str, ...],
    ) -> None:
        """Require an explicit transfer path for high relevance scores."""

        if (
            relevance_score is None
            or relevance_score < HIGH_RELEVANCE_SCORE
        ):
            return

        if (
            paper.evidence_status
            == ResearchPaperEvidenceStatus.DISCOVERY_ONLY
            and not paper.abstract
            and not paper.evidence_sections
        ):
            raise ValueError(
                "High relevance score requires a concrete, "
                "metadata-supported transfer path: paper evidence is "
                "discovery-only."
            )

        assessment = " ".join(
            (relevance_summary, *research_connections)
        ).lower()
        has_contradiction = any(
            marker in assessment
            for marker in HIGH_RELEVANCE_CONTRADICTION_MARKERS
        )
        if has_contradiction:
            raise ValueError(
                "High relevance score requires a concrete, "
                "metadata-supported transfer path: "
                "the assessment contradicts that requirement."
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
