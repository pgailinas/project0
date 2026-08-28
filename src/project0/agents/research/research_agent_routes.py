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

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

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
    """Create the Research Agent router."""

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
        guidance: str = Form(""),
        max_results: int = Form(10),
        context_document: UploadFile | None = File(None),
    ) -> HTMLResponse:
        """Submit a research request and render the resulting state."""

        context_source_name = None
        context_content = None

        if context_document is not None and context_document.filename:
            context_source_name = context_document.filename
            context_content = await context_document.read()

        page = await run_in_threadpool(
            ui_service.submit_request,
            question=question,
            guidance=guidance,
            max_results=max_results,
            context_source_name=context_source_name,
            context_content=context_content,
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
