# ============================================================
# Project0 - Documentation Workflow Models Tests
#
# File: test_documentation_workflow_models.py
#
# Purpose:
#     Verify shared documentation workflow models used to
#     propose, review, apply, and summarize documentation changes.
#
# ============================================================

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest

from project0.models.documentation_workflow_models import (
    AppliedDocumentationChange,
    ChangeApplicationStatus,
    DocumentationChangeProposal,
    DocumentationReview,
    DocumentationWorkflowRequest,
    DocumentationWorkflowResult,
    DocumentationWorkflowState,
    DocumentationWorkflowStatus,
    DocumentationWorkflowSummary,
    ReviewDecision,
)


def test_documentation_workflow_status_values() -> None:
    """DocumentationWorkflowStatus defines expected string values."""

    assert DocumentationWorkflowStatus.PENDING == "pending"
    assert DocumentationWorkflowStatus.RUNNING == "running"
    assert (
        DocumentationWorkflowStatus.REVIEW_REQUIRED
        == "review_required"
    )
    assert DocumentationWorkflowStatus.COMPLETED == "completed"
    assert (
        DocumentationWorkflowStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert DocumentationWorkflowStatus.FAILED == "failed"


def test_review_decision_values() -> None:
    """ReviewDecision defines expected user review values."""

    assert ReviewDecision.APPROVE == "approve"
    assert ReviewDecision.REVISE == "revise"
    assert ReviewDecision.REJECT == "reject"
    assert ReviewDecision.SKIP == "skip"


def test_change_application_status_values() -> None:
    """ChangeApplicationStatus defines expected string values."""

    assert ChangeApplicationStatus.PENDING == "pending"
    assert ChangeApplicationStatus.APPLIED == "applied"
    assert ChangeApplicationStatus.SKIPPED == "skipped"
    assert ChangeApplicationStatus.FAILED == "failed"


def test_documentation_change_proposal_generates_unique_identifier() -> None:
    """DocumentationChangeProposal generates a unique UUID by default."""

    first = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the heading.",
    )
    second = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the heading.",
    )

    UUID(first.proposal_id)
    UUID(second.proposal_id)

    assert first.proposal_id != second.proposal_id


def test_documentation_change_proposal_preserves_values() -> None:
    """DocumentationChangeProposal preserves supplied content."""

    proposal = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the heading.",
        proposal_id="proposal-001",
    )

    assert proposal.proposal_id == "proposal-001"
    assert proposal.repository_path == "docs/index.md"
    assert proposal.original_content == "# Original\n"
    assert proposal.proposed_content == "# Updated\n"
    assert proposal.rationale == "Update the heading."
    assert proposal.anchor_text is None


def test_documentation_change_proposal_preserves_anchor_text() -> None:
    """DocumentationChangeProposal preserves supplied anchor text."""

    proposal = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="Updated content.\n",
        rationale="Update the section content.",
        anchor_text="## Phase 8",
        proposal_id="proposal-002",
    )

    assert proposal.anchor_text == "## Phase 8"


def test_documentation_review_defaults() -> None:
    """DocumentationReview defaults feedback and timestamp to None."""

    review = DocumentationReview(
        proposal_id="proposal-001",
        decision=ReviewDecision.APPROVE,
    )

    assert review.proposal_id == "proposal-001"
    assert review.decision is ReviewDecision.APPROVE
    assert review.feedback is None
    assert review.reviewed_at is None


def test_documentation_review_preserves_optional_values() -> None:
    """DocumentationReview preserves feedback and review timestamp."""

    reviewed_at = datetime(2026, 8, 5, 11, 0, tzinfo=UTC)

    review = DocumentationReview(
        proposal_id="proposal-001",
        decision=ReviewDecision.REVISE,
        feedback="Clarify the rationale.",
        reviewed_at=reviewed_at,
    )

    assert review.feedback == "Clarify the rationale."
    assert review.reviewed_at == reviewed_at


def test_applied_documentation_change_defaults() -> None:
    """AppliedDocumentationChange defaults optional fields to None."""

    change = AppliedDocumentationChange(
        proposal_id="proposal-001",
        repository_path="docs/index.md",
        status=ChangeApplicationStatus.PENDING,
    )

    assert change.applied_at is None
    assert change.error_message is None


def test_applied_documentation_change_preserves_failure() -> None:
    """AppliedDocumentationChange preserves failure information."""

    change = AppliedDocumentationChange(
        proposal_id="proposal-001",
        repository_path="docs/index.md",
        status=ChangeApplicationStatus.FAILED,
        error_message="Original content no longer matches.",
    )

    assert change.status is ChangeApplicationStatus.FAILED
    assert change.error_message == "Original content no longer matches."


def test_documentation_workflow_request_generates_unique_identifier() -> None:
    """DocumentationWorkflowRequest generates a unique UUID by default."""

    first = DocumentationWorkflowRequest(
        user_request="Update the architecture documentation."
    )
    second = DocumentationWorkflowRequest(
        user_request="Update the architecture documentation."
    )

    UUID(first.workflow_id)
    UUID(second.workflow_id)

    assert first.workflow_id != second.workflow_id


def test_documentation_workflow_request_defaults_target_paths() -> None:
    """DocumentationWorkflowRequest defaults to no target paths."""

    request = DocumentationWorkflowRequest(
        user_request="Review documentation."
    )

    assert request.target_paths == ()


def test_documentation_workflow_request_preserves_values() -> None:
    """DocumentationWorkflowRequest preserves supplied values."""

    request = DocumentationWorkflowRequest(
        user_request="Update selected documents.",
        target_paths=(
            "docs/Documentation_Agent_Architecture.md",
            "docs/Documentation_Agent_Design.md",
        ),
        workflow_id="workflow-001",
    )

    assert request.workflow_id == "workflow-001"
    assert request.user_request == "Update selected documents."
    assert request.target_paths == (
        "docs/Documentation_Agent_Architecture.md",
        "docs/Documentation_Agent_Design.md",
    )


def test_documentation_workflow_state_defaults() -> None:
    """DocumentationWorkflowState defaults retained review state."""

    started_at = datetime(2026, 8, 5, 11, 0, tzinfo=UTC)
    proposal = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the heading.",
        proposal_id="proposal-001",
    )

    state = DocumentationWorkflowState(
        workflow_id="workflow-001",
        status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
        started_at=started_at,
        user_request="Update the documentation.",
        target_paths=("docs/index.md",),
        reasoning_result=None,
        proposals=(proposal,),
    )

    assert state.workflow_id == "workflow-001"
    assert state.status is DocumentationWorkflowStatus.REVIEW_REQUIRED
    assert state.started_at == started_at
    assert state.reasoning_result is None
    assert state.proposals == (proposal,)
    assert state.reviews == ()
    assert state.applied_changes == ()
    assert state.preliminary_validation is None
    assert state.warnings == ()
    assert state.error_message is None


def test_documentation_workflow_state_preserves_optional_values() -> None:
    """DocumentationWorkflowState preserves accumulated workflow values."""

    started_at = datetime(2026, 8, 5, 11, 0, tzinfo=UTC)
    reviewed_at = datetime(2026, 8, 5, 11, 5, tzinfo=UTC)

    proposal = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the heading.",
        proposal_id="proposal-001",
    )
    review = DocumentationReview(
        proposal_id="proposal-001",
        decision=ReviewDecision.APPROVE,
        reviewed_at=reviewed_at,
    )
    applied_change = AppliedDocumentationChange(
        proposal_id="proposal-001",
        repository_path="docs/index.md",
        status=ChangeApplicationStatus.APPLIED,
        applied_at=reviewed_at,
    )

    state = DocumentationWorkflowState(
        workflow_id="workflow-001",
        status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
        started_at=started_at,
        user_request="Update the documentation.",
        target_paths=("docs/index.md",),
        reasoning_result=None,
        proposals=(proposal,),
        reviews=(review,),
        applied_changes=(applied_change,),
        preliminary_validation=None,
        warnings=("Review remains pending.",),
        error_message=None,
    )

    assert state.reviews == (review,)
    assert state.applied_changes == (applied_change,)
    assert state.warnings == ("Review remains pending.",)
    assert state.error_message is None


def test_documentation_workflow_summary_preserves_counts() -> None:
    """DocumentationWorkflowSummary preserves all summary counts."""

    summary = DocumentationWorkflowSummary(
        proposed_count=5,
        approved_count=2,
        revised_count=1,
        rejected_count=1,
        skipped_count=1,
        applied_count=2,
        failed_count=0,
    )

    assert summary.proposed_count == 5
    assert summary.approved_count == 2
    assert summary.revised_count == 1
    assert summary.rejected_count == 1
    assert summary.skipped_count == 1
    assert summary.applied_count == 2
    assert summary.failed_count == 0


def test_documentation_workflow_result_preserves_values() -> None:
    """DocumentationWorkflowResult preserves composed workflow values."""

    started_at = datetime(2026, 8, 5, 11, 0, tzinfo=UTC)
    completed_at = datetime(2026, 8, 5, 11, 5, tzinfo=UTC)

    proposal = DocumentationChangeProposal(
        repository_path="docs/index.md",
        original_content="# Original\n",
        proposed_content="# Updated\n",
        rationale="Update the heading.",
        proposal_id="proposal-001",
    )
    review = DocumentationReview(
        proposal_id="proposal-001",
        decision=ReviewDecision.APPROVE,
        reviewed_at=completed_at,
    )
    applied_change = AppliedDocumentationChange(
        proposal_id="proposal-001",
        repository_path="docs/index.md",
        status=ChangeApplicationStatus.APPLIED,
        applied_at=completed_at,
    )
    summary = DocumentationWorkflowSummary(
        proposed_count=1,
        approved_count=1,
        revised_count=0,
        rejected_count=0,
        skipped_count=0,
        applied_count=1,
        failed_count=0,
    )

    result = DocumentationWorkflowResult(
        workflow_id="workflow-001",
        status=DocumentationWorkflowStatus.COMPLETED,
        started_at=started_at,
        completed_at=completed_at,
        reasoning_result=None,
        proposals=(proposal,),
        reviews=(review,),
        applied_changes=(applied_change,),
        preliminary_validation=None,
        final_validation=None,
        git_diff="diff --git a/docs/index.md b/docs/index.md",
        summary=summary,
    )

    assert result.workflow_id == "workflow-001"
    assert result.status is DocumentationWorkflowStatus.COMPLETED
    assert result.started_at == started_at
    assert result.completed_at == completed_at
    assert result.reasoning_result is None
    assert result.proposals == (proposal,)
    assert result.reviews == (review,)
    assert result.applied_changes == (applied_change,)
    assert result.preliminary_validation is None
    assert result.final_validation is None
    assert result.git_diff == "diff --git a/docs/index.md b/docs/index.md"
    assert result.summary == summary
    assert result.warnings == ()
    assert result.error_message is None


def test_documentation_workflow_result_preserves_warnings_and_error() -> None:
    """DocumentationWorkflowResult preserves warnings and error message."""

    timestamp = datetime(2026, 8, 5, 11, 0, tzinfo=UTC)
    summary = DocumentationWorkflowSummary(
        proposed_count=0,
        approved_count=0,
        revised_count=0,
        rejected_count=0,
        skipped_count=0,
        applied_count=0,
        failed_count=1,
    )

    result = DocumentationWorkflowResult(
        workflow_id="workflow-001",
        status=DocumentationWorkflowStatus.FAILED,
        started_at=timestamp,
        completed_at=timestamp,
        reasoning_result=None,
        proposals=(),
        reviews=(),
        applied_changes=(),
        preliminary_validation=None,
        final_validation=None,
        git_diff=None,
        summary=summary,
        warnings=("Validation did not complete.",),
        error_message="Workflow execution failed.",
    )

    assert result.warnings == ("Validation did not complete.",)
    assert result.error_message == "Workflow execution failed."


@pytest.mark.parametrize(
    ("model", "attribute_name", "new_value"),
    [
        (
            DocumentationChangeProposal(
                repository_path="docs/index.md",
                original_content="# Original\n",
                proposed_content="# Updated\n",
                rationale="Update heading.",
            ),
            "repository_path",
            "docs/other.md",
        ),
        (
            DocumentationReview(
                proposal_id="proposal-001",
                decision=ReviewDecision.APPROVE,
            ),
            "decision",
            ReviewDecision.REJECT,
        ),
        (
            AppliedDocumentationChange(
                proposal_id="proposal-001",
                repository_path="docs/index.md",
                status=ChangeApplicationStatus.PENDING,
            ),
            "status",
            ChangeApplicationStatus.APPLIED,
        ),
        (
            DocumentationWorkflowRequest(
                user_request="Update documentation."
            ),
            "user_request",
            "Changed request.",
        ),
        (
            DocumentationWorkflowState(
                workflow_id="workflow-001",
                status=DocumentationWorkflowStatus.REVIEW_REQUIRED,
                started_at=datetime(2026, 8, 5, 11, 0, tzinfo=UTC),
                user_request="Update the documentation.",
                target_paths=("docs/index.md",),
                reasoning_result=None,
                proposals=(),
            ),
            "status",
            DocumentationWorkflowStatus.COMPLETED,
        ),
        (
            DocumentationWorkflowSummary(
                proposed_count=1,
                approved_count=1,
                revised_count=0,
                rejected_count=0,
                skipped_count=0,
                applied_count=1,
                failed_count=0,
            ),
            "applied_count",
            2,
        ),
    ],
)
def test_documentation_workflow_models_are_immutable(
    model: object,
    attribute_name: str,
    new_value: object,
) -> None:
    """Documentation workflow model instances are immutable."""

    with pytest.raises(FrozenInstanceError):
        setattr(model, attribute_name, new_value)
