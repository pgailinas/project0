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
from pathlib import Path

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
    DocumentationChangeProposal,
    DocumentationReview,
    DocumentationWorkflowRequest,
    DocumentationWorkflowResult,
    DocumentationWorkflowStatus,
    DocumentationWorkflowSummary,
    ReviewDecision,
)
from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)
from project0.models.validation_models import (
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
)


ContextProvider = Callable[[DocumentationWorkflowRequest], str]


class DocumentationWorkflow:
    """Coordinate the complete documentation update workflow."""

    def __init__(
        self,
        repository_root: Path,
        context_provider: ContextProvider,
        reasoning_service: ReasoningServiceProtocol,
        validation_service: ValidationInterface,
        review_coordinator: ReviewCoordinatorInterface,
        repository_update_service: RepositoryUpdateInterface,
        git_diff_service: GitDiffInterface,
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._context_provider = context_provider
        self._reasoning_service = reasoning_service
        self._validation_service = validation_service
        self._review_coordinator = review_coordinator
        self._repository_update_service = repository_update_service
        self._git_diff_service = git_diff_service

    def execute(
        self,
        request: DocumentationWorkflowRequest,
    ) -> DocumentationWorkflowResult:
        """Execute a documentation workflow and return its result."""

        started_at = datetime.now(UTC)
        reasoning_result: ReasoningResult | None = None
        proposals: tuple[DocumentationChangeProposal, ...] = ()
        reviews: tuple[DocumentationReview, ...] = ()
        applied_changes: tuple[AppliedDocumentationChange, ...] = ()
        preliminary_validation: ValidationResult | None = None
        final_validation: ValidationResult | None = None
        git_diff: str | None = None
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
                reasoning_result
            )
            warnings.extend(proposal_warnings)

            preliminary_validation = self._validate_paths(
                tuple(
                    proposal.repository_path
                    for proposal in proposals
                ),
                request.workflow_id,
            )

            if (
                preliminary_validation.status
                is ValidationStatus.FAILED
            ):
                return self._failed_result(
                    request=request,
                    started_at=started_at,
                    reasoning_result=reasoning_result,
                    proposals=proposals,
                    preliminary_validation=preliminary_validation,
                    error_message=(
                        "Preliminary documentation validation failed."
                    ),
                    warnings=tuple(warnings),
                )

            if (
                preliminary_validation.status
                is ValidationStatus.PASSED_WITH_WARNINGS
            ):
                warnings.append(
                    "Preliminary validation completed with warnings."
                )

            review_list: list[DocumentationReview] = []
            applied_list: list[AppliedDocumentationChange] = []

            for proposal in proposals:
                review = self._review_coordinator.review(proposal)
                review_list.append(review)

                applied_change = (
                    self._repository_update_service.apply(
                        proposal,
                        review,
                    )
                )
                applied_list.append(applied_change)

            reviews = tuple(review_list)
            applied_changes = tuple(applied_list)

            applied_paths = tuple(
                change.repository_path
                for change in applied_changes
                if (
                    change.status
                    is ChangeApplicationStatus.APPLIED
                )
            )

            if applied_paths:
                final_validation = self._validate_paths(
                    applied_paths,
                    request.workflow_id,
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
                final_validation = None
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
                workflow_id=request.workflow_id,
                status=status,
                started_at=started_at,
                completed_at=datetime.now(UTC),
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

        except (OSError, RuntimeError, TypeError, ValueError) as error:
            return self._failed_result(
                request=request,
                started_at=started_at,
                reasoning_result=reasoning_result,
                proposals=proposals,
                reviews=reviews,
                applied_changes=applied_changes,
                preliminary_validation=preliminary_validation,
                final_validation=final_validation,
                git_diff=git_diff,
                error_message=str(error),
                warnings=tuple(warnings),
            )

    def _build_proposals(
        self,
        reasoning_result: ReasoningResult,
    ) -> tuple[
        tuple[DocumentationChangeProposal, ...],
        tuple[str, ...],
    ]:
        """Convert reasoning changes into reviewable workflow proposals."""

        proposals: list[DocumentationChangeProposal] = []
        warnings: list[str] = []

        for proposed_change in reasoning_result.proposed_changes:
            repository_path = proposed_change.document_path.as_posix()

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

            proposals.append(
                DocumentationChangeProposal(
                    repository_path=repository_path,
                    original_content=original_content,
                    proposed_content=(
                        proposed_change.proposed_content
                    ),
                    rationale=proposed_change.rationale,
                )
            )

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
