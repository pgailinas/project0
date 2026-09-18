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
    _create_research_processing_page,
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
        max_results: int = 10,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> ResearchAgentPageView:
        """Record request values and return the configured page."""

        self.received_request = {
            "question": question,
            "guidance": guidance,
            "max_results": max_results,
            "context_source_name": context_source_name,
            "context_content": context_content,
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
                <p id="system-active-agent">{{ active_agent_name }}</p>
                <p id="system-state">{{ system_state }}</p>
                <p id="system-operation">{{ system_operation or "" }}</p>
                <p id="system-elapsed">{{ elapsed_time or "" }}</p>
                <p id="question">{{ page.request_form.question }}</p>
                <p id="guidance">{{ page.request_form.guidance }}</p>
                <p id="context-source-name">{{ page.request_form.context_source_name or "" }}</p>
                <p id="max-results">{{ page.request_form.max_results }}</p>
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


def test_research_system_status_maps_processing_state() -> None:
    """Processing pages expose active Research Agent system status."""

    page = _build_page(
        ResearchAgentPageStatus.PROCESSING,
        "Processing.",
    )

    from project0.agents.research.research_agent_routes import (
        _research_system_status,
    )

    assert _research_system_status(
        page,
        elapsed_time="01:23",
    ) == {
        "active_agent_name": "Research Agent",
        "system_state": "Running",
        "system_operation": "Research",
        "elapsed_time": "01:23",
    }


def test_processing_page_preserves_submitted_form_values() -> None:
    """Processing state should retain normalized submitted values."""

    page = _create_research_processing_page(
        question="  Preserve this question.  ",
        guidance="  Preserve this guidance.  ",
        max_results=15,
        context_source_name="context.md",
    )

    assert page.page_status is ResearchAgentPageStatus.PROCESSING
    assert page.request_form == ResearchRequestForm(
        question="Preserve this question.",
        guidance="Preserve this guidance.",
        max_results=15,
        context_source_name="context.md",
    )


def test_research_system_status_maps_failed_state() -> None:
    """Failed pages retain elapsed time without a misleading operation."""

    page = _build_page(
        ResearchAgentPageStatus.FAILED,
        "Failed.",
    )

    from project0.agents.research.research_agent_routes import (
        _research_system_status,
    )

    assert _research_system_status(
        page,
        elapsed_time="00:17",
    ) == {
        "active_agent_name": "Research Agent",
        "system_state": "Failed",
        "system_operation": None,
        "elapsed_time": "00:17",
    }


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
    assert '<p id="system-active-agent">Research Agent</p>' in response.text
    assert '<p id="system-state">Ready</p>' in response.text
    assert '<p id="system-operation"></p>' in response.text
    assert '<p id="system-elapsed"></p>' in response.text
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
            "max_results": "5",
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
        "max_results": 5,
        "context_source_name": None,
        "context_content": None,
    }
    assert "The research workflow completed successfully." in response.text
    assert '<p id="status">completed</p>' in response.text
    assert '<p id="request-id">research-request</p>' in response.text
    assert '<p id="system-active-agent">Research Agent</p>' in response.text
    assert '<p id="system-state">Completed</p>' in response.text
    assert '<p id="system-operation">Complete</p>' in response.text
    assert '<p id="system-elapsed">00:00</p>' in response.text


def test_submit_request_route_uses_threadpool_without_changing_delegation(
    tmp_path: Path,
) -> None:
    """Thread-pool execution should preserve request delegation behavior."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/research/request",
        data={
            "question": "Find relevant research.",
            "guidance": "Prefer recent research.",
            "max_results": "15",
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "question": "Find relevant research.",
        "guidance": "Prefer recent research.",
        "max_results": 15,
        "context_source_name": None,
        "context_content": None,
    }
    assert '<p id="status">completed</p>' in response.text


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
        "max_results": 10,
        "context_source_name": None,
        "context_content": None,
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
        "max_results": 10,
        "context_source_name": None,
        "context_content": None,
    }



def test_submit_request_route_delegates_context_document(
    tmp_path: Path,
) -> None:
    """The request route should delegate uploaded context filename and bytes."""

    client, service = _build_client(tmp_path)

    response = client.post(
        "/agents/research/request",
        data={
            "question": "What should I investigate next?",
            "guidance": "",
        },
        files={
            "context_document": (
                "existing-research.md",
                b"# Existing Research\nPrior findings.",
                "text/markdown",
            ),
        },
    )

    assert response.status_code == 200
    assert service.received_request == {
        "question": "What should I investigate next?",
        "guidance": "",
        "max_results": 10,
        "context_source_name": "existing-research.md",
        "context_content": b"# Existing Research\nPrior findings.",
    }


def test_research_agent_progress_route_returns_live_stage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Progress route should expose the latest live workflow stage."""

    monkeypatch.setattr(
        "project0.agents.research.research_agent_routes."
        "get_research_workflow_progress",
        lambda: {
            "stage": "metadata",
            "state": "running",
            "request_id": "research-request",
        },
    )

    client, _ = _build_client(tmp_path)

    response = client.get("/agents/research/progress")

    assert response.status_code == 200
    assert response.json() == {
        "stage": "metadata",
        "state": "running",
        "request_id": "research-request",
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
    assert "research_agent_progress" in route_names
    assert "research_agent_submit_request" in route_names
