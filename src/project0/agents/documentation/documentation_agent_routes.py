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

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
from project0.dashboard.dashboard_routes import build_dashboard_shell_context
from project0.platform.background_runs import (
    BackgroundRunManager,
    BackgroundRunState,
)


DOCUMENTATION_AGENT_ROUTE_PREFIX = "/agents/documentation"
DOCUMENTATION_AGENT_TEMPLATE_NAME = "documentation_agent_home.html"


def create_documentation_agent_router(
    ui_service: DocumentationAgentUIService,
    templates: Jinja2Templates | None = None,
    run_manager: BackgroundRunManager | None = None,
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
    background_runs = run_manager or BackgroundRunManager()

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

    @router.get(
        "/runs/{run_id}",
        response_class=HTMLResponse,
        name="documentation_agent_run",
    )
    async def documentation_agent_run(
        request: Request,
        run_id: str,
    ) -> HTMLResponse:
        """Render the processing or completed state for one run."""

        run = _get_documentation_run(background_runs, run_id)
        if run.state is BackgroundRunState.COMPLETED and run.result is not None:
            page = run.result
        elif run.state is BackgroundRunState.FAILED:
            page = DocumentationAgentPageView(
                page_status=DocumentationAgentPageStatus.FAILED,
                status_message="The documentation workflow could not be completed.",
                request_form=DocumentationRequestForm(),
                error_message=run.error_message,
            )
        else:
            page = run.interim_result
            if page is None:
                page = DocumentationAgentPageView(
                    page_status=DocumentationAgentPageStatus.PROCESSING,
                    status_message="The documentation workflow is processing.",
                    request_form=DocumentationRequestForm(),
                )
        return _render_page(
            templates=template_engine,
            request=request,
            page=page,
            run_id=run_id,
            elapsed_time=_elapsed_since(run.started_at or run.created_at),
        )

    @router.get(
        "/runs/{run_id}/status",
        name="documentation_agent_run_status",
    )
    async def documentation_agent_run_status(run_id: str) -> dict[str, str]:
        """Return the platform lifecycle state for one documentation run."""

        run = _get_documentation_run(background_runs, run_id)
        return {
            "run_id": run.run_id,
            "run_state": run.state.value,
            "result_url": f"{DOCUMENTATION_AGENT_ROUTE_PREFIX}/runs/{run_id}",
        }

    @router.post(
        "/request",
        response_class=HTMLResponse,
        name="documentation_agent_submit_request",
    )
    async def documentation_agent_submit_request(
        request: Request,
        user_request: str = Form(""),
        source_paths: str = Form(""),
        target_paths: str = Form(""),
    ) -> HTMLResponse:
        """Submit a documentation request and render the resulting state."""

        parsed_source_paths = _parse_source_paths(source_paths)
        parsed_target_paths = _parse_target_paths(target_paths)
        processing_page = _create_documentation_processing_page(
            user_request=user_request,
            source_paths=parsed_source_paths,
            target_paths=parsed_target_paths,
        )
        run = background_runs.submit(
            "documentation",
            lambda: ui_service.submit_request(
                user_request=user_request,
                source_paths=parsed_source_paths,
                target_paths=parsed_target_paths,
            ),
            interim_result=processing_page,
        )
        return RedirectResponse(
            url=f"{DOCUMENTATION_AGENT_ROUTE_PREFIX}/runs/{run.run_id}",
            status_code=303,
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
            run = background_runs.submit(
                "documentation",
                lambda: ui_service.submit_review_decision(
                    workflow_id=workflow_id,
                    proposal_id=proposal_id,
                    decision=review_decision,
                    feedback=feedback,
                ),
            )
            return RedirectResponse(
                url=f"{DOCUMENTATION_AGENT_ROUTE_PREFIX}/runs/{run.run_id}",
                status_code=303,
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
    run_id: str | None = None,
    elapsed_time: str | None = None,
) -> HTMLResponse:
    """Render the Documentation Agent template with shared context."""

    context = build_dashboard_shell_context(
        request=request,
        active_page="agent:documentation",
    )
    context.update(
        {
            "page": page,
            "active_navigation": "documentation-agent",
            "run_id": run_id,
            "elapsed_time": elapsed_time,
        }
    )

    return templates.TemplateResponse(
        request=request,
        name=DOCUMENTATION_AGENT_TEMPLATE_NAME,
        context=context,
    )



def _parse_source_paths(value: str) -> tuple[str, ...]:
    """Convert newline-separated source paths into normalized values."""

    return tuple(
        line.strip()
        for line in value.splitlines()
        if line.strip()
    )

def _parse_target_paths(value: str) -> tuple[str, ...]:
    """Convert newline-separated target paths into normalized values."""

    return tuple(
        line.strip()
        for line in value.splitlines()
        if line.strip()
    )


def _elapsed_since(started_at: datetime) -> str:
    total_seconds = max(
        0,
        int((datetime.now(UTC) - started_at).total_seconds()),
    )
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _create_documentation_processing_page(
    user_request: str,
    source_paths: tuple[str, ...],
    target_paths: tuple[str, ...],
) -> DocumentationAgentPageView:
    """Create processing state without discarding submitted form values."""

    return DocumentationAgentPageView(
        page_status=DocumentationAgentPageStatus.PROCESSING,
        status_message="The documentation workflow is processing.",
        request_form=DocumentationRequestForm(
            user_request=user_request.strip(),
            source_paths=source_paths,
            target_paths=target_paths,
        ),
    )


def _get_documentation_run(
    run_manager: BackgroundRunManager,
    run_id: str,
):
    run = run_manager.get(run_id)
    if run is None or run.agent_identifier != "documentation":
        raise HTTPException(status_code=404, detail="Documentation run not found.")
    return run
