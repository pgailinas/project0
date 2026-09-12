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
from time import perf_counter

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from project0.agents.research.research_agent_ui_service import (
    ResearchAgentUIService,
)
from project0.dashboard.dashboard_routes import build_dashboard_shell_context
from project0.workflow.research_workflow import (
    get_research_workflow_progress,
)


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

    @router.get(
        "/progress",
        name="research_agent_progress",
    )
    async def research_agent_progress() -> dict[str, object]:
        """Return the live Research workflow stage."""

        return get_research_workflow_progress()

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

        started_at = perf_counter()

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
            elapsed_time=_format_elapsed(
                perf_counter() - started_at
            ),
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
    elapsed_time: str | None = None,
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
            **_research_system_status(
                page=page,
                elapsed_time=elapsed_time,
            ),
        }
    )

    return templates.TemplateResponse(
        request=request,
        name=RESEARCH_AGENT_TEMPLATE_NAME,
        context=context,
    )


def _research_system_status(
    page: object,
    elapsed_time: str | None = None,
) -> dict[str, str | None]:
    """Return Research Agent values for the shared System Status panel."""

    page_status = getattr(page, "page_status", None)
    status_value = getattr(page_status, "value", str(page_status or ""))

    states = {
        "ready": "Ready",
        "processing": "Running",
        "completed": "Completed",
        "completed_with_warnings": "Completed with Warnings",
        "failed": "Failed",
    }
    operations = {
        "processing": "Research",
        "completed": "Complete",
        "completed_with_warnings": "Complete",
    }

    return {
        "active_agent_name": "Research Agent",
        "system_state": states.get(status_value, "Idle"),
        "system_operation": operations.get(status_value),
        "elapsed_time": (
            elapsed_time
            if status_value != "ready"
            else None
        ),
    }


def _format_elapsed(elapsed_seconds: float) -> str:
    """Format elapsed seconds for the shared System Status panel."""

    total_seconds = max(0, int(elapsed_seconds))
    minutes, seconds = divmod(total_seconds, 60)

    return f"{minutes:02d}:{seconds:02d}"
