# ============================================================
# Project0 - Documentation Workflow
#
# File: documentation_workflow.py
#
# Purpose:
#     Coordinate reasoning, validation, individual review,
#     approved repository updates, Git diff generation, and
#     documentation workflow completion reporting.
#
# ============================================================

from __future__ import annotations

from collections.abc import Callable
import ast
from datetime import UTC, datetime
import logging
from pathlib import Path
import re
import textwrap

from project0.interfaces.artifact_interfaces import (
    ArtifactLocationServiceInterface,
)
from project0.models.artifact_models import (
    ArtifactLocation,
    ArtifactLocationType,
)
from project0.interfaces.documentation_workflow_interfaces import (
    GitDiffInterface,
    RepositoryUpdateInterface,
    ReviewCoordinatorInterface,
)
from project0.interfaces.reasoning_interfaces import (
    ReasoningServiceProtocol,
)
from project0.interfaces.validation_interfaces import (
    ValidationInterface,
)
from project0.models.documentation_workflow_models import (
    AppliedDocumentationChange,
    ChangeApplicationStatus,
    DocumentationAnchorMode,
    DocumentationChangeProposal,
    DocumentationReview,
    DocumentationWorkflowRequest,
    DocumentationWorkflowResult,
    DocumentationWorkflowState,
    DocumentationWorkflowStatus,
    DocumentationWorkflowSummary,
    ReviewDecision,
)
from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    DocumentationEditType,
    DocumentationGap,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)
from project0.models.validation_models import (
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
)
from project0.skills.skill_registry import SkillRegistry


logger = logging.getLogger(__name__)


ContextProvider = Callable[[DocumentationWorkflowRequest], str]


_STRICT_DOCUMENTATION_SKILL_NAME = "strict-documentation-editor"


_PROPOSED_CONTENT_META_INSTRUCTION_PATTERNS = (
    re.compile(r"^\s*add\s+(?:a\s+|an\s+|the\s+|new\s+)?sections?\b", re.IGNORECASE),
    re.compile(r"^\s*consider\s+adding\b", re.IGNORECASE),
    re.compile(r"^\s*include\s+examples?\b", re.IGNORECASE),
    re.compile(r"^\s*explain\b", re.IGNORECASE),
    re.compile(r"^\s*describe\b", re.IGNORECASE),
    re.compile(r"^\s*document\b", re.IGNORECASE),
    re.compile(r"^\s*update\s+the\s+documentation\b", re.IGNORECASE),
    re.compile(r"^\s*add\s+documentation\b", re.IGNORECASE),
)


_DOCUMENTATION_MEANING_RATIONALE_PATTERNS = (
    re.compile(r"^\s*this\s+change\b", re.IGNORECASE),
    re.compile(r"^\s*this\s+update\b", re.IGNORECASE),
    re.compile(r"^\s*this\s+will\b", re.IGNORECASE),
    re.compile(r"^\s*this\s+ensures?\b", re.IGNORECASE),
)


_SECTION_SEMANTIC_STOP_WORDS = frozenset(
    {
        "agent",
        "behavior",
        "change",
        "class",
        "code",
        "contract",
        "current",
        "document",
        "documentation",
        "implemented",
        "implementation",
        "interface",
        "method",
        "proposed",
        "research",
        "section",
        "update",
        "updated",
    }
)


class DocumentationWorkflow:
    """Coordinate the complete documentation update workflow."""

    def __init__(
        self,
        repository_root: Path,
        context_provider: ContextProvider,
        reasoning_service: ReasoningServiceProtocol,
        artifact_location_service: ArtifactLocationServiceInterface,
        validation_service: ValidationInterface,
        review_coordinator: ReviewCoordinatorInterface,
        repository_update_service: RepositoryUpdateInterface,
        git_diff_service: GitDiffInterface,
        skill_registry: SkillRegistry | None = None,
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._context_provider = context_provider
        self._reasoning_service = reasoning_service
        self._artifact_location_service = artifact_location_service
        self._validation_service = validation_service
        self._review_coordinator = review_coordinator
        self._repository_update_service = repository_update_service
        self._git_diff_service = git_diff_service
        self._skill_registry = skill_registry
        self._workflow_states: dict[str, DocumentationWorkflowState] = {}

    def execute(
        self,
        request: DocumentationWorkflowRequest,
    ) -> DocumentationWorkflowResult:
        """Execute a documentation workflow until review or completion."""

        started_at = datetime.now(UTC)
        reasoning_result: ReasoningResult | None = None
        proposals: tuple[DocumentationChangeProposal, ...] = ()
        preliminary_validation: ValidationResult | None = None
        warnings: list[str] = []

        try:
            context = self._context_provider(request)

            active_skills = ()
            if request.source_paths and self._skill_registry is not None:
                active_skills = (
                    self._skill_registry.load(
                        _STRICT_DOCUMENTATION_SKILL_NAME
                    ),
                )

            reasoning_constraints = ()
            if not active_skills:
                reasoning_constraints = (
                    "Modify Markdown documentation only.",
                    "Preserve existing documentation style.",
                    "Make the minimum necessary changes.",
                    "Do not invent project information.",
                    (
                        "Ground Truth Source Paths are read-only "
                        "authoritative evidence and must not be "
                        "proposed for modification."
                    ),
                    (
                        "When target documentation paths are "
                        "provided, propose changes only to those "
                        "target paths."
                    ),
                )

            source_grounded = bool(request.source_paths)
            target_paths = tuple(
                Path(repository_path)
                for repository_path in request.target_paths
            )

            if source_grounded:
                gap_context = self._build_claim_level_gap_context(context)

                gap_result = self._reasoning_service.reason(
                    ReasoningRequest(
                        objective=request.user_request,
                        context=gap_context,
                        workflow_type="documentation_gap_analysis",
                        target_paths=target_paths,
                        constraints=(),
                        skills=(),
                        metadata={
                            "workflow_id": request.workflow_id,
                            "documentation_stage": "gap_analysis",
                        },
                    )
                )

                self._log_reasoning_result(
                    "Documentation gap analysis",
                    gap_result,
                )

                if gap_result.status is ReasoningStatus.FAILED:
                    return self._failed_result(
                        request=request,
                        started_at=started_at,
                        reasoning_result=gap_result,
                        error_message=(
                            gap_result.error_message
                            or "Documentation gap analysis failed."
                        ),
                        warnings=gap_result.warnings,
                    )

                warnings.extend(
                    self._select_reasoning_warnings(
                        reasoning_result=gap_result,
                        source_grounded=True,
                    )
                )

                if not gap_result.gaps:
                    state = DocumentationWorkflowState(
                        workflow_id=request.workflow_id,
                        status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                        started_at=started_at,
                        user_request=request.user_request,
                        target_paths=request.target_paths,
                        source_paths=request.source_paths,
                        reasoning_result=gap_result,
                        proposals=(),
                        preliminary_validation=None,
                        warnings=tuple(warnings),
                    )

                    self._workflow_states[request.workflow_id] = state

                    return self._create_review_required_result(state)

                established_gaps = self._deduplicate_documentation_gaps(
                    gap_result.gaps
                )

                context = (
                    f"{context.rstrip()}\n\n"
                    f"{self._format_established_gaps(established_gaps)}"
                )

            reasoning_result = self._reasoning_service.reason(
                ReasoningRequest(
                    objective=request.user_request,
                    context=context,
                    workflow_type="documentation_update",
                    target_paths=target_paths,
                    constraints=reasoning_constraints,
                    skills=active_skills,
                    metadata={
                        "workflow_id": request.workflow_id,
                        "documentation_stage": (
                            "proposal_generation"
                            if source_grounded
                            else "single_stage"
                        ),
                    },
                )
            )

            self._log_reasoning_result(
                "Documentation proposal generation",
                reasoning_result,
            )

            if reasoning_result.status is ReasoningStatus.FAILED:
                return self._failed_result(
                    request=request,
                    started_at=started_at,
                    reasoning_result=reasoning_result,
                    error_message=(
                        reasoning_result.error_message
                        or "Documentation reasoning failed."
                    ),
                    warnings=reasoning_result.warnings,
                )

            warnings.extend(
                self._select_reasoning_warnings(
                    reasoning_result=reasoning_result,
                    source_grounded=source_grounded,
                )
            )

            proposals, proposal_warnings = self._build_proposals(
                reasoning_result=reasoning_result,
                target_paths=request.target_paths,
                source_grounded=source_grounded,
                context=context,
            )
            warnings.extend(proposal_warnings)

            if not proposals:
                state = DocumentationWorkflowState(
                    workflow_id=request.workflow_id,
                    status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                    started_at=started_at,
                    user_request=request.user_request,
                    target_paths=request.target_paths,
                    source_paths=request.source_paths,
                    reasoning_result=reasoning_result,
                    proposals=(),
                    preliminary_validation=None,
                    warnings=tuple(warnings),
                )

                self._workflow_states[request.workflow_id] = state

                return self._create_review_required_result(state)

            preliminary_validation = self._validate_paths(
                tuple(
                    proposal.repository_path
                    for proposal in proposals
                ),
                request.workflow_id,
            )

            if preliminary_validation.status is ValidationStatus.FAILED:
                state = DocumentationWorkflowState(
                    workflow_id=request.workflow_id,
                    status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                    started_at=started_at,
                    user_request=request.user_request,
                    target_paths=request.target_paths,
                    source_paths=request.source_paths,
                    reasoning_result=reasoning_result,
                    proposals=proposals,
                    preliminary_validation=preliminary_validation,
                    warnings=tuple(
                        [
                            *warnings,
                            "Preliminary documentation validation failed.",
                        ]
                    ),
                    error_message=(
                        "Preliminary documentation validation failed."
                    ),
                )

                self._workflow_states[request.workflow_id] = state

                return self._create_review_required_result(state)

            if (
                preliminary_validation.status
                is ValidationStatus.PASSED_WITH_WARNINGS
            ):
                warnings.append(
                    "Preliminary validation completed with warnings."
                )

            state = DocumentationWorkflowState(
                workflow_id=request.workflow_id,
                status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                started_at=started_at,
                user_request=request.user_request,
                target_paths=request.target_paths,
                source_paths=request.source_paths,
                reasoning_result=reasoning_result,
                proposals=proposals,
                preliminary_validation=preliminary_validation,
                warnings=tuple(warnings),
            )
            self._workflow_states[request.workflow_id] = state

            return self._create_review_required_result(state)

        except (OSError, RuntimeError, TypeError, ValueError) as error:
            return self._failed_result(
                request=request,
                started_at=started_at,
                reasoning_result=reasoning_result,
                proposals=proposals,
                preliminary_validation=preliminary_validation,
                error_message=str(error),
                warnings=tuple(warnings),
            )


    @staticmethod
    def _build_claim_level_gap_context(
        context: str,
    ) -> str:
        """Add exact target-document claim candidates for Stage 1 comparison.

        Claim candidates preserve target wording and section ownership while
        excluding headings, blank lines, fenced code, and context metadata.
        The authoritative source content remains unchanged in the original
        context so reasoning can compare each candidate against source evidence.
        """

        target_marker = "=== TARGET DOCUMENTATION ==="
        source_marker = "=== AUTHORITATIVE SOURCE ==="

        if target_marker not in context or source_marker not in context:
            return context

        claims: list[tuple[str | None, str]] = []
        in_target = False
        in_fence = False
        current_section: str | None = None

        for line in context.splitlines():
            stripped = line.strip()

            if stripped == target_marker:
                in_target = True
                in_fence = False
                current_section = None
                continue

            if stripped == source_marker:
                in_target = False
                in_fence = False
                current_section = None
                continue

            if stripped.startswith("=== ") and stripped.endswith(" ==="):
                in_target = False
                in_fence = False
                current_section = None
                continue

            if not in_target:
                continue

            if stripped.startswith("```"):
                in_fence = not in_fence
                continue

            if in_fence or not stripped or stripped.startswith("Path: "):
                continue

            if stripped.startswith("#"):
                marker_length = len(stripped) - len(
                    stripped.lstrip("#")
                )
                remainder = stripped[marker_length:]
                if (
                    1 <= marker_length <= 6
                    and remainder.startswith(" ")
                ):
                    current_section = remainder.strip()
                continue

            if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?", stripped):
                continue

            claim_text = stripped

            if claim_text.startswith(("- ", "* ", "+ ")):
                claim_text = claim_text[2:].strip()

            if re.match(r"^\d+[.)]\s+", claim_text):
                claim_text = re.sub(
                    r"^\d+[.)]\s+",
                    "",
                    claim_text,
                    count=1,
                ).strip()

            if not claim_text:
                continue

            claims.append((current_section, claim_text))

        if not claims:
            return context

        lines = [
            context.rstrip(),
            "",
            "=== TARGET DOCUMENTATION CLAIM CANDIDATES ===",
            (
                "Evaluate these exact target claims before considering "
                "undocumented source details. Preserve their wording when "
                "describing contradictions."
            ),
        ]

        for index, (section, claim_text) in enumerate(claims, start=1):
            lines.extend(
                (
                    f"Claim {index}:",
                    f"Section: {section if section is not None else 'null'}",
                    f"Text: {claim_text}",
                )
            )

        return "\n".join(lines)

    @staticmethod
    def _deduplicate_documentation_gaps(
        gaps: tuple[DocumentationGap, ...],
    ) -> tuple[DocumentationGap, ...]:
        """Return Stage 1 gaps with exact semantic duplicates removed."""

        deduplicated: list[DocumentationGap] = []
        seen: set[tuple[str, str | None, str, str]] = set()

        for gap in gaps:
            key = (
                gap.document_path.as_posix(),
                gap.section.strip() if gap.section is not None else None,
                " ".join(gap.gap.split()),
                " ".join(gap.source_evidence.split()),
            )

            if key in seen:
                continue

            seen.add(key)
            deduplicated.append(gap)

        return tuple(deduplicated)

    @staticmethod
    def _format_established_gaps(
        gaps: tuple[DocumentationGap, ...],
    ) -> str:
        """Format Stage 1 gaps as bounded input for proposal generation."""

        lines = ["=== ESTABLISHED DOCUMENTATION GAPS ==="]

        for index, gap in enumerate(gaps, start=1):
            lines.extend(
                (
                    f"Gap {index}:",
                    f"Document Path: {gap.document_path.as_posix()}",
                    f"Section: {gap.section if gap.section is not None else 'null'}",
                    f"Gap: {gap.gap}",
                    f"Source Evidence: {gap.source_evidence}",
                )
            )

        lines.append(
            "Generate documentation edits only for the established gaps above. "
            "Do not introduce additional gaps, requirements, or design changes."
        )

        return "\n".join(lines)

    @staticmethod
    def _log_reasoning_result(
        label: str,
        reasoning_result: ReasoningResult,
    ) -> None:
        """Log one reasoning-stage result before workflow filtering."""

        logger.debug(
            "%s result summary=%r gaps=%r impacts=%r warnings=%r metadata=%r",
            label,
            reasoning_result.summary,
            reasoning_result.gaps,
            reasoning_result.impacts,
            reasoning_result.warnings,
            reasoning_result.metadata,
        )

        for index, proposed_change in enumerate(
            reasoning_result.proposed_changes,
            start=1,
        ):
            logger.debug(
                "%s proposed_change[%d] "
                "document_path=%r operation=%r rationale=%r "
                "documentation_meaning=%r proposed_content=%r "
                "section=%r anchor_text=%r edit_type=%r "
                "confidence=%r",
                label,
                index,
                proposed_change.document_path.as_posix(),
                proposed_change.operation.value,
                proposed_change.rationale,
                proposed_change.documentation_meaning,
                proposed_change.proposed_content,
                proposed_change.section,
                proposed_change.anchor_text,
                proposed_change.edit_type.value,
                proposed_change.confidence,
            )

    def _create_review_required_result(
        self,
        state: DocumentationWorkflowState,
    ) -> DocumentationWorkflowResult:
        """Convert internal review state into the public workflow result."""

        return DocumentationWorkflowResult(
            workflow_id=state.workflow_id,
            status=self._determine_intermediate_status(state),
            started_at=state.started_at,
            completed_at=datetime.now(UTC),
            user_request=state.user_request,
            target_paths=state.target_paths,
            source_paths=state.source_paths,
            reasoning_result=state.reasoning_result,
            proposals=state.proposals,
            reviews=state.reviews,
            applied_changes=state.applied_changes,
            preliminary_validation=state.preliminary_validation,
            final_validation=None,
            git_diff="",
            summary=self._build_summary(
                proposals=state.proposals,
                reviews=state.reviews,
                applied_changes=state.applied_changes,
            ),
            warnings=state.warnings,
            error_message=state.error_message,
        )

    def _determine_intermediate_status(
        self,
        state: DocumentationWorkflowState,
    ) -> DocumentationWorkflowStatus:
        """Determine public result status while awaiting review."""

        if (
            state.preliminary_validation is not None
            and state.preliminary_validation.status
            is ValidationStatus.FAILED
        ):
            return DocumentationWorkflowStatus.FAILED

        if (
            state.preliminary_validation is not None
            and state.preliminary_validation.status
            is ValidationStatus.PASSED_WITH_WARNINGS
        ):
            return DocumentationWorkflowStatus.REVIEW_REQUIRED

        if state.warnings:
            return DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS

        return DocumentationWorkflowStatus.REVIEW_REQUIRED

    def get_workflow_state(
        self,
        workflow_id: str,
    ) -> DocumentationWorkflowState | None:
        """Return the current workflow state if it exists."""

        return self._workflow_states.get(workflow_id)

    def submit_review(
        self,
        workflow_id: str,
        review: DocumentationReview,
    ) -> DocumentationWorkflowState | DocumentationWorkflowResult:
        """Submit one user review and continue the workflow."""

        state = self._workflow_states.get(workflow_id)
        if state is None:
            raise ValueError(
                f"Documentation workflow state was not found: {workflow_id}"
            )

        reviewed_ids = {
            existing_review.proposal_id
            for existing_review in state.reviews
        }
        if review.proposal_id in reviewed_ids:
            raise ValueError(
                "Documentation proposal has already been reviewed: "
                f"{review.proposal_id}"
            )

        proposal = next(
            (
                candidate
                for candidate in state.proposals
                if candidate.proposal_id == review.proposal_id
            ),
            None,
        )
        if proposal is None:
            raise ValueError(
                "Documentation proposal was not found in workflow: "
                f"{review.proposal_id}"
            )

        reviews = (*state.reviews, review)

        if review.decision is ReviewDecision.REVISE:
            revised_state = DocumentationWorkflowState(
                workflow_id=state.workflow_id,
                status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                started_at=state.started_at,
                user_request=state.user_request,
                target_paths=state.target_paths,
                source_paths=state.source_paths,
                reasoning_result=state.reasoning_result,
                proposals=state.proposals,
                reviews=reviews,
                applied_changes=state.applied_changes,
                preliminary_validation=state.preliminary_validation,
                warnings=state.warnings,
                error_message=state.error_message,
            )
            self._workflow_states[workflow_id] = revised_state
            return revised_state

        applied_change = self._repository_update_service.apply(
            proposal,
            review,
        )
        applied_changes = (*state.applied_changes, applied_change)

        if len(reviews) < len(state.proposals):
            updated_state = DocumentationWorkflowState(
                workflow_id=state.workflow_id,
                status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                started_at=state.started_at,
                user_request=state.user_request,
                target_paths=state.target_paths,
                source_paths=state.source_paths,
                reasoning_result=state.reasoning_result,
                proposals=state.proposals,
                reviews=reviews,
                applied_changes=applied_changes,
                preliminary_validation=state.preliminary_validation,
                warnings=state.warnings,
                error_message=state.error_message,
            )
            self._workflow_states[workflow_id] = updated_state
            return updated_state

        result = self._complete_workflow(
            workflow_id=state.workflow_id,
            started_at=state.started_at,
            reasoning_result=state.reasoning_result,
            proposals=state.proposals,
            reviews=reviews,
            applied_changes=applied_changes,
            preliminary_validation=state.preliminary_validation,
            warnings=list(state.warnings),
        )
        self._workflow_states.pop(workflow_id, None)
        return result

    def _complete_workflow(
        self,
        workflow_id: str,
        started_at: datetime,
        reasoning_result: ReasoningResult | None,
        proposals: tuple[DocumentationChangeProposal, ...],
        reviews: tuple[DocumentationReview, ...],
        applied_changes: tuple[AppliedDocumentationChange, ...],
        preliminary_validation: ValidationResult | None,
        warnings: list[str],
    ) -> DocumentationWorkflowResult:
        """Complete validation, diff generation, and workflow reporting."""

        final_validation: ValidationResult | None = None
        git_diff: str | None = None

        applied_paths = tuple(
            change.repository_path
            for change in applied_changes
            if change.status is ChangeApplicationStatus.APPLIED
        )

        if applied_paths:
            final_validation = self._validate_paths(
                applied_paths,
                workflow_id,
            )

            if final_validation.status is ValidationStatus.FAILED:
                warnings.append(
                    "Final validation failed after approved "
                    "documentation changes were applied."
                )
            elif (
                final_validation.status
                is ValidationStatus.PASSED_WITH_WARNINGS
            ):
                warnings.append(
                    "Final validation completed with warnings."
                )

            git_diff = self._git_diff_service.generate_diff(
                applied_paths
            )
        else:
            git_diff = ""

        summary = self._build_summary(
            proposals=proposals,
            reviews=reviews,
            applied_changes=applied_changes,
        )
        status = self._determine_status(
            final_validation=final_validation,
            applied_changes=applied_changes,
            warnings=warnings,
        )

        return DocumentationWorkflowResult(
            workflow_id=workflow_id,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            user_request=self._workflow_states.get(
                workflow_id
            ).user_request if self._workflow_states.get(workflow_id) else "",
            target_paths=self._workflow_states.get(
                workflow_id
            ).target_paths if self._workflow_states.get(workflow_id) else (),
            source_paths=self._workflow_states.get(
                workflow_id
            ).source_paths if self._workflow_states.get(workflow_id) else (),
            reasoning_result=reasoning_result,
            proposals=proposals,
            reviews=reviews,
            applied_changes=applied_changes,
            preliminary_validation=preliminary_validation,
            final_validation=final_validation,
            git_diff=git_diff,
            summary=summary,
            warnings=tuple(warnings),
            error_message=(
                "One or more approved documentation changes failed."
                if status is DocumentationWorkflowStatus.FAILED
                else None
            ),
        )

    def _build_proposals(
        self,
        reasoning_result: ReasoningResult,
        target_paths: tuple[str, ...] = (),
        source_grounded: bool = False,
        context: str = "",
    ) -> tuple[
        tuple[DocumentationChangeProposal, ...],
        tuple[str, ...],
    ]:
        """Convert reasoning changes into reviewable workflow proposals."""

        proposals: list[DocumentationChangeProposal] = []
        warnings: list[str] = []
        allowed_target_paths = set(target_paths)

        for proposed_change in reasoning_result.proposed_changes:
            repository_path = proposed_change.document_path.as_posix()

            if (
                allowed_target_paths
                and repository_path not in allowed_target_paths
            ):
                warnings.append(
                    "Proposed documentation path was outside the "
                    "requested target scope and was skipped: "
                    f"{repository_path}."
                )
                continue

            if (
                proposed_change.operation
                is not DocumentationChangeOperation.UPDATE
            ):
                warnings.append(
                    "Unsupported documentation operation was skipped: "
                    f"{proposed_change.operation.value} "
                    f"for {repository_path}."
                )
                continue

            file_path = (
                self._repository_root / repository_path
            ).resolve()

            if not self._is_within_repository(file_path):
                warnings.append(
                    "Proposed documentation path was outside the "
                    f"repository and was skipped: {repository_path}."
                )
                continue

            if file_path.suffix.lower() != ".md":
                warnings.append(
                    "Proposed non-Markdown change was skipped: "
                    f"{repository_path}."
                )
                continue

            if not file_path.is_file():
                warnings.append(
                    "Proposed documentation file was not found and "
                    f"was skipped: {repository_path}."
                )
                continue

            original_content = file_path.read_text(encoding="utf-8")
            proposed_content = proposed_change.proposed_content

            if (
                source_grounded
                and self._is_meta_instruction_content(
                    proposed_content
                )
            ):
                logger.debug(
                    "Rejected source-grounded meta-instruction content "
                    "for %s: %r",
                    repository_path,
                    proposed_content,
                )
                warnings.append(
                    "Proposed documentation content described what "
                    "should be written instead of providing concrete "
                    f"Markdown and was skipped: {repository_path}."
                )
                continue

            if (
                source_grounded
                and self._introduces_python_fence_without_target_form(
                    original_content=original_content,
                    proposed_content=proposed_content,
                    section=proposed_change.section,
                )
            ):
                documentation_meaning = (
                    proposed_change.documentation_meaning
                )

                logger.debug(
                    "Evaluating source-grounded documentation meaning "
                    "fallback for %s: %r",
                    repository_path,
                    documentation_meaning,
                )

                if (
                    documentation_meaning
                    and not self._is_meta_instruction_content(
                        documentation_meaning
                    )
                    and not self._is_rationale_like_documentation_meaning(
                        documentation_meaning
                    )
                    and not self._contains_fenced_python(
                        documentation_meaning
                    )
                ):
                    proposed_content = documentation_meaning
                else:
                    warnings.append(
                        "Proposed documentation introduced a fenced Python "
                        "block where the affected target section does not "
                        "already use fenced Python content; the change was "
                        f"skipped: {repository_path}."
                    )
                    continue

            if source_grounded:
                proposed_content = self._canonicalize_python_declarations(
                    proposed_content=proposed_content,
                    context=context,
                )

            if (
                source_grounded
                and not self._python_declarations_are_source_grounded(
                    proposed_content=proposed_content,
                    context=context,
                )
            ):
                proposed_declarations = self._extract_python_declarations(
                    proposed_content
                )
                authoritative_declarations: set[str] = set()
                for source_content in (
                    self._extract_authoritative_python_sources(context)
                ):
                    authoritative_declarations.update(
                        self._extract_python_source_declarations(
                            source_content
                        )
                    )

                logger.debug(
                    "Rejected source-grounded Python declaration for %s; "
                    "proposed_declarations=%r authoritative_declarations=%r",
                    repository_path,
                    proposed_declarations,
                    tuple(sorted(authoritative_declarations)),
                )
                warnings.append(
                    "Proposed Python declaration did not exactly match "
                    "an authoritative source declaration and was skipped: "
                    f"{repository_path}."
                )
                continue

            artifact_locations = ()
            if proposed_change.section:
                artifact_locations = (
                    self._artifact_location_service.discover_locations(
                        file_path,
                        proposed_change.section,
                    )
                )

            if not artifact_locations:
                artifact_locations = (
                    self._artifact_location_service.discover_locations(
                        file_path,
                        proposed_change.rationale,
                    )
                )

            artifact_location = (
                artifact_locations[0]
                if artifact_locations
                else None
            )

            if (
                source_grounded
                and proposed_change.section
                and artifact_location is not None
                and not self._is_semantically_aligned_section(
                    section_heading=artifact_location.locator,
                    rationale=proposed_change.rationale,
                    proposed_content=proposed_content,
                )
            ):
                recovered_heading = self._select_recovery_section(
                    original_content=original_content,
                    rationale=proposed_change.rationale,
                    proposed_content=proposed_content,
                )

                if recovered_heading is None:
                    warnings.append(
                        "Proposed documentation section was not "
                        "semantically aligned with the proposed change "
                        "and no unambiguous replacement section was "
                        f"found; the change was skipped: {repository_path} "
                        f"(section: {artifact_location.locator})."
                    )
                    continue

                recovered_locations = (
                    self._artifact_location_service.discover_locations(
                        file_path,
                        recovered_heading,
                    )
                )

                if len(recovered_locations) != 1:
                    warnings.append(
                        "A semantically aligned replacement section "
                        "could not be resolved unambiguously; the proposed "
                        f"change was skipped: {repository_path} "
                        f"(section: {recovered_heading})."
                    )
                    continue

                artifact_locations = recovered_locations
                artifact_location = recovered_locations[0]

            if len(artifact_locations) > 1:
                warnings.append(
                    "Multiple artifact locations were discovered; "
                    "the proposed documentation change was skipped: "
                    f"{repository_path}."
                )
                continue

            if artifact_location is None and source_grounded:
                anchor_text = proposed_change.anchor_text

                if anchor_text is None:
                    warnings.append(
                        "No unambiguous documentation location or exact "
                        "anchor text was provided; the proposed change was "
                        f"skipped: {repository_path}."
                    )
                    continue

                anchor_count = original_content.count(anchor_text)

                if anchor_count == 0:
                    warnings.append(
                        "Proposed documentation anchor text was not found; "
                        f"the change was skipped: {repository_path}."
                    )
                    continue

                if anchor_count > 1:
                    warnings.append(
                        "Proposed documentation anchor text was ambiguous; "
                        f"the change was skipped: {repository_path}."
                    )
                    continue

            proposal_artifact_location = artifact_location
            proposal_anchor_mode = (
                DocumentationAnchorMode.INSERT_AFTER
                if proposed_change.edit_type
                is DocumentationEditType.INSERT
                else DocumentationAnchorMode.REPLACE
            )

            if (
                source_grounded
                and artifact_location is not None
                and artifact_location.location_type
                is ArtifactLocationType.SECTION
                and proposed_change.edit_type
                is DocumentationEditType.REPLACE
                and not self._proposed_content_replaces_full_section(
                    original_content=original_content,
                    proposed_content=proposed_content,
                    artifact_location=artifact_location,
                )
            ):
                proposal_artifact_location = self._section_heading_location(
                    artifact_location
                )
                proposal_anchor_mode = DocumentationAnchorMode.INSERT_AFTER

            proposal = DocumentationChangeProposal(
                repository_path=repository_path,
                original_content=original_content,
                proposed_content=proposed_content,
                rationale=proposed_change.rationale,
                artifact_location=proposal_artifact_location,
                anchor_text=proposed_change.anchor_text,
                anchor_mode=proposal_anchor_mode,
            )

            proposals.append(proposal)

        return tuple(proposals), tuple(warnings)

    @staticmethod
    def _is_meta_instruction_content(
        proposed_content: str,
    ) -> bool:
        """Return whether proposed content is an instruction, not content.

        Source-grounded proposals must contain actual documentation text.
        Obvious imperative planning language is rejected deterministically
        instead of being surfaced as reviewable Markdown.
        """

        stripped = proposed_content.strip()

        if not stripped:
            return False

        nonempty_lines = tuple(
            line.strip()
            for line in stripped.splitlines()
            if line.strip()
        )

        if not nonempty_lines:
            return False

        # Concrete Markdown structures should not be rejected merely
        # because later prose begins with a verb.
        first_line = nonempty_lines[0]
        if (
            first_line.startswith(("#", "-", "*", ">", "```"))
            or re.match(r"^\d+[.)]\s+", first_line)
        ):
            return False

        return any(
            pattern.search(stripped)
            for pattern in _PROPOSED_CONTENT_META_INSTRUCTION_PATTERNS
        )

    @staticmethod
    def _is_rationale_like_documentation_meaning(
        documentation_meaning: str,
    ) -> bool:
        """Return whether semantic fallback prose describes the change itself.

        Documentation meaning used as fallback content must state the
        implemented contract directly rather than explain what a proposed
        documentation change will accomplish.
        """

        stripped = documentation_meaning.strip()

        if not stripped:
            return False

        return any(
            pattern.search(stripped)
            for pattern in _DOCUMENTATION_MEANING_RATIONALE_PATTERNS
        )

    @classmethod
    def _introduces_python_fence_without_target_form(
        cls,
        original_content: str,
        proposed_content: str,
        section: str | None,
    ) -> bool:
        """Return whether a proposal introduces Python outside target form.

        Source-grounded synchronization may update fenced Python only when
        the affected existing target section already contains fenced Python.
        A proposal without a resolvable section fails closed when it
        introduces fenced Python.
        """

        if not cls._contains_fenced_python(proposed_content):
            return False

        if section is None:
            return True

        section_content = cls._extract_markdown_section_content(
            original_content,
            section,
        )

        if section_content is None:
            return True

        return not cls._contains_fenced_python(section_content)

    @staticmethod
    def _contains_fenced_python(content: str) -> bool:
        """Return whether Markdown contains a fenced Python code block."""

        return bool(
            re.search(
                r"```(?:python|py)\s*\n",
                content,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _extract_markdown_section_content(
        content: str,
        section: str,
    ) -> str | None:
        """Return one exact Markdown section including its heading."""

        lines = content.splitlines(keepends=True)
        heading_index: int | None = None
        heading_level: int | None = None

        for index, line in enumerate(lines):
            stripped = line.strip()

            if not stripped.startswith("#"):
                continue

            marker_length = len(stripped) - len(
                stripped.lstrip("#")
            )

            if not 1 <= marker_length <= 6:
                continue

            remainder = stripped[marker_length:]

            if not remainder.startswith(" "):
                continue

            if remainder.strip() != section:
                continue

            if heading_index is not None:
                return None

            heading_index = index
            heading_level = marker_length

        if heading_index is None or heading_level is None:
            return None

        end_index = len(lines)

        for index in range(heading_index + 1, len(lines)):
            stripped = lines[index].strip()

            if not stripped.startswith("#"):
                continue

            marker_length = len(stripped) - len(
                stripped.lstrip("#")
            )

            if not 1 <= marker_length <= 6:
                continue

            remainder = stripped[marker_length:]

            if (
                remainder.startswith(" ")
                and marker_length <= heading_level
            ):
                end_index = index
                break

        return "".join(lines[heading_index:end_index])

    @classmethod
    def _canonicalize_python_declarations(
        cls,
        proposed_content: str,
        context: str,
    ) -> str:
        """Replace uniquely matched Python declarations with source text.

        Only fenced Python declarations with one exact authoritative
        signature match are canonicalized. Unmatched or ambiguous
        declarations remain unchanged for the existing fail-closed
        source-fidelity guard.
        """

        authoritative_sources = (
            cls._extract_authoritative_python_sources(context)
        )

        if not authoritative_sources:
            return proposed_content

        declarations_by_signature: dict[str, list[str]] = {}

        for source_content in authoritative_sources:
            for signature, declaration in (
                cls._extract_python_source_declaration_records(
                    source_content
                )
            ):
                declarations_by_signature.setdefault(
                    signature,
                    [],
                ).append(declaration)

        if not declarations_by_signature:
            return proposed_content

        fence_pattern = re.compile(
            r"```(?:python|py)\s*\n(.*?)```",
            re.IGNORECASE | re.DOTALL,
        )

        def canonicalize_fence(match: re.Match[str]) -> str:
            code = match.group(1)

            try:
                module = ast.parse(code)
            except SyntaxError:
                return match.group(0)

            lines = code.splitlines(keepends=True)
            replacements: list[tuple[int, int, str]] = []

            for node in module.body:
                if not isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    continue

                signature = cls._python_declaration_signature(node)
                matches = declarations_by_signature.get(
                    signature,
                    [],
                )

                if len(matches) != 1:
                    continue

                if node.end_lineno is None:
                    continue

                start_index = node.lineno - 1
                end_index = node.end_lineno
                original_segment = "".join(
                    lines[start_index:end_index]
                )
                replacement = matches[0]

                if original_segment.endswith("\n"):
                    replacement += "\n"

                replacements.append(
                    (
                        start_index,
                        end_index,
                        replacement,
                    )
                )

            if not replacements:
                return match.group(0)

            for start_index, end_index, replacement in reversed(
                replacements
            ):
                lines[start_index:end_index] = [replacement]

            canonical_code = "".join(lines)
            prefix = match.group(0)[:match.start(1) - match.start(0)]
            suffix = match.group(0)[match.end(1) - match.start(0):]

            return f"{prefix}{canonical_code}{suffix}"

        return fence_pattern.sub(
            canonicalize_fence,
            proposed_content,
        )

    @classmethod
    def _extract_python_source_declaration_records(
        cls,
        source_content: str,
    ) -> tuple[tuple[str, str], ...]:
        """Extract authoritative declaration signatures and source text."""

        try:
            module = ast.parse(source_content)
        except SyntaxError:
            return ()

        records: list[tuple[str, str]] = []

        for node in ast.walk(module):
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                ),
            ):
                records.append(
                    (
                        cls._python_declaration_signature(node),
                        cls._normalized_ast_node_source(
                            source_content,
                            node,
                        ),
                    )
                )

        return tuple(records)

    @staticmethod
    def _python_declaration_signature(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> str:
        """Return a stable body-independent Python declaration signature."""

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return repr(
                (
                    type(node).__name__,
                    node.name,
                    ast.dump(
                        node.args,
                        include_attributes=False,
                    ),
                    ast.dump(
                        node.returns,
                        include_attributes=False,
                    )
                    if node.returns is not None
                    else None,
                    tuple(
                        ast.dump(
                            decorator,
                            include_attributes=False,
                        )
                        for decorator in node.decorator_list
                    ),
                    node.type_comment,
                    tuple(
                        ast.dump(
                            type_parameter,
                            include_attributes=False,
                        )
                        for type_parameter in getattr(
                            node,
                            "type_params",
                            (),
                        )
                    ),
                )
            )

        return repr(
            (
                type(node).__name__,
                node.name,
                tuple(
                    ast.dump(
                        base,
                        include_attributes=False,
                    )
                    for base in node.bases
                ),
                tuple(
                    ast.dump(
                        keyword,
                        include_attributes=False,
                    )
                    for keyword in node.keywords
                ),
                tuple(
                    ast.dump(
                        decorator,
                        include_attributes=False,
                    )
                    for decorator in node.decorator_list
                ),
                tuple(
                    ast.dump(
                        type_parameter,
                        include_attributes=False,
                    )
                    for type_parameter in getattr(
                        node,
                        "type_params",
                        (),
                    )
                ),
            )
        )

    @classmethod
    def _python_declarations_are_source_grounded(
        cls,
        proposed_content: str,
        context: str,
    ) -> bool:
        """Verify fenced Python declarations against authoritative sources.

        Source-grounded documentation may reproduce Python declarations
        only when each proposed function, async function, or class
        declaration exactly matches one declaration present in an
        authoritative Python source file. Non-declaration Python examples
        and proposals without authoritative Python source content preserve
        existing behavior.
        """

        proposed_declarations = cls._extract_python_declarations(
            proposed_content
        )

        if not proposed_declarations:
            return True

        authoritative_sources = (
            cls._extract_authoritative_python_sources(context)
        )

        if not authoritative_sources:
            return True

        authoritative_declarations: set[str] = set()

        for source_content in authoritative_sources:
            authoritative_declarations.update(
                cls._extract_python_source_declarations(
                    source_content
                )
            )

        return all(
            declaration in authoritative_declarations
            for declaration in proposed_declarations
        )

    @classmethod
    def _extract_python_declarations(
        cls,
        markdown_content: str,
    ) -> tuple[str, ...]:
        """Extract function and class declarations from fenced Python."""

        declarations: list[str] = []

        for match in re.finditer(
            r"```(?:python|py)\s*\n(.*?)```",
            markdown_content,
            re.IGNORECASE | re.DOTALL,
        ):
            code = match.group(1)

            try:
                module = ast.parse(code)
            except SyntaxError:
                continue

            for node in module.body:
                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    declarations.append(
                        cls._normalized_ast_node_source(
                            code,
                            node,
                        )
                    )

        return tuple(declarations)

    @classmethod
    def _extract_python_source_declarations(
        cls,
        source_content: str,
    ) -> tuple[str, ...]:
        """Extract declarations recursively from authoritative Python."""

        try:
            module = ast.parse(source_content)
        except SyntaxError:
            return ()

        declarations: list[str] = []

        for node in ast.walk(module):
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                ),
            ):
                declarations.append(
                    cls._normalized_ast_node_source(
                        source_content,
                        node,
                    )
                )

        return tuple(declarations)

    @staticmethod
    def _normalized_ast_node_source(
        source_content: str,
        node: ast.AST,
    ) -> str:
        """Return a declaration using stable dedented source text."""

        lineno = getattr(node, "lineno", None)
        end_lineno = getattr(node, "end_lineno", None)

        if lineno is None or end_lineno is None:
            return ""

        lines = source_content.splitlines()
        declaration = "\n".join(
            lines[lineno - 1:end_lineno]
        )

        return textwrap.dedent(declaration).strip()

    @staticmethod
    def _extract_authoritative_python_sources(
        context: str,
    ) -> tuple[str, ...]:
        """Extract Python source bodies from authoritative context sections."""

        target_marker = "=== TARGET DOCUMENTATION ==="
        source_marker = "=== AUTHORITATIVE SOURCE ==="

        sources: list[str] = []
        current_role: str | None = None
        current_path: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            if (
                current_role == source_marker
                and current_path is not None
                and current_path.endswith(".py")
            ):
                sources.append("\n".join(current_lines))

        for line in context.splitlines():
            stripped = line.strip()

            if stripped in {target_marker, source_marker}:
                flush()
                current_role = stripped
                current_path = None
                current_lines = []
                continue

            if (
                stripped.startswith("=== ")
                and stripped.endswith(" ===")
            ):
                flush()
                current_role = stripped
                current_path = None
                current_lines = []
                continue

            if current_path is None and line.startswith("Path: "):
                current_path = line[6:].strip()
                continue

            if current_role == source_marker:
                current_lines.append(line)

        flush()

        return tuple(sources)

    @staticmethod
    def _proposed_content_replaces_full_section(
        original_content: str,
        proposed_content: str,
        artifact_location: ArtifactLocation,
    ) -> bool:
        """Return whether proposed content explicitly includes the heading.

        Source-grounded section updates may safely replace an entire
        section only when the proposed content begins with the exact
        existing Markdown heading. Otherwise the proposal is treated as
        localized content to insert beneath that heading.
        """

        if artifact_location.start_line is None:
            return False

        lines = original_content.splitlines()
        heading_index = artifact_location.start_line - 1

        if heading_index < 0 or heading_index >= len(lines):
            return False

        existing_heading = lines[heading_index].strip()
        first_proposed_line = next(
            (
                line.strip()
                for line in proposed_content.splitlines()
                if line.strip()
            ),
            "",
        )

        return (
            bool(existing_heading)
            and first_proposed_line == existing_heading
        )

    @staticmethod
    def _section_heading_location(
        artifact_location: ArtifactLocation,
    ) -> ArtifactLocation:
        """Narrow a section location to its heading line."""

        if artifact_location.start_line is None:
            raise ValueError(
                "Section artifact location does not define a start line."
            )

        return ArtifactLocation(
            location_id=f"{artifact_location.location_id}-heading",
            repository_path=artifact_location.repository_path,
            location_type=ArtifactLocationType.LINE_RANGE,
            locator=artifact_location.locator,
            start_line=artifact_location.start_line,
            end_line=artifact_location.start_line,
            content_hash=artifact_location.content_hash,
        )

    @staticmethod
    def _semantic_tokens(text: str) -> frozenset[str]:
        """Return normalized semantic tokens for section validation."""

        expanded = re.sub(
            r"([a-z0-9])([A-Z])",
            r"\1 \2",
            text.replace("_", " ").replace("-", " "),
        )

        return frozenset(
            token
            for token in (
                value.casefold()
                for value in re.findall(
                    r"[A-Za-z0-9]+",
                    expanded,
                )
            )
            if (
                len(token) > 1
                and token not in _SECTION_SEMANTIC_STOP_WORDS
            )
        )

    @classmethod
    def _is_semantically_aligned_section(
        cls,
        section_heading: str,
        rationale: str,
        proposed_content: str,
    ) -> bool:
        """Return whether a selected heading matches the proposed change.

        Source-grounded proposals must share at least one meaningful,
        normalized term with the selected section heading. This provides
        a deterministic fail-closed guard against structurally valid but
        semantically unrelated model-selected sections.
        """

        heading_tokens = cls._semantic_tokens(section_heading)

        if not heading_tokens:
            return False

        change_tokens = cls._semantic_tokens(
            f"{rationale}\n{proposed_content}"
        )

        return bool(
            heading_tokens.intersection(change_tokens)
        )

    @classmethod
    def _select_recovery_section(
        cls,
        original_content: str,
        rationale: str,
        proposed_content: str,
    ) -> str | None:
        """Return one clear semantically aligned Markdown subsection.

        Candidate headings are taken directly from the target document.
        Level-one document titles are excluded. A recovery section is
        selected only when one candidate has a strictly greater positive
        overlap score than every other candidate.
        """

        candidates = cls._extract_recovery_section_headings(
            original_content
        )

        if not candidates:
            return None

        change_tokens = cls._semantic_tokens(
            f"{rationale}\n{proposed_content}"
        )

        scored_candidates = tuple(
            (
                heading,
                len(
                    cls._semantic_tokens(heading).intersection(
                        change_tokens
                    )
                ),
            )
            for heading in candidates
        )

        highest_score = max(
            score
            for _, score in scored_candidates
        )

        if highest_score <= 0:
            return None

        best_candidates = tuple(
            heading
            for heading, score in scored_candidates
            if score == highest_score
        )

        if len(best_candidates) != 1:
            return None

        return best_candidates[0]

    @staticmethod
    def _extract_recovery_section_headings(
        content: str,
    ) -> tuple[str, ...]:
        """Extract unique Markdown subsection headings from a document."""

        headings: list[str] = []

        for line in content.splitlines():
            stripped = line.strip()

            if not stripped.startswith("#"):
                continue

            marker_length = len(stripped) - len(
                stripped.lstrip("#")
            )

            if not 2 <= marker_length <= 6:
                continue

            remainder = stripped[marker_length:]

            if not remainder.startswith(" "):
                continue

            heading = remainder.strip()

            if heading and heading not in headings:
                headings.append(heading)

        return tuple(headings)

    @staticmethod
    def _select_reasoning_warnings(
        reasoning_result: ReasoningResult,
        source_grounded: bool,
    ) -> tuple[str, ...]:
        """Select warnings safe to surface for the workflow.

        Source-grounded documentation runs fail closed for free-form
        model warnings because the current reasoning response does not
        carry structured evidence for verifying them. Provider warnings
        remain available because they describe provider execution rather
        than repository conditions.
        """

        if not source_grounded:
            return reasoning_result.warnings

        provider_warnings = reasoning_result.metadata.get(
            "provider_warnings",
            (),
        )

        if not isinstance(provider_warnings, (tuple, list)):
            return ()

        return tuple(
            warning
            for warning in provider_warnings
            if isinstance(warning, str)
        )

    def _validate_paths(
        self,
        repository_paths: tuple[str, ...],
        workflow_id: str,
    ) -> ValidationResult:
        """Validate selected repository documentation paths."""

        return self._validation_service.validate(
            ValidationRequest(
                target_paths=repository_paths,
                validation_id=f"{workflow_id}-validation",
            )
        )

    @staticmethod
    def _build_summary(
        proposals: tuple[DocumentationChangeProposal, ...],
        reviews: tuple[DocumentationReview, ...],
        applied_changes: tuple[AppliedDocumentationChange, ...],
    ) -> DocumentationWorkflowSummary:
        """Build summary counts for a documentation workflow."""

        return DocumentationWorkflowSummary(
            proposed_count=len(proposals),
            approved_count=sum(
                review.decision is ReviewDecision.APPROVE
                for review in reviews
            ),
            revised_count=sum(
                review.decision is ReviewDecision.REVISE
                for review in reviews
            ),
            rejected_count=sum(
                review.decision is ReviewDecision.REJECT
                for review in reviews
            ),
            skipped_count=sum(
                review.decision is ReviewDecision.SKIP
                for review in reviews
            ),
            applied_count=sum(
                change.status is ChangeApplicationStatus.APPLIED
                for change in applied_changes
            ),
            failed_count=sum(
                change.status is ChangeApplicationStatus.FAILED
                for change in applied_changes
            ),
        )

    @staticmethod
    def _determine_status(
        final_validation: ValidationResult | None,
        applied_changes: tuple[AppliedDocumentationChange, ...],
        warnings: list[str],
    ) -> DocumentationWorkflowStatus:
        """Determine the completed documentation workflow status."""

        if any(
            change.status is ChangeApplicationStatus.FAILED
            for change in applied_changes
        ):
            return DocumentationWorkflowStatus.FAILED

        if (
            final_validation is not None
            and final_validation.status is ValidationStatus.FAILED
        ):
            return DocumentationWorkflowStatus.FAILED

        if warnings:
            return DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS

        return DocumentationWorkflowStatus.COMPLETED

    def _is_within_repository(self, file_path: Path) -> bool:
        """Return whether a path is contained by the repository root."""

        try:
            file_path.relative_to(self._repository_root)
        except ValueError:
            return False

        return True

    @staticmethod
    def _empty_summary() -> DocumentationWorkflowSummary:
        """Return an empty workflow summary."""

        return DocumentationWorkflowSummary(
            proposed_count=0,
            approved_count=0,
            revised_count=0,
            rejected_count=0,
            skipped_count=0,
            applied_count=0,
            failed_count=0,
        )

    def _failed_result(
        self,
        request: DocumentationWorkflowRequest,
        started_at: datetime,
        error_message: str,
        reasoning_result: ReasoningResult | None = None,
        proposals: tuple[DocumentationChangeProposal, ...] = (),
        reviews: tuple[DocumentationReview, ...] = (),
        applied_changes: tuple[AppliedDocumentationChange, ...] = (),
        preliminary_validation: ValidationResult | None = None,
        final_validation: ValidationResult | None = None,
        git_diff: str | None = None,
        warnings: tuple[str, ...] = (),
    ) -> DocumentationWorkflowResult:
        """Return a failed documentation workflow result."""

        summary = (
            self._build_summary(
                proposals=proposals,
                reviews=reviews,
                applied_changes=applied_changes,
            )
            if proposals or reviews or applied_changes
            else self._empty_summary()
        )

        return DocumentationWorkflowResult(
            workflow_id=request.workflow_id,
            status=DocumentationWorkflowStatus.FAILED,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            user_request=request.user_request,
            target_paths=request.target_paths,
            source_paths=request.source_paths,
            reasoning_result=reasoning_result,
            proposals=proposals,
            reviews=reviews,
            applied_changes=applied_changes,
            preliminary_validation=preliminary_validation,
            final_validation=final_validation,
            git_diff=git_diff,
            summary=summary,
            warnings=warnings,
            error_message=error_message,
        )
