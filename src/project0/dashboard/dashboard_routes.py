# ============================================================
# Project0 - Dashboard Framework
#
# File: dashboard_routes.py
#
# Purpose:
#     Define platform-level routes for the Project0 Dashboard
#     without implementing agent-specific user interfaces.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


DASHBOARD_AGENTS = (
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


def build_dashboard_shell_context(
    request: Request,
    active_page: str,
) -> dict[str, object]:
    """Build context owned by the shared Dashboard Framework shell."""

    return {
        "request": request,
        "project_name": "Project0",
        "active_page": active_page,
        "agents": DASHBOARD_AGENTS,
    }


def create_dashboard_router(
    project_root: Path,
    dashboard_root: Path,
) -> APIRouter:
    """Create the platform-level Project0 Dashboard router."""

    templates_directory = dashboard_root / "templates"

    router = APIRouter()
    templates = Jinja2Templates(
        directory=templates_directory
    )

    def build_dashboard_context(
        request: Request,
        active_page: str,
    ) -> dict[str, object]:
        """Build shared context for Dashboard Framework pages."""

        context = build_dashboard_shell_context(
            request=request,
            active_page=active_page,
        )
        context.update(
            {
                "repository_name": "project0",
                "project_root": project_root,
                "documentation_url": "/documentation",
                "git_branch": "Unknown",
                "git_status": "Unavailable",
                "git_status_class": "status-value--muted",
                "current_phase": (
                    "Phase 8 – Documentation Agent User Interface"
                ),
                "documentation_count": "Unknown",
                "test_status": "All tests passing",
                "test_status_class": "status-value--success",
                "validation_status": "Not run",
                "validation_status_class": "status-value--muted",
                "llm_status": "Not configured",
                "workflow_status": "Idle",
                "platform_version": "0.1.0",
            }
        )

        return context

    @router.get(
        "/",
        response_class=HTMLResponse,
        name="dashboard_home",
    )
    async def dashboard_home(
        request: Request,
    ) -> HTMLResponse:
        """Render the Project0 Dashboard home page."""

        context = build_dashboard_context(
            request=request,
            active_page="dashboard",
        )
        context["recent_activity"] = ()

        return templates.TemplateResponse(
            request=request,
            name="dashboard_home.html",
            context=context,
        )

    @router.get(
        "/documentation",
        response_class=RedirectResponse,
        name="dashboard_documentation",
    )
    async def dashboard_documentation() -> RedirectResponse:
        """Redirect to the locally served Project0 documentation."""

        return RedirectResponse(
            url="http://127.0.0.1:8000",
            status_code=307,
        )

    @router.get(
        "/agents/{agent_identifier}",
        response_class=HTMLResponse,
        name="dashboard_agent_placeholder",
    )
    async def dashboard_agent_placeholder(
        request: Request,
        agent_identifier: str,
    ) -> HTMLResponse:
        """
        Render a generic placeholder for an agent without a registered UI.

        Agent-specific routers should be registered before this platform-level
        fallback route so implemented agents receive their own Work Areas.
        """

        normalized_identifier = agent_identifier.strip().lower()

        agent_names = {
            "documentation": "Documentation Agent",
            "research": "Research Agent",
        }
        agent_name = agent_names.get(
            normalized_identifier,
            normalized_identifier.replace("-", " ").title(),
        )

        context = build_dashboard_context(
            request=request,
            active_page=f"agent:{normalized_identifier}",
        )
        context.update(
            {
                "agent_identifier": normalized_identifier,
                "agent_name": agent_name,
            }
        )

        return templates.TemplateResponse(
            request=request,
            name="agent_placeholder.html",
            context=context,
            status_code=200,
        )

    @router.get(
        "/api/status",
        name="dashboard_status",
    )
    async def dashboard_status() -> dict[str, object]:
        """Return basic Project0 Dashboard status information."""

        return {
            "application": "Project0 Dashboard",
            "status": "available",
            "project_root": str(project_root),
        }

    return router
