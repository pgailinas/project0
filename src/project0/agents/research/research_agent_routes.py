# ============================================================
# Project0 - Research Agent Routes
#
# File: research_agent_routes.py
#
# Purpose:
#     Define browser routes for the Research Agent user
#     interface and delegate agent behavior to the UI service.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from project0.agents.research.research_agent_ui_service import (
    ResearchAgentUIService,
)
from project0.dashboard.dashboard_routes import build_dashboard_shell_context


RESEARCH_AGENT_ROUTE_PREFIX = "/agents/research"
RESEARCH_AGENT_TEMPLATE_NAME = "research_agent_home.html"


def create_research_agent_router(
    ui_service: ResearchAgentUIService,
    templates: Jinja2Templates | None = None,
) -> APIRouter:
    """
    Create the Research Agent router.

    Args:
        ui_service:
            UI adapter used to invoke Research Agent services and
            produce browser-facing page models.
        templates:
            Optional shared Jinja2 template environment. When omitted,
            a local template environment is created for the agent package.

    Returns:
        Configured FastAPI router.
    """

    router = APIRouter(
        prefix=RESEARCH_AGENT_ROUTE_PREFIX,
        tags=["research-agent"],
    )
    template_engine = templates or _create_template_engine()

    @router.get(
        "",
        response_class=HTMLResponse,
        name="research_agent_home",
    )
    async def research_agent_home(request: Request) -> HTMLResponse:
        """Render the initial Research Agent Work Area."""

        page = ui_service.create_ready_page()

        return _render_page(
            templates=template_engine,
            request=request,
            page=page,
        )

    @router.post(
        "/request",
        response_class=HTMLResponse,
        name="research_agent_submit_request",
    )
    async def research_agent_submit_request(
        request: Request,
        question: str = Form(""),
        constraints: str = Form(""),
        focus_areas: str = Form(""),
        source_names: str = Form(""),
    ) -> HTMLResponse:
        """Submit a research request and render the resulting state."""

        page = ui_service.submit_request(
            question=question,
            constraints=_parse_multiline_values(constraints),
            focus_areas=_parse_multiline_values(focus_areas),
            source_names=_parse_multiline_values(source_names),
        )

        return _render_page(
            templates=template_engine,
            request=request,
            page=page,
        )

    return router


def _create_template_engine() -> Jinja2Templates:
    """Create a template environment for the Research Agent package."""

    template_directory = Path(__file__).resolve().parent / "templates"
    return Jinja2Templates(directory=str(template_directory))


def _render_page(
    templates: Jinja2Templates,
    request: Request,
    page: object,
) -> HTMLResponse:
    """Render the Research Agent template with shared context."""

    context = build_dashboard_shell_context(
        request=request,
        active_page="agent:research",
    )
    context.update(
        {
            "page": page,
            "active_navigation": "research-agent",
        }
    )

    return templates.TemplateResponse(
        request=request,
        name=RESEARCH_AGENT_TEMPLATE_NAME,
        context=context,
    )


def _parse_multiline_values(value: str) -> tuple[str, ...]:
    """Convert newline-separated values into normalized values."""

    return tuple(
        line.strip()
        for line in value.splitlines()
        if line.strip()
    )
