# ============================================================
# Project0 - Documentation Agent View Model Tests
#
# File: test_documentation_agent_view_models.py
#
# Purpose:
#     Verify Documentation Agent presentation models, defaults,
#     enum values, and convenience properties.
#
# ============================================================

from dataclasses import FrozenInstanceError

import pytest

from project0.agents.documentation.documentation_agent_view_models import (
    DifferenceLineType,
    DifferenceLineView,
    DocumentationAgentPageStatus,
    DocumentationAgentPageView,
    DocumentationDifferenceView,
    DocumentationProposalView,
    DocumentationRequestForm,
    DocumentationWorkflowSummaryView,
    ValidationDisplayStatus,
    ValidationMessageView,
    ValidationResultView,
)
from project0.models.documentation_workflow_models import ReviewDecision


def test_documentation_agent_page_status_values() -> None:
    """Documentation Agent page states should expose stable string values."""

    assert DocumentationAgentPageStatus.READY == "ready"
    assert DocumentationAgentPageStatus.PROCESSING == "processing"
    assert DocumentationAgentPageStatus.REVIEW_REQUIRED == "review_required"
    assert DocumentationAgentPageStatus.COMPLETED == "completed"
    assert (
        DocumentationAgentPageStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert DocumentationAgentPageStatus.FAILED == "failed"


def test_validation_display_status_values() -> None:
    """Validation display states should expose stable string values."""

    assert ValidationDisplayStatus.NOT_RUN == "not_run"
    assert ValidationDisplayStatus.PASSED == "passed"
    assert (
        ValidationDisplayStatus.PASSED_WITH_WARNINGS
        == "passed_with_warnings"
    )
    assert ValidationDisplayStatus.FAILED == "failed"


def test_difference_line_type_values() -> None:
    """Difference line types should expose stable string values."""

    assert DifferenceLineType.CONTEXT == "context"
    assert DifferenceLineType.ADDED == "added"
    assert DifferenceLineType.REMOVED == "removed"
    assert DifferenceLineType.HEADER == "header"


def test_documentation_request_form_defaults() -> None:
    """A new request form should begin empty."""

    request_form = DocumentationRequestForm()

    assert request_form.user_request == ""
    assert request_form.target_paths == ()


def test_validation_result_passed_property() -> None:
    """Passed should include successful validation with or without warnings."""

    passed = ValidationResultView(
        status=ValidationDisplayStatus.PASSED,
        title="Validation passed",
        summary="No issues found.",
    )
    passed_with_warnings = ValidationResultView(
        status=ValidationDisplayStatus.PASSED_WITH_WARNINGS,
        title="Validation passed with warnings",
        summary="Warnings require review.",
        warning_count=1,
    )
    failed = ValidationResultView(
        status=ValidationDisplayStatus.FAILED,
        title="Validation failed",
        summary="Errors require correction.",
        error_count=1,
    )
    not_run = ValidationResultView(
        status=ValidationDisplayStatus.NOT_RUN,
        title="Validation not run",
        summary="Validation has not started.",
    )

    assert passed.passed is True
    assert passed_with_warnings.passed is True
    assert failed.passed is False
    assert not_run.passed is False


def test_validation_result_has_messages_property() -> None:
    """Validation results should report whether display messages exist."""

    empty_result = ValidationResultView(
        status=ValidationDisplayStatus.PASSED,
        title="Validation passed",
        summary="No issues found.",
    )
    result_with_message = ValidationResultView(
        status=ValidationDisplayStatus.PASSED_WITH_WARNINGS,
        title="Validation passed with warnings",
        summary="One warning found.",
        warning_count=1,
        messages=(
            ValidationMessageView(
                validator_name="MarkdownValidator",
                message="Heading level skipped.",
                severity="warning",
                repository_path="docs/Example.md",
                line_number=12,
            ),
        ),
    )

    assert empty_result.has_messages is False
    assert result_with_message.has_messages is True


def test_documentation_difference_has_differences_property() -> None:
    """Documentation differences should identify empty and populated states."""

    empty_difference = DocumentationDifferenceView(
        repository_path="docs/Example.md"
    )
    populated_difference = DocumentationDifferenceView(
        repository_path="docs/Example.md",
        lines=(
            DifferenceLineView(
                line_type=DifferenceLineType.REMOVED,
                content="-Old content",
                old_line_number=4,
            ),
            DifferenceLineView(
                line_type=DifferenceLineType.ADDED,
                content="+New content",
                new_line_number=4,
            ),
        ),
    )

    assert empty_difference.has_differences is False
    assert populated_difference.has_differences is True


def test_documentation_proposal_has_decision_property() -> None:
    """A proposal should report whether a review decision was selected."""

    undecided = DocumentationProposalView(
        proposal_id="proposal-1",
        repository_path="docs/Example.md",
        rationale="Update the implementation status.",
        original_content="Old content",
        proposed_content="New content",
    )
    approved = DocumentationProposalView(
        proposal_id="proposal-2",
        repository_path="docs/Example.md",
        rationale="Update the implementation status.",
        original_content="Old content",
        proposed_content="New content",
        selected_decision=ReviewDecision.APPROVE,
    )

    assert undecided.has_decision is False
    assert approved.has_decision is True


def test_documentation_agent_page_requires_review() -> None:
    """Review should be required only for review-ready pages with proposals."""

    proposal = DocumentationProposalView(
        proposal_id="proposal-1",
        repository_path="docs/Example.md",
        rationale="Update the implementation status.",
        original_content="Old content",
        proposed_content="New content",
    )

    review_page = DocumentationAgentPageView(
        page_status=DocumentationAgentPageStatus.REVIEW_REQUIRED,
        status_message="Review the proposed documentation changes.",
        request_form=DocumentationRequestForm(
            user_request="Update the implementation status."
        ),
        workflow_id="workflow-1",
        proposals=(proposal,),
    )
    empty_review_page = DocumentationAgentPageView(
        page_status=DocumentationAgentPageStatus.REVIEW_REQUIRED,
        status_message="No proposals are available.",
        request_form=DocumentationRequestForm(),
    )
    processing_page = DocumentationAgentPageView(
        page_status=DocumentationAgentPageStatus.PROCESSING,
        status_message="Generating proposed changes.",
        request_form=DocumentationRequestForm(),
        proposals=(proposal,),
    )

    assert review_page.requires_review is True
    assert empty_review_page.requires_review is False
    assert processing_page.requires_review is False


def test_documentation_agent_page_warning_and_error_properties() -> None:
    """Page helpers should identify warning and error states."""

    page = DocumentationAgentPageView(
        page_status=DocumentationAgentPageStatus.FAILED,
        status_message="The documentation workflow failed.",
        request_form=DocumentationRequestForm(
            user_request="Update the implementation status."
        ),
        warnings=("One document could not be selected.",),
        error_message="Reasoning service unavailable.",
    )

    assert page.has_warnings is True
    assert page.has_error is True


def test_documentation_agent_page_defaults() -> None:
    """Optional page collections and results should have safe defaults."""

    page = DocumentationAgentPageView(
        page_status=DocumentationAgentPageStatus.READY,
        status_message="Ready for a documentation request.",
        request_form=DocumentationRequestForm(),
    )

    assert page.workflow_id is None
    assert page.proposals == ()
    assert page.preliminary_validation is None
    assert page.final_validation is None
    assert page.workflow_summary is None
    assert page.warnings == ()
    assert page.error_message is None
    assert page.requires_review is False
    assert page.has_warnings is False
    assert page.has_error is False


def test_documentation_workflow_summary_defaults() -> None:
    """Workflow summary counters should default to zero."""

    summary = DocumentationWorkflowSummaryView()

    assert summary.proposed_count == 0
    assert summary.approved_count == 0
    assert summary.revised_count == 0
    assert summary.rejected_count == 0
    assert summary.skipped_count == 0
    assert summary.applied_count == 0
    assert summary.failed_count == 0


def test_view_models_are_immutable() -> None:
    """Presentation models should not be mutable after construction."""

    request_form = DocumentationRequestForm(
        user_request="Update the implementation status."
    )

    with pytest.raises(FrozenInstanceError):
        request_form.user_request = "Changed request"
