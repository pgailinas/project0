# ============================================================
# Project0 - Research Direction Analysis Service
#
# File: research_direction_analysis_service.py
#
# Purpose:
#     Synthesize retained-paper analyses and identify candidate,
#     evidence-grounded Research Agent research directions.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
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
    PaperAnalysis,
    ResearchDirection,
    ResearchDirectionAnalysis,
    ResearchEvidenceReference,
    ResearchEvidenceSourceType,
    ResearchFinding,
    ResearchRequest,
    ResearchSynthesis,
)


LOGGER = logging.getLogger(__name__)


class _SemanticGroundingError(ValueError):
    """Signal a generated claim that is not directly grounded in evidence."""


@dataclass(frozen=True, slots=True)
class _EvidenceCatalogEntry:
    """Provider-facing handle for one supplied evidence-bearing finding."""

    finding: ResearchFinding
    source_type: ResearchEvidenceSourceType
    provider_id: str = ""


class ResearchDirectionAnalysisService:
    """Execute AI-assisted cross-paper synthesis and direction analysis."""

    def __init__(
        self,
        provider: ReasoningProviderProtocol,
        model_name: str,
    ) -> None:
        """Initialize the research direction analysis dependencies."""

        self._provider = provider
        self._model_name = model_name
        self._max_paper_analyses = 3
        self._timeout_seconds = 600.0

    def analyze(
        self,
        request: ResearchRequest,
        context: ExistingResearchContext | None,
        paper_analyses: tuple[PaperAnalysis, ...],
    ) -> ResearchDirectionAnalysis:
        """Synthesize analyzed literature and identify research directions."""

        selected_paper_analyses = paper_analyses[
            :self._max_paper_analyses
        ]

        if len(selected_paper_analyses) < 2:
            return ResearchDirectionAnalysis(
                synthesis=ResearchSynthesis(),
                candidate_directions=(),
            )

        evidence_catalog = self._build_evidence_catalog(
            context=context,
            paper_analyses=selected_paper_analyses,
        )

        provider_request = self._build_provider_request(
            request=request,
            context=context,
            paper_analyses=selected_paper_analyses,
            evidence_catalog=evidence_catalog,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        try:
            return self._create_analysis(
                context=context,
                evidence_catalog=evidence_catalog,
                provider_response=provider_response,
                skip_unsupported_comparisons=False,
            )
        except ValueError as error:
            LOGGER.warning(
                "Research direction analysis response failed structural "
                "or provenance validation; retrying once: %s",
                error,
            )
            validation_error = str(error)

        provider_request = self._build_provider_request(
            request=request,
            context=context,
            paper_analyses=selected_paper_analyses,
            evidence_catalog=evidence_catalog,
            validation_error=validation_error,
        )

        provider_response = self._provider.generate(
            provider_request
        )

        return self._create_analysis(
            context=context,
            evidence_catalog=evidence_catalog,
            provider_response=provider_response,
            skip_unsupported_comparisons=True,
        )

    def _build_evidence_catalog(
        self,
        *,
        context: ExistingResearchContext | None,
        paper_analyses: tuple[PaperAnalysis, ...],
    ) -> dict[str, _EvidenceCatalogEntry]:
        """Create deterministic provider-facing handles for supplied findings."""

        catalog: dict[str, _EvidenceCatalogEntry] = {}

        if context is not None:
            self._add_optional_context_finding(
                catalog,
                "context:research_problem:0",
                context.research_problem,
            )

            for field_name in (
                "prior_work",
                "implemented_approaches",
                "findings",
                "limitations",
                "unresolved_questions",
                "stated_future_work",
            ):
                findings = getattr(context, field_name)
                for index, finding in enumerate(findings):
                    catalog[
                        f"context:{field_name}:{index}"
                    ] = _EvidenceCatalogEntry(
                        finding=finding,
                        source_type=(
                            ResearchEvidenceSourceType.CONTEXT_DOCUMENT
                        ),
                    )

        for paper_index, analysis in enumerate(paper_analyses):
            prefix = f"paper:{paper_index}"

            catalog[f"{prefix}:problem:0"] = _EvidenceCatalogEntry(
                finding=analysis.problem,
                source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
            )
            catalog[f"{prefix}:approach:0"] = _EvidenceCatalogEntry(
                finding=analysis.approach,
                source_type=ResearchEvidenceSourceType.RESEARCH_PAPER,
            )

            for field_name in (
                "representations",
                "modalities",
                "learning_objectives",
                "datasets_tasks",
                "findings",
                "limitations",
            ):
                findings = getattr(analysis, field_name)
                for index, finding in enumerate(findings):
                    catalog[
                        f"{prefix}:{field_name}:{index}"
                    ] = _EvidenceCatalogEntry(
                        finding=finding,
                        source_type=(
                            ResearchEvidenceSourceType.RESEARCH_PAPER
                        ),
                    )

        context_index = 0
        literature_index = 0
        provider_catalog: dict[str, _EvidenceCatalogEntry] = {}

        for finding_id, entry in catalog.items():
            if (
                entry.source_type
                == ResearchEvidenceSourceType.CONTEXT_DOCUMENT
            ):
                context_index += 1
                provider_id = f"context-{context_index:03d}"
            else:
                literature_index += 1
                provider_id = f"literature-{literature_index:03d}"

            provider_catalog[finding_id] = _EvidenceCatalogEntry(
                finding=entry.finding,
                source_type=entry.source_type,
                provider_id=provider_id,
            )

        return provider_catalog

    @staticmethod
    def _add_optional_context_finding(
        catalog: dict[str, _EvidenceCatalogEntry],
        finding_id: str,
        finding: ResearchFinding | None,
    ) -> None:
        """Add one optional context finding to the evidence catalog."""

        if finding is None:
            return

        catalog[finding_id] = _EvidenceCatalogEntry(
            finding=finding,
            source_type=ResearchEvidenceSourceType.CONTEXT_DOCUMENT,
        )

    def _build_provider_request(
        self,
        *,
        request: ResearchRequest,
        context: ExistingResearchContext | None,
        paper_analyses: tuple[PaperAnalysis, ...],
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
        validation_error: str | None = None,
    ) -> ProviderRequest:
        """Build a provider-neutral research direction analysis request."""

        context_payload = (
            self._serialize_context(
                context=context,
                evidence_catalog=evidence_catalog,
            )
            if context is not None
            else None
        )

        paper_payload = [
            self._serialize_paper_analysis(
                paper_index=index,
                analysis=analysis,
                evidence_catalog=evidence_catalog,
            )
            for index, analysis in enumerate(paper_analyses)
        ]

        context_evidence_ids = [
            entry.provider_id
            for entry in evidence_catalog.values()
            if entry.source_type
            == ResearchEvidenceSourceType.CONTEXT_DOCUMENT
        ]
        literature_evidence_ids = [
            entry.provider_id
            for entry in evidence_catalog.values()
            if entry.source_type
            == ResearchEvidenceSourceType.RESEARCH_PAPER
        ]

        user_prompt = json.dumps(
            {
                "research_request": {
                    "question": request.question,
                    "guidance": request.guidance,
                    "constraints": list(request.constraints),
                    "focus_areas": list(request.focus_areas),
                },
                "allowed_evidence_ids": {
                    "context_evidence_ids": context_evidence_ids,
                    "literature_evidence_ids": literature_evidence_ids,
                },
                "validation_feedback": validation_error,
                "existing_research_context": context_payload,
                "paper_analyses": paper_payload,
            },
            indent=2,
        )

        synthesis_item_schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "evidence_ids": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": literature_evidence_ids,
                    },
                    "uniqueItems": True,
                    "maxItems": len(paper_analyses),
                },
            },
            "required": ["content", "evidence_ids"],
        }

        direction_schema = {
            "type": "object",
            "properties": {
                "direction": {"type": "string"},
                "rationale": {"type": "string"},
                "context_evidence_ids": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": context_evidence_ids,
                    },
                    "uniqueItems": True,
                },
                "literature_evidence_ids": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": literature_evidence_ids,
                    },
                    "uniqueItems": True,
                    "maxItems": len(paper_analyses),
                },
                "speculative": {"type": "boolean"},
            },
            "required": [
                "direction",
                "rationale",
                "context_evidence_ids",
                "literature_evidence_ids",
                "speculative",
            ],
        }

        response_schema = {
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "object",
                    "properties": {
                        "themes": {
                            "type": "array",
                            "items": synthesis_item_schema,
                        },
                        "comparisons": {
                            "type": "array",
                            "items": synthesis_item_schema,
                        },
                        "shared_limitations": {
                            "type": "array",
                            "items": synthesis_item_schema,
                        },
                        "unresolved_questions": {
                            "type": "array",
                            "items": synthesis_item_schema,
                        },
                    },
                    "required": [
                        "themes",
                        "comparisons",
                        "shared_limitations",
                        "unresolved_questions",
                    ],
                },
                "candidate_directions": {
                    "type": "array",
                    "items": direction_schema,
                },
            },
            "required": ["synthesis", "candidate_directions"],
        }

        return ProviderRequest(
            system_instructions=(
                "You are the Project0 Research Agent research direction "
                "analysis service. Use only the supplied structured existing "
                "research context and retained-paper analyses. Do not use "
                "outside knowledge. Synthesize the analyzed papers into "
                "concise themes, comparisons, shared limitations, and "
                "unresolved questions, then propose candidate research "
                "directions relevant to the supplied research request. "
                "Every synthesis item must be supported by supplied paper "
                "evidence identifiers. Each cited evidence identifier must "
                "directly support the specific claim content; do not cite an "
                "identifier merely because it is topically related. Explicit performance "
                "ordering claims such as better, worse, higher, lower, "
                "outperforms, or underperforms must be directly stated by "
                "the cited literature findings; do not infer, reverse, or "
                "import such comparisons from existing research context. "
                "Use the smallest sufficient evidence set and never bulk-cite all "
                "available identifiers. Synthesis fields are literature-only: "
                "do not restate an existing-context claim as synthesis unless "
                "the same claim is independently supported by the cited paper "
                "findings. Themes, comparisons, and shared limitations must be "
                "supported by findings from at least two distinct papers. "
                "Scope claims to the analyzed evidence. Do "
                "not infer absence from the broader literature merely because "
                "something is absent from the supplied analyses. Do not claim "
                "novelty, no prior work, or a global research gap unless such "
                "a broader claim is explicitly supported by supplied evidence. "
                "For candidate directions, cite only findings that directly "
                "support the direction and rationale. Use context_evidence_ids "
                "only for claims supported by existing research context, and "
                "use literature_evidence_ids only for claims supported by "
                "retained-paper findings. Use context_evidence_ids only from "
                "allowed_evidence_ids.context_evidence_ids and use "
                "literature_evidence_ids only from "
                "allowed_evidence_ids.literature_evidence_ids. When existing "
                "research context is supplied, a non-speculative candidate "
                "direction must connect at least one context finding with at "
                "least one literature finding. Without existing "
                "research context, non-speculative directions must still be "
                "grounded in literature evidence and must return no context "
                "evidence identifiers. Speculative directions are allowed only "
                "as explicitly labeled, evidence-anchored extrapolations. Do "
                "not invent unsupported ideas merely by marking them "
                "speculative. Treat every supplied finding_id as an opaque "
                "identifier and return it exactly as supplied. Do not invent, "
                "modify, normalize, or expand evidence identifiers."
            ),
            user_prompt=user_prompt,
            response_schema=response_schema,
            model_name=self._model_name,
            temperature=0.0,
            metadata={
                "research_request_id": request.request_id,
                "paper_analysis_count": len(paper_analyses),
                "has_existing_research_context": context is not None,
                "timeout_seconds": self._timeout_seconds,
                "debug_capture_path": (
                    "/tmp/project0_direction_analysis_request.json"
                ),
            },
        )

    def _serialize_context(
        self,
        *,
        context: ExistingResearchContext,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
    ) -> dict[str, Any]:
        """Serialize existing research context with provider-facing handles."""

        result: dict[str, Any] = {
            "research_problem": self._serialize_optional_catalog_finding(
                evidence_catalog,
                "context:research_problem:0",
            )
        }

        for field_name in (
            "prior_work",
            "implemented_approaches",
            "findings",
            "limitations",
            "unresolved_questions",
            "stated_future_work",
        ):
            result[field_name] = [
                self._serialize_catalog_finding(
                    evidence_catalog,
                    f"context:{field_name}:{index}",
                )
                for index, _ in enumerate(getattr(context, field_name))
            ]

        return result

    def _serialize_paper_analysis(
        self,
        *,
        paper_index: int,
        analysis: PaperAnalysis,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
    ) -> dict[str, Any]:
        """Serialize one retained-paper analysis with finding handles."""

        prefix = f"paper:{paper_index}"
        result: dict[str, Any] = {
            "source_id": analysis.paper.source_reference.source_id,
            "title": analysis.paper.title,
            "analysis_basis": analysis.analysis_basis,
            "problem": self._serialize_catalog_finding(
                evidence_catalog,
                f"{prefix}:problem:0",
            ),
            "approach": self._serialize_catalog_finding(
                evidence_catalog,
                f"{prefix}:approach:0",
            ),
            "warnings": list(analysis.warnings),
        }

        for field_name in (
            "representations",
            "modalities",
            "learning_objectives",
            "datasets_tasks",
            "findings",
            "limitations",
        ):
            result[field_name] = [
                self._serialize_catalog_finding(
                    evidence_catalog,
                    f"{prefix}:{field_name}:{index}",
                )
                for index, _ in enumerate(getattr(analysis, field_name))
            ]

        return result

    @staticmethod
    def _serialize_catalog_finding(
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
        finding_id: str,
    ) -> dict[str, str]:
        """Serialize one catalog finding."""

        entry = evidence_catalog[finding_id]
        return {
            "finding_id": entry.provider_id,
            "content": entry.finding.content,
        }

    @classmethod
    def _serialize_optional_catalog_finding(
        cls,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
        finding_id: str,
    ) -> dict[str, str] | None:
        """Serialize one optional catalog finding."""

        if finding_id not in evidence_catalog:
            return None

        return cls._serialize_catalog_finding(
            evidence_catalog,
            finding_id,
        )

    def _create_analysis(
        self,
        *,
        context: ExistingResearchContext | None,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
        provider_response: ProviderResponse,
        skip_unsupported_comparisons: bool,
    ) -> ResearchDirectionAnalysis:
        """Create a research direction analysis from structured output."""

        structured_output = provider_response.structured_output

        if structured_output is None:
            raise ValueError(
                "Provider response did not include structured output."
            )

        if not isinstance(structured_output, dict):
            raise ValueError(
                "Provider structured output must be an object."
            )

        synthesis_value = structured_output.get("synthesis")
        if not isinstance(synthesis_value, dict):
            raise ValueError(
                "Provider field 'synthesis' must be an object."
            )

        maximum_literature_evidence_ids = (
            self._count_distinct_literature_sources(evidence_catalog)
        )

        synthesis = ResearchSynthesis(
            themes=self._parse_synthesis_findings(
                value=synthesis_value.get("themes"),
                field_name="themes",
                evidence_catalog=evidence_catalog,
                minimum_distinct_papers=2,
                maximum_evidence_ids=maximum_literature_evidence_ids,
                skip_unsupported_comparisons=skip_unsupported_comparisons,
            ),
            comparisons=self._parse_synthesis_findings(
                value=synthesis_value.get("comparisons"),
                field_name="comparisons",
                evidence_catalog=evidence_catalog,
                minimum_distinct_papers=2,
                maximum_evidence_ids=maximum_literature_evidence_ids,
                skip_unsupported_comparisons=skip_unsupported_comparisons,
            ),
            shared_limitations=self._parse_synthesis_findings(
                value=synthesis_value.get("shared_limitations"),
                field_name="shared_limitations",
                evidence_catalog=evidence_catalog,
                minimum_distinct_papers=2,
                maximum_evidence_ids=maximum_literature_evidence_ids,
                skip_unsupported_comparisons=skip_unsupported_comparisons,
            ),
            unresolved_questions=self._parse_synthesis_findings(
                value=synthesis_value.get("unresolved_questions"),
                field_name="unresolved_questions",
                evidence_catalog=evidence_catalog,
                minimum_distinct_papers=1,
                maximum_evidence_ids=maximum_literature_evidence_ids,
                skip_unsupported_comparisons=skip_unsupported_comparisons,
            ),
        )

        candidate_directions = self._parse_directions(
            value=structured_output.get("candidate_directions"),
            context=context,
            evidence_catalog=evidence_catalog,
            maximum_literature_evidence_ids=(
                maximum_literature_evidence_ids
            ),
        )

        return ResearchDirectionAnalysis(
            synthesis=synthesis,
            candidate_directions=candidate_directions,
        )

    def _parse_synthesis_findings(
        self,
        *,
        value: Any,
        field_name: str,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
        minimum_distinct_papers: int,
        maximum_evidence_ids: int,
        skip_unsupported_comparisons: bool,
    ) -> tuple[ResearchFinding, ...]:
        """Parse one collection of evidence-grounded synthesis findings."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        findings: list[ResearchFinding] = []

        for item in value:
            try:
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Provider field '{field_name}' findings must be objects."
                    )

                content = self._require_non_empty_string(
                    item.get("content"),
                    f"{field_name}.content",
                )
                evidence_ids = self._parse_evidence_ids(
                    item.get("evidence_ids"),
                    f"{field_name}.evidence_ids",
                    maximum_count=maximum_evidence_ids,
                )

                evidence = self._resolve_evidence(
                    evidence_ids=evidence_ids,
                    field_name=f"{field_name}.evidence_ids",
                    expected_source_type=(
                        ResearchEvidenceSourceType.RESEARCH_PAPER
                    ),
                    evidence_catalog=evidence_catalog,
                )

                if field_name == "comparisons":
                    self._validate_explicit_performance_comparison(
                        content=content,
                        evidence_ids=evidence_ids,
                        evidence_catalog=evidence_catalog,
                    )

                distinct_papers = {
                    reference.source_id
                    for reference in evidence
                    if reference.source_type
                    == ResearchEvidenceSourceType.RESEARCH_PAPER
                }

                if len(distinct_papers) < minimum_distinct_papers:
                    raise ValueError(
                        f"Provider field '{field_name}' requires evidence from "
                        f"at least {minimum_distinct_papers} distinct paper"
                        f"{'s' if minimum_distinct_papers != 1 else ''}."
                    )

                findings.append(
                    ResearchFinding(
                        content=content,
                        evidence=evidence,
                    )
                )
            except _SemanticGroundingError as error:
                if not skip_unsupported_comparisons:
                    raise

                LOGGER.warning(
                    "Skipping semantically ungrounded research direction "
                    "synthesis finding for field '%s' after the corrective "
                    "retry: %s",
                    field_name,
                    error,
                )
            except ValueError as error:
                LOGGER.warning(
                    "Skipping invalid research direction synthesis finding "
                    "for field '%s': %s",
                    field_name,
                    error,
                )

        return tuple(findings)

    def _parse_directions(
        self,
        *,
        value: Any,
        context: ExistingResearchContext | None,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
        maximum_literature_evidence_ids: int,
    ) -> tuple[ResearchDirection, ...]:
        """Parse candidate research directions."""

        if not isinstance(value, list):
            raise ValueError(
                "Provider field 'candidate_directions' must be an array."
            )

        directions: list[ResearchDirection] = []

        for item in value:
            if not isinstance(item, dict):
                raise ValueError(
                    "Provider field 'candidate_directions' items must be "
                    "objects."
                )

            direction = self._require_non_empty_string(
                item.get("direction"),
                "candidate_directions.direction",
            )
            rationale = self._require_non_empty_string(
                item.get("rationale"),
                "candidate_directions.rationale",
            )

            speculative = item.get("speculative")
            if not isinstance(speculative, bool):
                raise ValueError(
                    "Provider field 'candidate_directions.speculative' "
                    "must be a boolean."
                )

            context_ids = self._parse_candidate_evidence_ids(
                item.get("context_evidence_ids"),
                "candidate_directions.context_evidence_ids",
            )
            literature_ids = self._parse_candidate_evidence_ids(
                item.get("literature_evidence_ids"),
                "candidate_directions.literature_evidence_ids",
                maximum_count=maximum_literature_evidence_ids,
            )

            context_evidence = self._resolve_evidence(
                evidence_ids=context_ids,
                field_name="candidate_directions.context_evidence_ids",
                expected_source_type=(
                    ResearchEvidenceSourceType.CONTEXT_DOCUMENT
                ),
                evidence_catalog=evidence_catalog,
            )
            literature_evidence = self._resolve_evidence(
                evidence_ids=literature_ids,
                field_name="candidate_directions.literature_evidence_ids",
                expected_source_type=(
                    ResearchEvidenceSourceType.RESEARCH_PAPER
                ),
                evidence_catalog=evidence_catalog,
            )

            if context is None and context_evidence:
                raise ValueError(
                    "Candidate direction returned context evidence when no "
                    "existing research context was supplied."
                )

            if not speculative:
                if context is not None and not context_evidence:
                    raise ValueError(
                        "Non-speculative candidate direction requires context "
                        "evidence when existing research context is supplied."
                    )

                if not literature_evidence:
                    raise ValueError(
                        "Non-speculative candidate direction requires "
                        "literature evidence."
                    )
            elif not context_evidence and not literature_evidence:
                raise ValueError(
                    "Speculative candidate direction requires an evidence "
                    "anchor."
                )

            directions.append(
                ResearchDirection(
                    direction=direction,
                    rationale=rationale,
                    context_evidence=context_evidence,
                    literature_evidence=literature_evidence,
                    speculative=speculative,
                )
            )

        return tuple(directions)

    def _validate_explicit_performance_comparison(
        self,
        *,
        content: str,
        evidence_ids: tuple[str, ...],
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
    ) -> None:
        """Reject unsupported explicit performance-ordering comparisons."""

        claim_polarities = self._performance_comparison_polarities(content)

        if not claim_polarities:
            return

        evidence_polarities: set[str] = set()

        for evidence_id in evidence_ids:
            entry = next(
                (
                    catalog_entry
                    for catalog_entry in evidence_catalog.values()
                    if catalog_entry.provider_id == evidence_id
                ),
                None,
            )

            if entry is not None:
                evidence_polarities.update(
                    self._performance_comparison_polarities(
                        entry.finding.content
                    )
                )

        if not claim_polarities.issubset(evidence_polarities):
            raise _SemanticGroundingError(
                "Provider field 'comparisons.content' makes an explicit "
                "performance-ordering claim that is not directly stated by "
                "the cited literature evidence."
            )

    @staticmethod
    def _performance_comparison_polarities(
        value: str,
    ) -> set[str]:
        """Return explicit positive or negative performance comparison cues."""

        positive_patterns = (
            r"\bbetter\b",
            r"\boutperform(?:s|ed|ing)?\b",
            r"\bhigher\b",
            r"\bsuperior\b",
            r"\bexceed(?:s|ed|ing)?\b",
            r"\bsurpass(?:es|ed|ing)?\b",
        )
        negative_patterns = (
            r"\bworse\b",
            r"\bunderperform(?:s|ed|ing)?\b",
            r"\blower\b",
            r"\binferior\b",
        )
        normalized = value.casefold()
        polarities: set[str] = set()

        if any(re.search(pattern, normalized) for pattern in positive_patterns):
            polarities.add("positive")
        if any(re.search(pattern, normalized) for pattern in negative_patterns):
            polarities.add("negative")

        return polarities

    @staticmethod
    def _parse_candidate_evidence_ids(
        value: Any,
        field_name: str,
        *,
        maximum_count: int | None = None,
    ) -> tuple[str, ...]:
        """Parse and validate provider-returned candidate evidence handles."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        if not all(isinstance(item, str) for item in value):
            raise ValueError(
                f"Provider field '{field_name}' must contain strings only."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                f"Provider field '{field_name}' must not contain duplicates."
            )

        if maximum_count is not None and len(value) > maximum_count:
            raise ValueError(
                f"Provider field '{field_name}' must contain no more than "
                f"{maximum_count} evidence identifiers."
            )

        return tuple(value)

    @staticmethod
    def _parse_evidence_ids(
        value: Any,
        field_name: str,
        *,
        maximum_count: int | None = None,
    ) -> tuple[str, ...]:
        """Parse and validate provider-returned evidence handles."""

        if not isinstance(value, list):
            raise ValueError(
                f"Provider field '{field_name}' must be an array."
            )

        if not all(isinstance(item, str) for item in value):
            raise ValueError(
                f"Provider field '{field_name}' must contain strings only."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                f"Provider field '{field_name}' must not contain duplicates."
            )

        if maximum_count is not None and len(value) > maximum_count:
            raise ValueError(
                f"Provider field '{field_name}' must contain no more than "
                f"{maximum_count} evidence identifiers."
            )

        return tuple(value)

    @staticmethod
    def _count_distinct_literature_sources(
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
    ) -> int:
        """Count distinct retained-paper sources represented in the catalog."""

        return len(
            {
                reference.source_id
                for entry in evidence_catalog.values()
                if entry.source_type
                == ResearchEvidenceSourceType.RESEARCH_PAPER
                for reference in entry.finding.evidence
                if reference.source_type
                == ResearchEvidenceSourceType.RESEARCH_PAPER
            }
        )

    def _resolve_evidence(
        self,
        *,
        evidence_ids: tuple[str, ...],
        field_name: str,
        expected_source_type: ResearchEvidenceSourceType,
        evidence_catalog: dict[str, _EvidenceCatalogEntry],
    ) -> tuple[ResearchEvidenceReference, ...]:
        """Resolve provider handles to original supplied evidence references."""

        resolved: list[ResearchEvidenceReference] = []

        for evidence_id in evidence_ids:
            entry = next(
                (
                    catalog_entry
                    for catalog_entry in evidence_catalog.values()
                    if catalog_entry.provider_id == evidence_id
                ),
                None,
            )

            if entry is None:
                raise ValueError(
                    f"Provider field '{field_name}' referenced unknown "
                    f"evidence identifier: {evidence_id}"
                )

            if entry.source_type != expected_source_type:
                raise ValueError(
                    f"Provider field '{field_name}' referenced evidence from "
                    "the wrong source type."
                )

            for reference in entry.finding.evidence:
                if reference.source_type != expected_source_type:
                    raise ValueError(
                        f"Provider field '{field_name}' resolved to evidence "
                        "with the wrong source type."
                    )

                if reference not in resolved:
                    resolved.append(reference)

        return tuple(resolved)

    @staticmethod
    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        """Return one required non-empty provider string."""

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Provider field '{field_name}' must be a non-empty string."
            )

        return value.strip()
