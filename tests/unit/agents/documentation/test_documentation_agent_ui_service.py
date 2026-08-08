# ============================================================
# Project0 - Documentation Agent UI Service Tests
#
# File: test_documentation_agent_ui_service.py
#
# Purpose:
#     Verify Documentation Agent UI service request handling,
#     workflow mapping, review processing, and failure states.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project0.agents.documentation.documentation_agent_ui_service import (
    DocumentationAgentUIService,
)
from project0.agents.documentation.documentation_agent_view_models import (
    DifferenceLineType,
    DocumentationAgentPageStatus,
    ValidationDisplayStatus,
)
from project0.models.documentation_workflow_models import ReviewDecision


@dataclass
class FakeWorkflow:
    """Simple workflow fake used by UI service tests."""

    result: object | None = None
    error: Exception | None = None
    review_result: object | None = None
    review_error: Exception | None = None
    received_arguments: dict[str, Any] | None = None
    received_review: tuple[str, object] | None = None

    def run_documentation_workflow(
        self,
        user_request: str,
        target_paths: tuple[str, ...] = (),
        workflow_id: str | None = None,
    ) -> object:
        """Record request arguments and return or raise the configured result."""

        self.received_arguments = {
            "user_request": user_request,
            "target_paths": target_paths,
            "workflow_id": workflow_id,
        }

        if self.error is not None:
            raise self.error

        return self.result

    def submit_documentation_review(
        self,
        workflow_id: str,
        review: object,
    ) -> object:
        """Record the review and return or raise the configured result."""

        self.received_review = (workflow_id, review)

        if self.review_error is not None:
            raise self.review_error

        return self.review_result


def test_create_ready_page() -> None:
    """The initial page should be ready with an empty request form."""

    service = DocumentationAgentUIService(workflow=FakeWorkflow())

    page = service.create_ready_page()

    assert page.page_status is DocumentationAgentPageStatus.READY
    assert page.status_message == "Ready for a documentation request."
    assert page.request_form.user_request == ""
    assert page.request_form.target_paths == ()
    assert page.workflow_id is None
    assert page.proposals == ()
    assert page.has_error is False


def test_submit_request_requires_nonempty_request() -> None:
    """Blank documentation requests should fail before workflow execution."""

    workflow = FakeWorkflow()
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request(
        user_request="   ",
        target_paths=(" docs/Example.md ",),
    )

    assert page.page_status is DocumentationAgentPageStatus.FAILED
    assert page.status_message == "A documentation request is required."
    assert page.error_message == (
        "Enter a documentation request before continuing."
    )
    assert page.request_form.user_request == ""
    assert page.request_form.target_paths == ("docs/Example.md",)
    assert workflow.received_arguments is None


def test_submit_request_normalizes_form_values() -> None:
    """Submitted requests and target paths should be stripped and filtered."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-1",
            "status": "running",
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request(
        user_request="  Update the implementation status.  ",
        target_paths=(
            " docs/Implementation_Status.md ",
            "",
            "   ",
            "docs/Dashboard_Design.md",
        ),
    )

    assert workflow.received_arguments == {
        "user_request": "Update the implementation status.",
        "target_paths": (
            "docs/Implementation_Status.md",
            "docs/Dashboard_Design.md",
        ),
        "workflow_id": None,
    }
    assert page.request_form.user_request == (
        "Update the implementation status."
    )
    assert page.request_form.target_paths == (
        "docs/Implementation_Status.md",
        "docs/Dashboard_Design.md",
    )
    assert page.page_status is DocumentationAgentPageStatus.PROCESSING


def test_submit_request_maps_review_ready_workflow_result() -> None:
    """Workflow proposals should be converted to review-ready page state."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-2",
            "status": "review_required",
            "proposals": (
                {
                    "proposal_id": "proposal-1",
                    "repository_path": "docs/Implementation_Status.md",
                    "rationale": "Record the Phase 8 start.",
                    "original_content": "Phase 8: Ready to Begin",
                    "proposed_content": "Phase 8: In Progress",
                    "difference": {
                        "repository_path": (
                            "docs/Implementation_Status.md"
                        ),
                        "lines": (
                            {
                                "line_type": "removed",
                                "content": "-Phase 8: Ready to Begin",
                                "old_line_number": 10,
                            },
                            {
                                "line_type": "added",
                                "content": "+Phase 8: In Progress",
                                "new_line_number": 10,
                            },
                        ),
                    },
                },
            ),
            "preliminary_validation": {
                "status": "passed_with_warnings",
                "issues": (
                    {
                        "validator_name": "MarkdownValidator",
                        "message": "Heading level should be reviewed.",
                        "severity": "warning",
                        "repository_path": (
                            "docs/Implementation_Status.md"
                        ),
                        "line_number": 10,
                    },
                ),
            },
            "summary": {
                "proposed_count": 1,
            },
            "warnings": ("Review the heading level.",),
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request(
        user_request="Update Phase 8 status.",
        target_paths=("docs/Implementation_Status.md",),
    )

    assert page.page_status is DocumentationAgentPageStatus.REVIEW_REQUIRED
    assert page.requires_review is True
    assert page.workflow_id == "workflow-2"
    assert len(page.proposals) == 1

    proposal = page.proposals[0]
    assert proposal.proposal_id == "proposal-1"
    assert proposal.repository_path == "docs/Implementation_Status.md"
    assert proposal.rationale == "Record the Phase 8 start."
    assert proposal.has_decision is False
    assert proposal.difference is not None
    assert proposal.difference.has_differences is True
    assert proposal.difference.lines[0].line_type is DifferenceLineType.REMOVED
    assert proposal.difference.lines[1].line_type is DifferenceLineType.ADDED

    validation = page.preliminary_validation
    assert validation is not None
    assert validation.status is ValidationDisplayStatus.PASSED_WITH_WARNINGS
    assert validation.passed is True
    assert validation.warning_count == 1
    assert validation.has_messages is True
    assert validation.messages[0].validator_name == "MarkdownValidator"
    assert validation.messages[0].line_number == 10

    assert page.workflow_summary is not None
    assert page.workflow_summary.proposed_count == 1
    assert page.warnings == ("Review the heading level.",)
    assert page.has_warnings is True


def test_submit_request_maps_completed_result() -> None:
    """A completed workflow should produce a completed page state."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-3",
            "status": "completed",
            "proposals": (
                {
                    "proposal_id": "proposal-1",
                    "repository_path": "docs/Example.md",
                    "rationale": "Apply the approved update.",
                    "original_content": "Old",
                    "proposed_content": "New",
                },
            ),
            "reviews": (
                {
                    "proposal_id": "proposal-1",
                    "decision": "approve",
                },
            ),
            "final_validation": {
                "status": "passed",
                "issues": (),
            },
            "summary": {
                "proposed_count": 1,
                "approved_count": 1,
                "applied_count": 1,
            },
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request("Update the example.")

    assert page.page_status is DocumentationAgentPageStatus.COMPLETED
    assert page.status_message == (
        "The documentation workflow completed successfully."
    )
    assert page.proposals[0].selected_decision is ReviewDecision.APPROVE
    assert page.proposals[0].has_decision is True
    assert page.final_validation is not None
    assert page.final_validation.status is ValidationDisplayStatus.PASSED
    assert page.final_validation.title == "Validation passed"
    assert page.workflow_summary is not None
    assert page.workflow_summary.approved_count == 1
    assert page.workflow_summary.applied_count == 1


def test_submit_request_maps_completed_with_warnings_result() -> None:
    """Completed workflows with warnings should use the warning page state."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-4",
            "status": "completed_with_warnings",
            "warnings": ("One optional link check was skipped.",),
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request("Update documentation.")

    assert (
        page.page_status
        is DocumentationAgentPageStatus.COMPLETED_WITH_WARNINGS
    )
    assert page.status_message == (
        "The documentation workflow completed with warnings."
    )
    assert page.has_warnings is True


def test_submit_request_maps_failed_preliminary_validation() -> None:
    """Failed preliminary validation should expose validator issues."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-validation-failed",
            "status": "failed",
            "error_message": (
                "Preliminary documentation validation failed."
            ),
            "preliminary_validation": {
                "status": "failed",
                "error_message": "Validation found blocking issues.",
                "issues": (
                    {
                        "validator_name": "MarkdownValidator",
                        "message": "Malformed Markdown heading.",
                        "severity": "error",
                        "repository_path": "docs/Implementation_Status.md",
                        "line_number": 12,
                    },
                    {
                        "validator_name": "LinkValidator",
                        "message": "Optional link should be reviewed.",
                        "severity": "warning",
                        "repository_path": "docs/Implementation_Status.md",
                    },
                ),
            },
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request("Update documentation.")

    assert page.page_status is DocumentationAgentPageStatus.FAILED
    assert page.preliminary_validation is not None
    assert (
        page.preliminary_validation.status
        is ValidationDisplayStatus.FAILED
    )
    assert page.preliminary_validation.error_count == 1
    assert page.preliminary_validation.warning_count == 1
    assert page.preliminary_validation.summary == (
        "Validation found blocking issues."
    )
    assert len(page.preliminary_validation.messages) == 2
    assert (
        page.preliminary_validation.messages[0].validator_name
        == "MarkdownValidator"
    )
    assert (
        page.preliminary_validation.messages[0].message
        == "Malformed Markdown heading."
    )
    assert page.preliminary_validation.messages[0].line_number == 12
    assert (
        page.preliminary_validation.messages[1].validator_name
        == "LinkValidator"
    )


def test_submit_request_maps_explicit_failed_status() -> None:
    """An explicit workflow page status should be honored."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-5",
            "status": "failed",
            "error_message": "Validation failed.",
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request("Update documentation.")

    assert page.page_status is DocumentationAgentPageStatus.FAILED
    assert page.error_message == "Validation failed."
    assert page.has_error is True


def test_submit_request_handles_workflow_exception() -> None:
    """Workflow exceptions should become consistent failure pages."""

    workflow = FakeWorkflow(error=RuntimeError("Reasoning service unavailable."))
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request(
        user_request="Update documentation.",
        target_paths=("docs/Example.md",),
    )

    assert page.page_status is DocumentationAgentPageStatus.FAILED
    assert page.status_message == (
        "The documentation workflow could not be completed."
    )
    assert page.error_message == "Reasoning service unavailable."
    assert page.request_form.user_request == "Update documentation."
    assert page.request_form.target_paths == ("docs/Example.md",)


def test_submit_review_decision_normalizes_feedback_and_maps_result() -> None:
    """Review decisions should be forwarded and mapped to updated state."""

    workflow = FakeWorkflow(
        review_result={
            "workflow_id": "workflow-6",
            "status": "completed",
            "proposals": (
                {
                    "proposal_id": "proposal-1",
                    "repository_path": "docs/Example.md",
                    "rationale": "Apply the approved update.",
                    "original_content": "Old",
                    "proposed_content": "New",
                },
            ),
            "reviews": (
                {
                    "proposal_id": "proposal-1",
                    "decision": "approve",
                    "feedback": "Looks correct.",
                },
            ),
            "summary": {
                "proposed_count": 1,
                "approved_count": 1,
                "applied_count": 1,
            },
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_review_decision(
        workflow_id="workflow-6",
        proposal_id="proposal-1",
        decision=ReviewDecision.APPROVE,
        feedback="  Looks correct.  ",
    )

    assert workflow.received_review is not None
    received_workflow_id, received_review = workflow.received_review
    assert received_workflow_id == "workflow-6"
    assert received_review.proposal_id == "proposal-1"
    assert received_review.decision is ReviewDecision.APPROVE
    assert received_review.feedback == "Looks correct."
    assert received_review.reviewed_at.tzinfo is not None

    assert page.page_status is DocumentationAgentPageStatus.COMPLETED
    assert page.workflow_id == "workflow-6"
    assert page.proposals[0].selected_decision is ReviewDecision.APPROVE
    assert page.proposals[0].feedback == "Looks correct."


def test_submit_review_decision_converts_blank_feedback_to_none() -> None:
    """Blank review feedback should be submitted as None."""

    workflow = FakeWorkflow(
        review_result={
            "workflow_id": "workflow-7",
            "status": "review_required",
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    service.submit_review_decision(
        workflow_id="workflow-7",
        proposal_id="proposal-1",
        decision=ReviewDecision.SKIP,
        feedback="   ",
    )

    assert workflow.received_review is not None
    _, received_review = workflow.received_review
    assert received_review.feedback is None


def test_submit_review_decision_handles_exception() -> None:
    """Workflow review exceptions should become failure pages."""

    workflow = FakeWorkflow(
        review_error=RuntimeError("Review state was not found.")
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_review_decision(
        workflow_id="workflow-8",
        proposal_id="proposal-1",
        decision=ReviewDecision.REJECT,
        feedback="Do not apply this change.",
    )

    assert page.page_status is DocumentationAgentPageStatus.FAILED
    assert page.status_message == (
        "The review decision could not be processed."
    )
    assert page.error_message == "Review state was not found."
    assert page.workflow_id == "workflow-8"


def test_unknown_mapped_values_use_safe_defaults() -> None:
    """Unknown status and line values should not break page mapping."""

    workflow = FakeWorkflow(
        result={
            "workflow_id": "workflow-9",
            "status": "unknown-workflow-status",
            "proposals": (
                {
                    "proposal_id": "proposal-1",
                    "repository_path": "docs/Example.md",
                    "rationale": "Test safe mappings.",
                    "original_content": "Old",
                    "proposed_content": "New",
                },
            ),
            "preliminary_validation": {
                "status": "unknown-validation-status",
                "issues": (),
            },
        }
    )
    service = DocumentationAgentUIService(workflow=workflow)

    page = service.submit_request("Test safe mappings.")

    assert page.page_status is DocumentationAgentPageStatus.REVIEW_REQUIRED
    assert page.proposals[0].selected_decision is None
    assert (
        page.proposals[0].difference.lines[0].line_type
        is DifferenceLineType.REMOVED
    )
    assert (
        page.proposals[0].difference.lines[1].line_type
        is DifferenceLineType.ADDED
    )
    assert page.preliminary_validation is not None
    assert (
        page.preliminary_validation.status
        is ValidationDisplayStatus.NOT_RUN
    )
