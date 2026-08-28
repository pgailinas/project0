# ============================================================
# Project0 - Documentation Agent Route Tests
#
# File: test_documentation_agent_routes.py
#
# Purpose:
#     Verify Documentation Agent HTTP routes, form parsing,
#     service delegation, and rendered template context.
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
    DOCUMENTATION_AGENT_ROUTE_PREFIX,
    DOCUMENTATION_AGENT_TEMPLATE_NAME,
    _parse_target_paths,
    create_documentation_agent_router,
)
from project0.agents.documentation.documentation_agent_view_models import (
    DocumentationAgentPageStatus,
    DocumentationAgentPageView,
    DocumentationRequestForm,
)
from project0.models.documentation_workflow_models import ReviewDecision


@dataclass
class FakeDocumentationAgentUIService:
    """Simple UI service fake used by route tests."""

    ready_page: DocumentationAgentPageView
    request_page: DocumentationAgentPageView
    review_page: DocumentationAgentPageView
    received_request: dict[str, Any] | None = None
    received_review: dict[str, Any] | None = None

    def create_ready_page(self) -> DocumentationAgentPageView:
        """Return the configured initial page."""

        return self.ready_page

    def submit_request(
        self,
        user_request: str,
        target_paths: tuple[str, ...],
    ) -> DocumentationAgentPageView:
        """Record request values and return the configured page."""

        self.received_request = {
            "user_request": user_request,
            "target_paths": target_paths,
        }
        return self.request_page

    def submit_review_decision(
        self,
        workflow_id: str,
        proposal_id: str,
        decision: ReviewDecision,
        feedback: str | None = None,
    ) -> DocumentationAgentPageView:
        """Record review values and return the configured page."""

        self.received_review = {
            "workflow_id": workflow_id,
            "proposal_id": proposal_id,
            "decision": decision,
            "feedback": feedback,
        }
        return self.review_page


def _build_page(
    status: DocumentationAgentPageStatus,
    message: str,
    workflow_id: str | None = None,
) -> DocumentationAgentPageView:
    """Create a minimal page model for route tests."""

    return DocumentationAgentPageView(
        page_status=status,
        status_message=message,
        request_form=DocumentationRequestForm(),
        workflow_id=workflow_id,
    )


def _build_templates(tmp_path: Path) -> Jinja2Templates:
    """Create a minimal template environment for route tests."""

    template_path = tmp_path / DOCUMENTATION_AGENT_TEMPLATE_NAME
    template_path.write_text(
        """
        <html>
            <body>
                <h1>{{ page.status_message }}</h1>
                <p id="status">{{ page.page_status.value }}</p>
                <p id="active-navigation">{{ active_navigation }}</p>
                <p id="active-page">{{ active_page }}</p>
                <p id="project-name">{{ project_name }}</p>
                {% for agent in agents %}
                <p class="dashboard-agent">
                    {{ agent.name }}:{{ agent.available }}
                </p>
                {% endfor %}
                {% if page.workflow_id %}
                <p id="workflow-id">{{ page.workflow_id }}</p>
                {% endif %}
                {% if page.error_message %}
                <p id="error-message">{{ page.error_message }}</p>
                {% endif %}
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    return Jinja2Templates(directory=str(tmp_path))


def _build_client(
    tmp_path: Path,
) -> tuple[TestClient, FakeDocumentationAgentUIService]:
    """Build a FastAPI test client with a fake UI service."""

    service = FakeDocumentationAgentUIService(
        ready_page=_build_page(
            DocumentationAgentPageStatus.READY,
            "Ready for a documentation request.",
        ),
        request_page=_build_page(
            DocumentationAgentPageStatus.REVIEW_REQUIRED,
            "Review the proposed documentation changes.",
            workflow_id="workflow-request",
        ),
        review_page=_build_page(
            DocumentationAgentPageStatus.COMPLETED,
            "The documentation workflow completed successfully.",
            workflow_id="workflow-review",
        ),
    )

    app = FastAPI()
    app.include_router(
        create_documentation_agent_router(
            ui_service=service,
            templates=_build_templates(tmp_path),
        )
    )

    return TestClient(app), service


def test_route_constants() -> None:
    """Route constants should remain stable for templates and registration."""

    assert DOCUMENTATION_AGENT_ROUTE_PREFIX == "/agents/documentation"
    assert DOCUMENTATION_AGENT_TEMPLATE_NAME == (
        "documentation_agent_home.html"
    )


def test_parse_target_paths() -> None:
    """Target paths should be split, stripped, and filtered."""

    result = _parse_target_paths(
        """
        docs/Implementation_Status.md

          docs/Dashboard_Design.md
        """
    )

    assert result == (
        "docs/Implementation_Status.md",
        "docs/Dashboard_Design.md",
    )


def test_documentation_agent_home_route(tmp_path: Path) -> None:
    """The home route should render the initial page state."""

    client, service = _build_client(tmp_path)

    response = client.get("/agents/documentation")

    assert response.status_code == 200
    assert "Ready for a documentation request." in response.text
    assert '<p id="status">ready</p>' in response.text
    assert (
        '<p id="active-navigation">documentation-agent</p>'
        in response.text
    )
    assert '<p id="active-page">agent:documentation</p>' in response.text
    assert '<p id="project-name">Project0</p>' in response.text
    assert "Documentation Agent:True" in response.text
    assert "Research Agent:True" in response.text
    assert service.received_request is None
    assert service.received_review is None


def test_submit_request_route_delegates_form_values(
    tmp_path: Path,
) -> None:
    """The request route should parse paths and delegate to the UI service."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/request",
        data={
            "user_request": "Update the implementation status.",
            "target_paths": (
                "docs/Implementation_Status.md\n"
                "\n"
                " docs/Dashboard_Design.md "
            ),
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "user_request": "Update the implementation status.",
        "target_paths": (
            "docs/Implementation_Status.md",
            "docs/Dashboard_Design.md",
        ),
    }
    assert "Review the proposed documentation changes." in response.text
    assert '<p id="status">review_required</p>' in response.text
    assert '<p id="workflow-id">workflow-request</p>' in response.text


def test_submit_request_route_uses_threadpool_without_changing_delegation(
    tmp_path: Path,
) -> None:
    """Thread-pool execution should preserve request delegation behavior."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/request",
        data={
            "user_request": "Update the documentation.",
            "target_paths": "docs/Implementation_Status.md",
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "user_request": "Update the documentation.",
        "target_paths": ("docs/Implementation_Status.md",),
    }
    assert '<p id="status">review_required</p>' in response.text


def test_submit_request_route_accepts_empty_optional_paths(
    tmp_path: Path,
) -> None:
    """The request route should pass an empty tuple for omitted paths."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/request",
        data={
            "user_request": "Update the documentation.",
            "target_paths": "",
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "user_request": "Update the documentation.",
        "target_paths": (),
    }


def test_submit_review_route_delegates_valid_decision(
    tmp_path: Path,
) -> None:
    """The review route should convert and forward valid decisions."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-1",
            "proposal_id": "proposal-1",
            "decision": "approve",
            "feedback": "Looks correct.",
        },
    )

    assert response.status_code == 200
    assert service.received_review == {
        "workflow_id": "workflow-1",
        "proposal_id": "proposal-1",
        "decision": ReviewDecision.APPROVE,
        "feedback": "Looks correct.",
    }
    assert (
        "The documentation workflow completed successfully."
        in response.text
    )
    assert '<p id="status">completed</p>' in response.text
    assert '<p id="workflow-id">workflow-review</p>' in response.text


def test_submit_review_route_uses_threadpool_without_changing_delegation(
    tmp_path: Path,
) -> None:
    """Thread-pool execution should preserve review delegation behavior."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-4",
            "proposal_id": "proposal-4",
            "decision": "approve",
            "feedback": "Approved.",
        },
    )

    assert response.status_code == 200
    assert service.received_review == {
        "workflow_id": "workflow-4",
        "proposal_id": "proposal-4",
        "decision": ReviewDecision.APPROVE,
        "feedback": "Approved.",
    }
    assert '<p id="status">completed</p>' in response.text


def test_submit_review_route_forwards_blank_feedback(
    tmp_path: Path,
) -> None:
    """Blank feedback should be forwarded for UI-service normalization."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-2",
            "proposal_id": "proposal-2",
            "decision": "skip",
            "feedback": "",
        },
    )

    assert response.status_code == 200
    assert service.received_review == {
        "workflow_id": "workflow-2",
        "proposal_id": "proposal-2",
        "decision": ReviewDecision.SKIP,
        "feedback": "",
    }


def test_submit_review_route_rejects_unknown_decision(
    tmp_path: Path,
) -> None:
    """Unsupported decisions should render a failure page."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-3",
            "proposal_id": "proposal-3",
            "decision": "invalid",
            "feedback": "Unsupported choice.",
        },
    )

    assert response.status_code == 200
    assert service.received_review is None
    assert (
        "The review decision could not be processed."
        in response.text
    )
    assert '<p id="status">failed</p>' in response.text
    assert '<p id="workflow-id">workflow-3</p>' in response.text
    assert (
        '<p id="error-message">'
        "Unsupported review decision: invalid"
        "</p>"
        in response.text
    )


def test_submit_review_route_requires_workflow_id(
    tmp_path: Path,
) -> None:
    """Missing workflow IDs should produce FastAPI form validation errors."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "proposal_id": "proposal-1",
            "decision": "approve",
        },
    )

    assert response.status_code == 422
    assert service.received_review is None


def test_submit_review_route_requires_proposal_id(
    tmp_path: Path,
) -> None:
    """Missing proposal IDs should produce FastAPI form validation errors."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-1",
            "decision": "approve",
        },
    )

    assert response.status_code == 422
    assert service.received_review is None


def test_submit_review_route_requires_decision(
    tmp_path: Path,
) -> None:
    """Missing decisions should produce FastAPI form validation errors."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/documentation/review",
        data={
            "workflow_id": "workflow-1",
            "proposal_id": "proposal-1",
        },
    )

    assert response.status_code == 422
    assert service.received_review is None


def test_router_exposes_expected_named_routes(tmp_path: Path) -> None:
    """The router should expose stable names for URL generation."""

    service = FakeDocumentationAgentUIService(
        ready_page=_build_page(
            DocumentationAgentPageStatus.READY,
            "Ready.",
        ),
        request_page=_build_page(
            DocumentationAgentPageStatus.PROCESSING,
            "Processing.",
        ),
        review_page=_build_page(
            DocumentationAgentPageStatus.COMPLETED,
            "Completed.",
        ),
    )

    router = create_documentation_agent_router(
        ui_service=service,
        templates=_build_templates(tmp_path),
    )

    route_names = {route.name for route in router.routes}

    assert "documentation_agent_home" in route_names
    assert "documentation_agent_submit_request" in route_names
    assert "documentation_agent_submit_review" in route_names
