# ============================================================
# Project0 - Dashboard Framework Tests
#
# File: test_dashboard_routes.py
#
# Purpose:
#     Verify platform-level Project0 Dashboard routes without
#     testing agent-specific user interface behavior.
#
# ============================================================

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from project0.dashboard.dashboard_routes import (
    build_dashboard_shell_context,
    create_dashboard_router,
)


def _create_test_client(
    tmp_path: Path,
) -> tuple[TestClient, Path]:
    """Create a dashboard test client with isolated templates."""

    project_root = tmp_path / "project0"
    project_root.mkdir()

    dashboard_root = tmp_path / "dashboard"
    templates_directory = dashboard_root / "templates"
    templates_directory.mkdir(parents=True)

    (
        templates_directory / "dashboard.html"
    ).write_text(
        """
        <!DOCTYPE html>
        <html lang="en">
        <body>
            <aside>
                {% for agent in agents %}
                    <a href="/agents/{{ agent.identifier }}">
                        {{ agent.name }}
                        {% if agent.available %}
                            <span>{{ agent.identifier }}-available</span>
                        {% else %}
                            <span>{{ agent.identifier }}-planned</span>
                        {% endif %}
                    </a>
                {% endfor %}

                <a href="/">Project Overview</a>
                <a href="/documentation">Documentation</a>
            </aside>

            <main>
                {% block work_area %}{% endblock %}
            </main>
        </body>
        </html>
        """,
        encoding="utf-8",
    )

    (
        templates_directory / "dashboard_home.html"
    ).write_text(
        """
        {% extends "dashboard.html" %}

        {% block work_area %}
            <h1>Project Overview</h1>
            <p>{{ project_name }}</p>
            <p>{{ project_root }}</p>
            <p>{{ active_page }}</p>
            <p>{{ platform_version }}</p>
            <p>{{ repository_name }}</p>
            <p>{{ git_branch }}</p>
            <p>{{ current_phase }}</p>
            <p>{{ documentation_count }}</p>
            <p>{{ test_status }}</p>
            <p>{{ validation_status }}</p>
            <p>{{ git_status }}</p>
            <p>{{ llm_status }}</p>
            <p>{{ workflow_status }}</p>
        {% endblock %}
        """,
        encoding="utf-8",
    )

    (
        templates_directory / "agent_placeholder.html"
    ).write_text(
        """
        {% extends "dashboard.html" %}

        {% block work_area %}
            <h1>{{ agent_name }}</h1>
            <p>{{ agent_identifier }}</p>
            <p>{{ active_page }}</p>
        {% endblock %}
        """,
        encoding="utf-8",
    )

    application = FastAPI()
    application.include_router(
        create_dashboard_router(
            project_root=project_root,
            dashboard_root=dashboard_root,
        )
    )

    return TestClient(application), project_root


def test_dashboard_shell_context_owns_agent_navigation() -> None:
    """Dashboard shell context provides shared agent navigation."""

    request = object()

    context = build_dashboard_shell_context(
        request=request,
        active_page="agent:documentation",
    )

    assert context["request"] is request
    assert context["project_name"] == "Project0"
    assert context["active_page"] == "agent:documentation"
    assert context["agents"] == (
        {
            "identifier": "documentation",
            "name": "Documentation Agent",
            "available": True,
        },
        {
            "identifier": "research",
            "name": "Research Agent",
            "available": False,
        },
    )


def test_dashboard_home_returns_success(
    tmp_path: Path,
) -> None:
    """Dashboard home route returns a successful HTML response."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/html"
    )


def test_dashboard_home_displays_project_information(
    tmp_path: Path,
) -> None:
    """Dashboard home includes project and repository information."""

    client, project_root = _create_test_client(tmp_path)

    response = client.get("/")

    assert "Project0" in response.text
    assert "project0" in response.text
    assert str(project_root) in response.text
    assert "0.1.0" in response.text


def test_dashboard_home_displays_project_status_in_work_area(
    tmp_path: Path,
) -> None:
    """Project Overview renders Project0 status in the Work Area."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/")

    assert "Project Overview" in response.text
    assert "Unknown" in response.text
    assert "Phase 8 – Documentation Agent User Interface" in response.text
    assert "All tests passing" in response.text
    assert "Not run" in response.text
    assert "Not configured" in response.text
    assert "Idle" in response.text
    assert "dashboard" in response.text


def test_dashboard_home_displays_registered_agents(
    tmp_path: Path,
) -> None:
    """Dashboard home lists platform-level agent entries."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/")

    assert "Documentation Agent" in response.text
    assert "Research Agent" in response.text
    assert 'href="/agents/documentation"' in response.text
    assert 'href="/agents/research"' in response.text


def test_dashboard_home_displays_agent_availability(
    tmp_path: Path,
) -> None:
    """Implemented and planned agents expose distinct availability states."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/")

    assert "documentation-available" in response.text
    assert "documentation-planned" not in response.text
    assert "research-planned" in response.text


def test_documentation_route_redirects_to_local_mkdocs(
    tmp_path: Path,
) -> None:
    """Documentation route redirects to the local MkDocs site."""

    client, _ = _create_test_client(tmp_path)

    response = client.get(
        "/documentation",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == (
        "http://127.0.0.1:8000"
    )


def test_documentation_agent_fallback_route_renders_placeholder(
    tmp_path: Path,
) -> None:
    """
    The platform router retains a fallback when the agent UI is not registered.

    The complete Dashboard application registers the Documentation Agent
    router before this generic fallback during Phase 8.
    """

    client, _ = _create_test_client(tmp_path)

    response = client.get("/agents/documentation")

    assert response.status_code == 200
    assert "Documentation Agent" in response.text
    assert "documentation" in response.text
    assert "agent:documentation" in response.text
    assert "Project Overview" in response.text
    assert (
        "Phase 8 – Documentation Agent User Interface"
        not in response.text
    )
    assert "All tests passing" not in response.text


def test_research_agent_route_renders_placeholder(
    tmp_path: Path,
) -> None:
    """Research Agent uses the shared placeholder route."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/agents/research")

    assert response.status_code == 200
    assert "Research Agent" in response.text
    assert "research" in response.text
    assert "agent:research" in response.text


def test_unknown_agent_name_is_formatted(
    tmp_path: Path,
) -> None:
    """Unknown agent identifiers receive a readable display name."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/agents/code-review")

    assert response.status_code == 200
    assert "Code Review" in response.text
    assert "code-review" in response.text
    assert "agent:code-review" in response.text


def test_agent_identifier_is_normalized(
    tmp_path: Path,
) -> None:
    """Agent identifiers are normalized to lowercase."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/agents/DOCUMENTATION")

    assert response.status_code == 200
    assert "Documentation Agent" in response.text
    assert "documentation" in response.text
    assert "agent:documentation" in response.text


def test_dashboard_status_returns_expected_json(
    tmp_path: Path,
) -> None:
    """Status endpoint returns basic dashboard information."""

    client, project_root = _create_test_client(tmp_path)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "application": "Project0 Dashboard",
        "status": "available",
        "project_root": str(project_root),
    }


def test_unknown_route_returns_not_found(
    tmp_path: Path,
) -> None:
    """Unregistered dashboard routes return HTTP 404."""

    client, _ = _create_test_client(tmp_path)

    response = client.get("/unknown")

    assert response.status_code == 404
