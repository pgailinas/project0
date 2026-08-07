# ============================================================
# Project0 - Documentation Agent Routes
#
# File: documentation_agent_routes.py
#
# Purpose:
#     Define browser routes for the Documentation Agent user
#     interface and delegate agent behavior to the UI service.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from project0.agents.documentation.documentation_agent_ui_service import (
    DocumentationAgentUIService,
)
from project0.agents.documentation.documentation_agent_view_models import (
    DocumentationAgentPageStatus,
    DocumentationAgentPageView,
    DocumentationRequestForm,
)
from project0.models.documentation_workflow_models import ReviewDecision


DOCUMENTATION_AGENT_ROUTE_PREFIX = "/agents/documentation"
DOCUMENTATION_AGENT_TEMPLATE_NAME = "documentation_agent_home.html"


def create_documentation_agent_router(
    ui_service: DocumentationAgentUIService,
    templates: Jinja2Templates | None = None,
) -> APIRouter:
    """
    Create the Documentation Agent router.

    Args:
        ui_service:
            UI adapter used to invoke Documentation Agent services and
            produce browser-facing page models.
        templates:
            Optional shared Jinja2 template environment. When omitted,
            a local template environment is created for the agent package.

    Returns:
        Configured FastAPI router.
    """

    router = APIRouter(
        prefix=DOCUMENTATION_AGENT_ROUTE_PREFIX,
        tags=["documentation-agent"],
    )
    template_engine = templates or _create_template_engine()

    @router.get(
        "",
        response_class=HTMLResponse,
        name="documentation_agent_home",
    )
    async def documentation_agent_home(request: Request) -> HTMLResponse:
        """Render the initial Documentation Agent Work Area."""

        page = ui_service.create_ready_page()

        return _render_page(
            templates=template_engine,
            request=request,
            page=page,
        )

    @router.post(
        "/request",
        response_class=HTMLResponse,
        name="documentation_agent_submit_request",
    )
    async def documentation_agent_submit_request(
        request: Request,
        user_request: str = Form(""),
        target_paths: str = Form(""),
    ) -> HTMLResponse:
        """Submit a documentation request and render the resulting state."""

        page = ui_service.submit_request(
            user_request=user_request,
            target_paths=_parse_target_paths(target_paths),
        )

        return _render_page(
            templates=template_engine,
            request=request,
            page=page,
        )

    @router.post(
        "/review",
        response_class=HTMLResponse,
        name="documentation_agent_submit_review",
    )
    async def documentation_agent_submit_review(
        request: Request,
        workflow_id: str = Form(...),
        proposal_id: str = Form(...),
        decision: str = Form(...),
        feedback: str = Form(""),
    ) -> HTMLResponse:
        """Submit one review decision and render updated workflow state."""

        try:
            review_decision = ReviewDecision(decision)
        except ValueError:
            page = DocumentationAgentPageView(
                page_status=DocumentationAgentPageStatus.FAILED,
                status_message="The review decision could not be processed.",
                request_form=DocumentationRequestForm(),
                workflow_id=workflow_id,
                error_message=f"Unsupported review decision: {decision}",
            )
        else:
            page = ui_service.submit_review_decision(
                workflow_id=workflow_id,
                proposal_id=proposal_id,
                decision=review_decision,
                feedback=feedback,
            )

        return _render_page(
            templates=template_engine,
            request=request,
            page=page,
        )

    return router


def _create_template_engine() -> Jinja2Templates:
    """Create a template environment for the Documentation Agent package."""

    template_directory = Path(__file__).resolve().parent / "templates"
    return Jinja2Templates(directory=str(template_directory))


def _render_page(
    templates: Jinja2Templates,
    request: Request,
    page: object,
) -> HTMLResponse:
    """Render the Documentation Agent template with shared context."""

    return templates.TemplateResponse(
        request=request,
        name=DOCUMENTATION_AGENT_TEMPLATE_NAME,
        context={
            "request": request,
            "page": page,
            "active_navigation": "documentation-agent",
        },
    )


def _parse_target_paths(value: str) -> tuple[str, ...]:
    """Convert newline-separated target paths into normalized values."""

    return tuple(
        line.strip()
        for line in value.splitlines()
        if line.strip()
    )
