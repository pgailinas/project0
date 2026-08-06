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

from fastapi import FastAPI
from starlette.routing import Mount

from project0.dashboard.dashboard_app import create_dashboard_app


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
