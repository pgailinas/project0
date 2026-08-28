# ============================================================
# Project0 - Dashboard Framework Tests
#
# File: test_dashboard_app.py
#
# Purpose:
#     Verify construction and configuration of the Project0
#     browser-based Dashboard application.
#
# ============================================================

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Mount

from project0.agents.documentation.documentation_agent_ui_service import (
    DocumentationAgentUIService,
)
from project0.dashboard.dashboard_app import (
    _create_reasoning_provider,
    create_dashboard_app,
    create_project0_dashboard_app,
)
from project0.reasoning.providers.ollama_provider import (
    OllamaReasoningProvider,
)
from project0.reasoning.providers.stub_provider import (
    StubReasoningProvider,
)


class FakeDocumentationWorkflow:
    """Minimal workflow fake used for Dashboard registration tests."""

    def run_documentation_workflow(
        self,
        user_request: str,
        target_paths: tuple[str, ...] = (),
        workflow_id: str | None = None,
    ) -> object:
        """Return an incomplete workflow result."""

        del user_request, target_paths, workflow_id

        return {
            "workflow_id": "workflow-dashboard-test",
            "status": "running",
        }

    def submit_documentation_review(
        self,
        workflow_id: str,
        review: object,
    ) -> object:
        """Return an incomplete workflow result after review."""

        del workflow_id, review

        return {
            "workflow_id": "workflow-dashboard-test",
            "status": "running",
        }


def _create_documentation_agent_ui_service() -> (
    DocumentationAgentUIService
):
    """Create a Documentation Agent UI service for application tests."""

    return DocumentationAgentUIService(
        workflow=FakeDocumentationWorkflow()
    )


def test_create_dashboard_app_returns_fastapi_application(
    tmp_path: Path,
) -> None:
    """Dashboard application factory returns a FastAPI instance."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    assert isinstance(application, FastAPI)


def test_dashboard_application_metadata(tmp_path: Path) -> None:
    """Dashboard application exposes the expected metadata."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    assert application.title == "Project0 Dashboard"
    assert application.version == "0.1.0"
    assert application.description == (
        "Browser-based interface for Project0 platform services "
        "and registered AI agents."
    )
    assert application.docs_url == "/api/docs"
    assert application.redoc_url is None


def test_dashboard_application_stores_resolved_project_root(
    tmp_path: Path,
) -> None:
    """Dashboard state stores the resolved project root."""

    project_root = tmp_path / "project0"
    project_root.mkdir()

    application = create_dashboard_app(
        project_root=project_root
    )

    assert application.state.project_root == (
        project_root.resolve()
    )


def test_dashboard_application_defaults_to_current_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard state defaults to the current working directory."""

    monkeypatch.chdir(tmp_path)

    application = create_dashboard_app()

    assert application.state.project_root == tmp_path.resolve()


def test_dashboard_application_stores_dashboard_root(
    tmp_path: Path,
) -> None:
    """Dashboard state stores the package dashboard directory."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    dashboard_root = application.state.dashboard_root

    assert isinstance(dashboard_root, Path)
    assert dashboard_root.name == "dashboard"
    assert dashboard_root.is_absolute()


def test_dashboard_routes_are_registered(
    tmp_path: Path,
) -> None:
    """Dashboard application registers platform-level routes."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    route_paths = set(application.openapi()["paths"])

    assert "/" in route_paths
    assert "/documentation" in route_paths
    assert "/agents/{agent_identifier}" in route_paths
    assert "/api/status" in route_paths


def test_dashboard_api_documentation_route_is_registered(
    tmp_path: Path,
) -> None:
    """FastAPI documentation uses the configured route."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    assert application.docs_url == "/api/docs"
    assert application.openapi_url == "/openapi.json"
    assert application.redoc_url is None


def test_css_directory_is_mounted_when_present(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard CSS is mounted when the CSS directory exists."""

    dashboard_root = tmp_path / "dashboard"
    css_directory = dashboard_root / "css"
    css_directory.mkdir(parents=True)

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.__file__",
        str(dashboard_root / "dashboard_app.py"),
    )

    application = create_dashboard_app(
        project_root=tmp_path
    )

    mount_paths = {
        route.path
        for route in application.routes
        if isinstance(route, Mount)
    }

    assert "/css" in mount_paths


def test_css_directory_is_not_mounted_when_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard CSS remains optional when its directory is absent."""

    dashboard_root = tmp_path / "dashboard"
    dashboard_root.mkdir()

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.__file__",
        str(dashboard_root / "dashboard_app.py"),
    )

    application = create_dashboard_app(
        project_root=tmp_path
    )

    mount_paths = {
        route.path
        for route in application.routes
        if isinstance(route, Mount)
    }

    assert "/css" not in mount_paths


def test_dashboard_applications_are_independent(
    tmp_path: Path,
) -> None:
    """Each factory call creates a separate application instance."""

    first_application = create_dashboard_app(
        project_root=tmp_path / "first"
    )
    second_application = create_dashboard_app(
        project_root=tmp_path / "second"
    )

    assert first_application is not second_application
    assert (
        first_application.state.project_root
        != second_application.state.project_root
    )


def test_documentation_agent_routes_are_not_registered_by_default(
    tmp_path: Path,
) -> None:
    """Agent-specific routes remain optional without a UI service."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    route_paths = set(application.openapi()["paths"])

    assert "/agents/documentation/request" not in route_paths
    assert "/agents/documentation/review" not in route_paths
    assert not hasattr(
        application.state,
        "documentation_agent_ui_service",
    )


def test_documentation_agent_routes_are_registered_when_configured(
    tmp_path: Path,
) -> None:
    """Configured Documentation Agent services register Phase 8 routes."""

    ui_service = _create_documentation_agent_ui_service()

    application = create_dashboard_app(
        project_root=tmp_path,
        documentation_agent_ui_service=ui_service,
    )

    route_paths = set(application.openapi()["paths"])

    assert "/agents/documentation" in route_paths
    assert "/agents/documentation/request" in route_paths
    assert "/agents/documentation/review" in route_paths


def test_documentation_agent_service_is_stored_in_application_state(
    tmp_path: Path,
) -> None:
    """Configured Documentation Agent services are available in app state."""

    ui_service = _create_documentation_agent_ui_service()

    application = create_dashboard_app(
        project_root=tmp_path,
        documentation_agent_ui_service=ui_service,
    )

    assert (
        application.state.documentation_agent_ui_service
        is ui_service
    )


def test_documentation_agent_root_is_stored_in_application_state(
    tmp_path: Path,
) -> None:
    """Configured Documentation Agent package root is stored in app state."""

    application = create_dashboard_app(
        project_root=tmp_path,
        documentation_agent_ui_service=(
            _create_documentation_agent_ui_service()
        ),
    )

    documentation_agent_root = (
        application.state.documentation_agent_root
    )

    assert isinstance(documentation_agent_root, Path)
    assert documentation_agent_root.name == "documentation"
    assert documentation_agent_root.parent.name == "agents"
    assert documentation_agent_root.is_absolute()


def test_documentation_agent_css_is_mounted_when_configured(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Configured Documentation Agent exposes its agent-owned stylesheet."""

    dashboard_root = tmp_path / "dashboard"
    dashboard_root.mkdir()

    documentation_agent_root = (
        tmp_path / "agents" / "documentation"
    )
    documentation_agent_css_directory = (
        documentation_agent_root / "css"
    )
    documentation_agent_css_directory.mkdir(parents=True)
    (
        documentation_agent_css_directory
        / "documentation_agent.css"
    ).write_text(
        ".documentation-agent { display: grid; }\n",
        encoding="utf-8",
    )

    documentation_agent_template_directory = (
        documentation_agent_root / "templates"
    )
    documentation_agent_template_directory.mkdir(parents=True)

    dashboard_templates_directory = (
        dashboard_root / "templates"
    )
    dashboard_templates_directory.mkdir(parents=True)

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.__file__",
        str(dashboard_root / "dashboard_app.py"),
    )

    application = create_dashboard_app(
        project_root=tmp_path,
        documentation_agent_ui_service=(
            _create_documentation_agent_ui_service()
        ),
    )

    mount_paths = {
        route.path
        for route in application.routes
        if isinstance(route, Mount)
    }

    assert "/agents/documentation/css" in mount_paths

    client = TestClient(application)
    response = client.get(
        "/agents/documentation/css/documentation_agent.css"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert ".documentation-agent" in response.text


def test_documentation_agent_css_is_not_mounted_without_agent(
    tmp_path: Path,
) -> None:
    """Agent-owned CSS is absent when the Documentation Agent is not configured."""

    application = create_dashboard_app(
        project_root=tmp_path
    )

    mount_paths = {
        route.path
        for route in application.routes
        if isinstance(route, Mount)
    }

    assert "/agents/documentation/css" not in mount_paths


def test_documentation_agent_route_precedes_generic_agent_route(
    tmp_path: Path,
) -> None:
    """The specific Documentation Agent route handles its URL."""

    application = create_dashboard_app(
        project_root=tmp_path,
        documentation_agent_ui_service=(
            _create_documentation_agent_ui_service()
        ),
    )
    client = TestClient(application)

    response = client.get("/agents/documentation")

    assert response.status_code == 200
    assert "Ready for a documentation request." in response.text
    assert "agent:documentation" not in response.text



def test_create_project0_dashboard_app_configures_documentation_agent(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """The executable factory wires the Documentation Agent service."""

    dispatcher = FakeDocumentationWorkflow()

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.create_platform_dispatcher",
        lambda reasoning_provider, reasoning_model_name: dispatcher,
    )
    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.SETTINGS",
        SimpleNamespace(
            project_root=tmp_path,
            reasoning_provider="ollama",
            ollama_base_url="http://127.0.0.1:11434",
            ollama_timeout_seconds=120.0,
            ollama_model="qwen2.5:7b",
        ),
    )

    application = create_project0_dashboard_app()
    route_paths = set(application.openapi()["paths"])

    assert isinstance(application, FastAPI)
    assert application.state.project_root == tmp_path.resolve()
    assert "/agents/documentation" in route_paths
    assert "/agents/documentation/request" in route_paths
    assert "/agents/documentation/review" in route_paths
    assert isinstance(
        application.state.documentation_agent_ui_service,
        DocumentationAgentUIService,
    )
    assert (
        application.state.documentation_agent_ui_service.workflow
        is dispatcher
    )


def test_create_reasoning_provider_uses_ollama_configuration(
    monkeypatch,
) -> None:
    """The configured provider factory creates an Ollama provider."""

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.SETTINGS",
        SimpleNamespace(
            reasoning_provider="ollama",
            ollama_base_url="http://localhost:22000",
            ollama_timeout_seconds=45.0,
        ),
    )

    reasoning_provider = _create_reasoning_provider()

    assert isinstance(
        reasoning_provider,
        OllamaReasoningProvider,
    )
    assert reasoning_provider.base_url == "http://localhost:22000"
    assert reasoning_provider.timeout_seconds == 45.0


def test_create_reasoning_provider_can_use_stub(
    monkeypatch,
) -> None:
    """The configured provider factory retains the stub provider."""

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.SETTINGS",
        SimpleNamespace(
            reasoning_provider="stub",
        ),
    )

    reasoning_provider = _create_reasoning_provider()

    assert isinstance(
        reasoning_provider,
        StubReasoningProvider,
    )
    assert reasoning_provider.response.provider_name == "stub"
    assert reasoning_provider.response.model_name == "stub-model"
    assert reasoning_provider.response.structured_output == {
        "evaluations": [
            {
                "source_id": "stub-paper-001",
                "relevance_score": 95,
                "relevance_summary": (
                    "Stub research evaluation."
                ),
                "strengths": [
                    "Vision-language alignment relevance",
                ],
                "limitations": [
                    "Stub evaluation for deterministic testing",
                ],
                "research_connections": [
                    "vision-language alignment",
                ],
                "warnings": [],
            },
        ],
    }


def test_create_reasoning_provider_rejects_unsupported_provider(
    monkeypatch,
) -> None:
    """Unsupported provider configuration fails explicitly."""

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.SETTINGS",
        SimpleNamespace(
            reasoning_provider="unsupported",
        ),
    )

    try:
        _create_reasoning_provider()
    except ValueError as error:
        assert str(error) == (
            "Unsupported Project0 reasoning provider: unsupported"
        )
    else:
        raise AssertionError(
            "Unsupported reasoning provider did not raise ValueError."
        )


def test_create_project0_dashboard_app_supplies_reasoning_provider(
    monkeypatch,
) -> None:
    """The executable factory supplies the configured reasoning provider."""

    captured: dict[str, object] = {}
    dispatcher = FakeDocumentationWorkflow()

    def fake_create_platform_dispatcher(
        reasoning_provider,
        reasoning_model_name,
    ):
        captured["reasoning_provider"] = reasoning_provider
        captured["reasoning_model_name"] = reasoning_model_name
        return dispatcher

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.create_platform_dispatcher",
        fake_create_platform_dispatcher,
    )
    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.SETTINGS",
        SimpleNamespace(
            project_root=Path.cwd(),
            reasoning_provider="ollama",
            ollama_base_url="http://127.0.0.1:11434",
            ollama_timeout_seconds=120.0,
            ollama_model="qwen2.5:7b",
        ),
    )

    create_project0_dashboard_app()

    reasoning_provider = captured["reasoning_provider"]

    assert isinstance(
        reasoning_provider,
        OllamaReasoningProvider,
    )
    assert captured["reasoning_model_name"] == "qwen2.5:7b"
