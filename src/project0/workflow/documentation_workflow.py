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
from datetime import UTC, datetime
import logging
from pathlib import Path

from project0.interfaces.artifact_interfaces import (
    ArtifactLocationServiceInterface,
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
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)
from project0.models.validation_models import (
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
)


logger = logging.getLogger(__name__)


ContextProvider = Callable[[DocumentationWorkflowRequest], str]


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
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._context_provider = context_provider
        self._reasoning_service = reasoning_service
        self._artifact_location_service = artifact_location_service
        self._validation_service = validation_service
        self._review_coordinator = review_coordinator
        self._repository_update_service = repository_update_service
        self._git_diff_service = git_diff_service
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

            reasoning_result = self._reasoning_service.reason(
                ReasoningRequest(
                    objective=request.user_request,
                    context=context,
                    workflow_type="documentation_update",
                    target_paths=tuple(
                        Path(repository_path)
                        for repository_path in request.target_paths
                    ),
                    constraints=(
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
                    ),
                    metadata={
                        "workflow_id": request.workflow_id,
                    },
                )
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

            warnings.extend(reasoning_result.warnings)

            proposals, proposal_warnings = self._build_proposals(
                reasoning_result=reasoning_result,
                target_paths=request.target_paths,
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

            location_request = (
                proposed_change.section
                or proposed_change.rationale
            )

            artifact_locations = (
                self._artifact_location_service.discover_locations(
                    file_path,
                    location_request,
                )
            )

            artifact_location = (
                artifact_locations[0]
                if artifact_locations
                else None
            )

            if len(artifact_locations) > 1:
                warnings.append(
                    "Multiple artifact locations were discovered; "
                    "the first location was selected."
                )

            proposal = DocumentationChangeProposal(
                repository_path=repository_path,
                original_content=original_content,
                proposed_content=(
                    proposed_change.proposed_content
                ),
                rationale=proposed_change.rationale,
                artifact_location=artifact_location,
                anchor_text=proposed_change.anchor_text,
                anchor_mode=(
                    DocumentationAnchorMode.INSERT_AFTER
                    if proposed_change.edit_type
                    is DocumentationEditType.INSERT
                    else DocumentationAnchorMode.REPLACE
                ),
            )

            proposals.append(proposal)

        return tuple(proposals), tuple(warnings)

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
