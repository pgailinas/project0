# ============================================================
# Project0 - Documentation Agent UI Flow Integration Tests
#
# File: test_documentation_agent_ui_flow.py
#
# Purpose:
#     Verify the browser-facing Documentation Agent workflow
#     across routes, UI service, templates, review decisions,
#     validation presentation, and documentation differences.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from project0.agents.documentation.documentation_agent_routes import (
    create_documentation_agent_router,
)
from project0.agents.documentation.documentation_agent_ui_service import (
    DocumentationAgentUIService,
)
from project0.models.documentation_workflow_models import ReviewDecision


@dataclass
class FakeDocumentationWorkflow:
    """Workflow fake for the browser-facing interactive UI flow."""

    received_request: dict[str, Any] | None = None
    received_review: tuple[str, object] | None = None

    def run_documentation_workflow(
        self,
        user_request: str,
        target_paths: tuple[str, ...] = (),
        workflow_id: str | None = None,
    ) -> object:
        """Return a representative review-required workflow state."""

        self.received_request = {
            "user_request": user_request,
            "target_paths": target_paths,
            "workflow_id": workflow_id,
        }

        return {
            "workflow_id": "workflow-integration-1",
            "status": "review_required",
            "proposals": (
                {
                    "proposal_id": "proposal-integration-1",
                    "repository_path": "docs/Implementation_Status.md",
                    "rationale": (
                        "Update the implementation status to show that "
                        "Phase 8 is in progress."
                    ),
                    "original_content": (
                        "Phase 8 — Documentation Agent User Interface\n"
                        "Status: Ready to Begin"
                    ),
                    "proposed_content": (
                        "Phase 8 — Documentation Agent User Interface\n"
                        "Status: In Progress"
                    ),
                },
            ),
            "preliminary_validation": {
                "status": "passed_with_warnings",
                "title": "Preliminary validation",
                "summary": (
                    "The proposed documentation change passed validation "
                    "with one warning."
                ),
                "error_count": 0,
                "warning_count": 1,
                "messages": (
                    {
                        "validator_name": "DocumentationConsistencyValidator",
                        "message": (
                            "Confirm that related Phase 8 documentation "
                            "uses the same status."
                        ),
                        "severity": "warning",
                        "repository_path": "docs/Implementation_Status.md",
                        "line_number": 42,
                    },
                ),
            },
            "summary": {"proposed_count": 1},
            "warnings": (
                "Related Phase 8 documentation may require a later update.",
            ),
        }

    def submit_documentation_review(
        self,
        workflow_id: str,
        review: object,
    ) -> object:
        """Record a browser review and return completed workflow state."""

        self.received_review = (workflow_id, review)

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "proposals": (
                {
                    "proposal_id": review.proposal_id,
                    "repository_path": "docs/Implementation_Status.md",
                    "rationale": (
                        "Update the implementation status to show that "
                        "Phase 8 is in progress."
                    ),
                    "original_content": (
                        "Phase 8 — Documentation Agent User Interface\n"
                        "Status: Ready to Begin"
                    ),
                    "proposed_content": (
                        "Phase 8 — Documentation Agent User Interface\n"
                        "Status: In Progress"
                    ),
                },
            ),
            "reviews": (
                {
                    "proposal_id": review.proposal_id,
                    "decision": review.decision.value,
                    "feedback": review.feedback,
                },
            ),
            "final_validation": {
                "status": "passed",
                "title": "Final validation",
                "summary": "All final validation checks passed.",
                "error_count": 0,
                "warning_count": 0,
                "messages": (),
            },
            "summary": {
                "proposed_count": 1,
                "approved_count": 1,
                "applied_count": 1,
            },
        }


def _template_directories() -> list[str]:
    """Return shared Dashboard and Documentation Agent template paths."""

    source_root = Path(__file__).resolve().parents[2] / "src" / "project0"

    return [
        str(source_root / "dashboard" / "templates"),
        str(
            source_root
            / "agents"
            / "documentation"
            / "templates"
        ),
    ]


def _build_client() -> tuple[
    TestClient,
    FakeDocumentationWorkflow,
]:
    """Create an integrated FastAPI application for the UI flow."""

    workflow = FakeDocumentationWorkflow()

    ui_service = DocumentationAgentUIService(
        workflow=workflow,
    )

    templates = Jinja2Templates(directory=_template_directories())

    app = FastAPI()
    app.include_router(
        create_documentation_agent_router(
            ui_service=ui_service,
            templates=templates,
        )
    )

    return TestClient(app), workflow


def test_documentation_agent_home_page_renders_shared_dashboard() -> None:
    """The Documentation Agent should render inside the Dashboard shell."""

    client, _ = _build_client()

    response = client.get("/agents/documentation")

    assert response.status_code == 200
    assert "Documentation Agent" in response.text
    assert "Documentation Request" in response.text
    assert "Workflow Status" in response.text
    assert "Ready for a documentation request." in response.text
    assert 'action="/agents/documentation/request"' in response.text


def test_documentation_request_presents_review_validation_and_diff() -> None:
    """A submitted request should present the complete review state."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/documentation/request",
        data={
            "user_request": (
                "Update the implementation status for Phase 8."
            ),
            "target_paths": "docs/Implementation_Status.md",
        },
    )

    assert response.status_code == 200
    assert workflow.received_request == {
        "user_request": (
            "Update the implementation status for Phase 8."
        ),
        "target_paths": ("docs/Implementation_Status.md",),
        "workflow_id": None,
    }

    assert "Review the proposed documentation changes." in response.text
    assert "Proposed Documentation Changes" in response.text
    assert "docs/Implementation_Status.md" in response.text
    assert "Preliminary Validation" in response.text
    assert "passed with warnings" in response.text.lower()
    assert "DocumentationConsistencyValidator" in response.text
    assert "Confirm that related Phase 8 documentation" in response.text
    assert "Status: Ready to Begin" in response.text
    assert "Status: In Progress" in response.text
    assert 'value="approve"' in response.text
    assert 'value="revise"' in response.text
    assert 'value="reject"' in response.text
    assert 'value="skip"' in response.text


def test_approved_documentation_change_completes_workflow() -> None:
    """Approving a proposal should show completion and final validation."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-integration-1",
            "proposal_id": "proposal-integration-1",
            "decision": "approve",
            "feedback": "The proposed status update is correct.",
        },
    )

    assert response.status_code == 200
    assert workflow.received_review is not None
    received_workflow_id, received_review = workflow.received_review
    assert received_workflow_id == "workflow-integration-1"
    assert received_review.proposal_id == "proposal-integration-1"
    assert received_review.decision is ReviewDecision.APPROVE
    assert received_review.feedback == (
        "The proposed status update is correct."
    )
    assert received_review.reviewed_at.tzinfo is not None

    assert (
        "The documentation workflow completed successfully."
        in response.text
    )
    assert "Final Validation" in response.text
    assert "All final validation checks passed." in response.text
    assert "Workflow Summary" in response.text
    assert "Approved" in response.text
    assert "Applied" in response.text
    assert "The proposed status update is correct." in response.text


def test_invalid_review_decision_renders_error_state() -> None:
    """An unsupported browser review decision should render safely."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-integration-1",
            "proposal_id": "proposal-integration-1",
            "decision": "unsupported",
            "feedback": "",
        },
    )

    assert response.status_code == 200
    assert workflow.received_review is None
    assert "The review decision could not be processed." in response.text
    assert "Unsupported review decision: unsupported" in response.text
