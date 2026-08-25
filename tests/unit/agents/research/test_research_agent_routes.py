# ============================================================
# Project0 - Research Agent Route Tests
#
# File: test_research_agent_routes.py
#
# Purpose:
#     Verify Research Agent HTTP routes, form parsing,
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

from project0.agents.research.research_agent_routes import (
    RESEARCH_AGENT_ROUTE_PREFIX,
    RESEARCH_AGENT_TEMPLATE_NAME,
    create_research_agent_router,
)
from project0.agents.research.research_agent_view_models import (
    ResearchAgentPageStatus,
    ResearchAgentPageView,
    ResearchRequestForm,
)


@dataclass
class FakeResearchAgentUIService:
    """Simple UI service fake used by route tests."""

    ready_page: ResearchAgentPageView
    request_page: ResearchAgentPageView
    received_request: dict[str, Any] | None = None

    def create_ready_page(self) -> ResearchAgentPageView:
        """Return the configured initial page."""

        return self.ready_page

    def submit_request(
        self,
        question: str,
        guidance: str,
    ) -> ResearchAgentPageView:
        """Record request values and return the configured page."""

        self.received_request = {
            "question": question,
            "guidance": guidance,
        }
        return self.request_page


def _build_page(
    status: ResearchAgentPageStatus,
    message: str,
    request_id: str | None = None,
) -> ResearchAgentPageView:
    """Create a minimal page model for route tests."""

    return ResearchAgentPageView(
        page_status=status,
        status_message=message,
        request_form=ResearchRequestForm(),
        request_id=request_id,
    )


def _build_templates(tmp_path: Path) -> Jinja2Templates:
    """Create a minimal template environment for route tests."""

    template_path = tmp_path / RESEARCH_AGENT_TEMPLATE_NAME
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
                {% if page.request_id %}
                <p id="request-id">{{ page.request_id }}</p>
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
) -> tuple[TestClient, FakeResearchAgentUIService]:
    """Build a FastAPI test client with a fake UI service."""

    service = FakeResearchAgentUIService(
        ready_page=_build_page(
            ResearchAgentPageStatus.READY,
            "Ready for a research request.",
        ),
        request_page=_build_page(
            ResearchAgentPageStatus.COMPLETED,
            "The research workflow completed successfully.",
            request_id="research-request",
        ),
    )

    app = FastAPI()
    app.include_router(
        create_research_agent_router(
            ui_service=service,
            templates=_build_templates(tmp_path),
        )
    )

    return TestClient(app), service


def test_route_constants() -> None:
    """Route constants should remain stable for templates and registration."""

    assert RESEARCH_AGENT_ROUTE_PREFIX == "/agents/research"
    assert RESEARCH_AGENT_TEMPLATE_NAME == (
        "research_agent_home.html"
    )


def test_research_agent_home_route(tmp_path: Path) -> None:
    """The home route should render the initial page state."""

    client, service = _build_client(tmp_path)

    response = client.get("/agents/research")

    assert response.status_code == 200
    assert "Ready for a research request." in response.text
    assert '<p id="status">ready</p>' in response.text
    assert (
        '<p id="active-navigation">research-agent</p>'
        in response.text
    )
    assert '<p id="active-page">agent:research</p>' in response.text
    assert '<p id="project-name">Project0</p>' in response.text
    assert "Documentation Agent:True" in response.text
    assert "Research Agent:True" in response.text
    assert service.received_request is None


def test_submit_request_route_delegates_form_values(
    tmp_path: Path,
) -> None:
    """The request route should parse values and delegate to the UI service."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/research/request",
        data={
            "question": "Find relevant VideoQA research.",
            "guidance": (
                "Prefer recent research. "
                "Focus on peer-reviewed work. "
                "vision-language alignment. "
                "self-supervised video representations. "
                "semantic_scholar. "
                "arxiv."
            ),
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "question": "Find relevant VideoQA research.",
        "guidance": (
            "Prefer recent research. "
            "Focus on peer-reviewed work. "
            "vision-language alignment. "
            "self-supervised video representations. "
            "semantic_scholar. "
            "arxiv."
        ),
    }
    assert "The research workflow completed successfully." in response.text
    assert '<p id="status">completed</p>' in response.text
    assert '<p id="request-id">research-request</p>' in response.text


def test_submit_request_route_accepts_empty_optional_values(
    tmp_path: Path,
) -> None:
    """The request route should pass empty tuples for omitted values."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/research/request",
        data={
            "question": "Find relevant research.",
            "guidance": "",
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "question": "Find relevant research.",
        "guidance": "",
    }


def test_submit_request_route_accepts_blank_question(
    tmp_path: Path,
) -> None:
    """Blank questions should be forwarded for UI-service validation."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/research/request",
        data={
            "question": "",
            "guidance": "",
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "question": "",
        "guidance": "",
    }


def test_router_exposes_expected_named_routes(tmp_path: Path) -> None:
    """The router should expose stable names for URL generation."""

    service = FakeResearchAgentUIService(
        ready_page=_build_page(
            ResearchAgentPageStatus.READY,
            "Ready.",
        ),
        request_page=_build_page(
            ResearchAgentPageStatus.PROCESSING,
            "Processing.",
        ),
    )

    router = create_research_agent_router(
        ui_service=service,
        templates=_build_templates(tmp_path),
    )

    route_names = {route.name for route in router.routes}

    assert "research_agent_home" in route_names
    assert "research_agent_submit_request" in route_names
