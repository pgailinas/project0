# ============================================================
# Project0 - Documentation Workflow Models
#
# File: documentation_workflow_models.py
#
# Purpose:
#     Define shared documentation workflow models used to
#     propose, review, apply, and summarize documentation changes.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from project0.models.reasoning_models import ReasoningResult
from project0.models.validation_models import ValidationResult


class DocumentationWorkflowStatus(StrEnum):
    """Supported documentation workflow execution states."""

    PENDING = "pending"
    RUNNING = "running"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class ReviewDecision(StrEnum):
    """Supported user review decisions for proposed changes."""

    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"
    SKIP = "skip"


class ChangeApplicationStatus(StrEnum):
    """Supported documentation change application states."""

    PENDING = "pending"
    APPLIED = "applied"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DocumentationChangeProposal:
    """A proposed update to one repository documentation file."""

    repository_path: str
    original_content: str
    proposed_content: str
    rationale: str
    proposal_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class DocumentationReview:
    """The review decision for one documentation change proposal."""

    proposal_id: str
    decision: ReviewDecision
    feedback: str | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AppliedDocumentationChange:
    """Result of applying one reviewed documentation change."""

    proposal_id: str
    repository_path: str
    status: ChangeApplicationStatus
    applied_at: datetime | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentationWorkflowRequest:
    """Request to execute a documentation update workflow."""

    user_request: str
    target_paths: tuple[str, ...] = ()
    workflow_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class DocumentationWorkflowState:
    """State retained while a documentation workflow awaits user review."""

    workflow_id: str
    status: DocumentationWorkflowStatus
    started_at: datetime
    reasoning_result: ReasoningResult | None
    proposals: tuple[DocumentationChangeProposal, ...]
    reviews: tuple[DocumentationReview, ...] = ()
    applied_changes: tuple[AppliedDocumentationChange, ...] = ()
    preliminary_validation: ValidationResult | None = None
    warnings: tuple[str, ...] = ()
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentationWorkflowSummary:
    """Summary counts for a completed documentation workflow."""

    proposed_count: int
    approved_count: int
    revised_count: int
    rejected_count: int
    skipped_count: int
    applied_count: int
    failed_count: int


@dataclass(frozen=True, slots=True)
class DocumentationWorkflowResult:
    """Result of a complete documentation update workflow."""

    workflow_id: str
    status: DocumentationWorkflowStatus
    started_at: datetime
    completed_at: datetime
    reasoning_result: ReasoningResult | None
    proposals: tuple[DocumentationChangeProposal, ...]
    reviews: tuple[DocumentationReview, ...]
    applied_changes: tuple[AppliedDocumentationChange, ...]
    preliminary_validation: ValidationResult | None
    final_validation: ValidationResult | None
    git_diff: str | None
    summary: DocumentationWorkflowSummary
    warnings: tuple[str, ...] = ()
    error_message: str | None = None
