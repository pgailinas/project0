# ============================================================
# Project0 - Dashboard Framework Integration Tests
#
# File: test_dashboard_flow.py
#
# Purpose:
#     Verify the complete Project0 Dashboard Framework flow
#     using the real application factory and dashboard routes.
#
# ============================================================

from pathlib import Path

from fastapi.testclient import TestClient

from project0.dashboard.dashboard_app import create_dashboard_app


def _write_dashboard_templates(
    dashboard_root: Path,
) -> None:
    """Create isolated templates for Dashboard integration tests."""

    templates_directory = dashboard_root / "templates"
    templates_directory.mkdir(parents=True)

    (
        templates_directory / "dashboard.html"
    ).write_text(
        (
            "<!DOCTYPE html>"
            "<html lang=\"en\">"
            "<body>"
            "<aside>"
            "<a href=\"/\">Project Overview</a>"
            "<a href=\"/documentation\">Documentation</a>"
            "{% for agent in agents %}"
            "<a href=\"/agents/{{ agent.identifier }}\">"
            "{{ agent.name }}"
            "</a>"
            "{% endfor %}"
            "</aside>"
            "{% block breadcrumb %}{% endblock %}"
            "{% block context_toolbar %}{% endblock %}"
            "<main>{% block work_area %}{% endblock %}</main>"
            "</body>"
            "</html>"
        ),
        encoding="utf-8",
    )

    (
        templates_directory / "dashboard_home.html"
    ).write_text(
        (
            "{% extends \"dashboard.html\" %}"
            "{% block work_area %}"
            "<h1>Project Overview</h1>"
            "<p>{{ project_name }}</p>"
            "<p id=\"project-root\">{{ project_root }}</p>"
            "<p>{{ repository_name }}</p>"
            "<p>{{ git_branch }}</p>"
            "<p>{{ current_phase }}</p>"
            "<p>{{ documentation_count }}</p>"
            "<p>{{ test_status }}</p>"
            "<p>{{ validation_status }}</p>"
            "<p>{{ git_status }}</p>"
            "<p>{{ llm_status }}</p>"
            "<p>{{ workflow_status }}</p>"
            "<a href=\"{{ documentation_url }}\">Documentation</a>"
            "{% endblock %}"
        ),
        encoding="utf-8",
    )

    (
        templates_directory / "agent_placeholder.html"
    ).write_text(
        (
            "{% extends \"dashboard.html\" %}"
            "{% block work_area %}"
            "<h1>{{ agent_name }}</h1>"
            "<p>{{ agent_identifier }}</p>"
            "<p>{{ active_page }}</p>"
            "{% endblock %}"
        ),
        encoding="utf-8",
    )


def _create_integration_client(
    tmp_path: Path,
    monkeypatch,
) -> tuple[TestClient, Path]:
    """Create the real Dashboard application with test resources."""

    project_root = tmp_path / "project0"
    project_root.mkdir()

    dashboard_root = tmp_path / "dashboard"
    _write_dashboard_templates(dashboard_root)

    monkeypatch.setattr(
        "project0.dashboard.dashboard_app.__file__",
        str(dashboard_root / "dashboard_app.py"),
    )

    application = create_dashboard_app(
        project_root=project_root
    )

    return TestClient(application), project_root


def test_dashboard_home_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard home loads through the real application."""

    client, project_root = _create_integration_client(
        tmp_path,
        monkeypatch,
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Project Overview" in response.text
    assert "Project0" in response.text
    assert str(project_root) in response.text
    assert "Phase 7 – Dashboard Framework" in response.text
    assert "All tests passing" in response.text
    assert "Documentation Agent" in response.text
    assert "Research Agent" in response.text


def test_dashboard_documentation_navigation_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard documentation navigation redirects to MkDocs."""

    client, _ = _create_integration_client(
        tmp_path,
        monkeypatch,
    )

    home_response = client.get("/")

    assert 'href="/documentation"' in home_response.text

    redirect_response = client.get(
        "/documentation",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == (
        "http://127.0.0.1:8000"
    )


def test_dashboard_agent_navigation_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard agent links open shared placeholder pages."""

    client, _ = _create_integration_client(
        tmp_path,
        monkeypatch,
    )

    home_response = client.get("/")

    assert 'href="/agents/documentation"' in home_response.text
    assert 'href="/agents/research"' in home_response.text

    documentation_response = client.get(
        "/agents/documentation"
    )
    research_response = client.get("/agents/research")

    assert documentation_response.status_code == 200
    assert "Documentation Agent" in documentation_response.text
    assert "Project Overview" in documentation_response.text
    assert "Phase 7 – Dashboard Framework" not in (
        documentation_response.text
    )
    assert "All tests passing" not in documentation_response.text

    assert research_response.status_code == 200
    assert "Research Agent" in research_response.text
    assert "Project Overview" in research_response.text
    assert "Phase 7 – Dashboard Framework" not in (
        research_response.text
    )
    assert "All tests passing" not in research_response.text


def test_dashboard_status_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard status is available through the real app."""

    client, project_root = _create_integration_client(
        tmp_path,
        monkeypatch,
    )

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "application": "Project0 Dashboard",
        "status": "available",
        "project_root": str(project_root),
    }


def test_dashboard_openapi_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Dashboard routes appear in the generated OpenAPI schema."""

    client, _ = _create_integration_client(
        tmp_path,
        monkeypatch,
    )

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/" in paths
    assert "/documentation" in paths
    assert "/agents/{agent_identifier}" in paths
    assert "/api/status" in paths


def test_dashboard_unknown_route_flow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Unknown Dashboard routes return a structured 404 response."""

    client, _ = _create_integration_client(
        tmp_path,
        monkeypatch,
    )

    response = client.get("/not-a-dashboard-route")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Not Found",
    }

