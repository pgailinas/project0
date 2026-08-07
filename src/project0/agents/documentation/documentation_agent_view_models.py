# ============================================================
# Project0 - Documentation Agent View Models
#
# File: documentation_agent_view_models.py
#
# Purpose:
#     Define immutable presentation models used by the
#     Documentation Agent browser interface.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from project0.models.documentation_workflow_models import ReviewDecision


class DocumentationAgentPageStatus(StrEnum):
    """Supported Documentation Agent page states."""

    READY = "ready"
    PROCESSING = "processing"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class ValidationDisplayStatus(StrEnum):
    """Supported validation presentation states."""

    NOT_RUN = "not_run"
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class DifferenceLineType(StrEnum):
    """Supported documentation difference line types."""

    CONTEXT = "context"
    ADDED = "added"
    REMOVED = "removed"
    HEADER = "header"


@dataclass(frozen=True, slots=True)
class DocumentationRequestForm:
    """User-entered documentation request values."""

    user_request: str = ""
    target_paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationMessageView:
    """One validation message prepared for browser display."""

    validator_name: str
    message: str
    severity: str
    repository_path: str | None = None
    line_number: int | None = None


@dataclass(frozen=True, slots=True)
class ValidationResultView:
    """Validation result summary prepared for browser display."""

    status: ValidationDisplayStatus
    title: str
    summary: str
    error_count: int = 0
    warning_count: int = 0
    messages: tuple[ValidationMessageView, ...] = ()

    @property
    def passed(self) -> bool:
        """Return True when validation did not fail."""

        return self.status in {
            ValidationDisplayStatus.PASSED,
            ValidationDisplayStatus.PASSED_WITH_WARNINGS,
        }

    @property
    def has_messages(self) -> bool:
        """Return True when validation produced display messages."""

        return bool(self.messages)


@dataclass(frozen=True, slots=True)
class DifferenceLineView:
    """One formatted line of a documentation difference."""

    line_type: DifferenceLineType
    content: str
    old_line_number: int | None = None
    new_line_number: int | None = None


@dataclass(frozen=True, slots=True)
class DocumentationDifferenceView:
    """Documentation differences prepared for browser display."""

    repository_path: str
    lines: tuple[DifferenceLineView, ...] = ()

    @property
    def has_differences(self) -> bool:
        """Return True when difference lines are available."""

        return bool(self.lines)


@dataclass(frozen=True, slots=True)
class DocumentationProposalView:
    """One documentation change proposal prepared for review."""

    proposal_id: str
    repository_path: str
    rationale: str
    original_content: str
    proposed_content: str
    selected_decision: ReviewDecision | None = None
    feedback: str | None = None
    difference: DocumentationDifferenceView | None = None

    @property
    def has_decision(self) -> bool:
        """Return True when the user has selected a review decision."""

        return self.selected_decision is not None


@dataclass(frozen=True, slots=True)
class DocumentationWorkflowSummaryView:
    """Documentation workflow counts prepared for browser display."""

    proposed_count: int = 0
    approved_count: int = 0
    revised_count: int = 0
    rejected_count: int = 0
    skipped_count: int = 0
    applied_count: int = 0
    failed_count: int = 0


@dataclass(frozen=True, slots=True)
class DocumentationAgentPageView:
    """Complete Documentation Agent Work Area presentation state."""

    page_status: DocumentationAgentPageStatus
    status_message: str
    request_form: DocumentationRequestForm
    workflow_id: str | None = None
    proposals: tuple[DocumentationProposalView, ...] = ()
    preliminary_validation: ValidationResultView | None = None
    final_validation: ValidationResultView | None = None
    workflow_summary: DocumentationWorkflowSummaryView | None = None
    warnings: tuple[str, ...] = ()
    error_message: str | None = None

    @property
    def requires_review(self) -> bool:
        """Return True when one or more proposals await review."""

        return (
            self.page_status
            == DocumentationAgentPageStatus.REVIEW_REQUIRED
            and bool(self.proposals)
        )

    @property
    def has_warnings(self) -> bool:
        """Return True when the page contains workflow warnings."""

        return bool(self.warnings)

    @property
    def has_error(self) -> bool:
        """Return True when the page contains an error message."""

        return self.error_message is not None
