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

import os
import subprocess

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
        "available": True,
    },
)


def _read_git_branch(project_root: Path) -> str:
    """Return the current repository branch when available."""

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "branch",
                "--show-current",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "Unknown"

    return result.stdout.strip() or "Unknown"


def _read_git_status(project_root: Path) -> str:
    """Return a compact current repository status."""

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "status",
                "--porcelain",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "Unavailable"

    return "Clean" if not result.stdout.strip() else "Modified"


def _count_documentation(project_root: Path) -> int | str:
    """Return the number of Markdown documentation files."""

    documentation_root = project_root / "docs"

    if not documentation_root.exists():
        return "Unknown"

    return sum(
        1
        for path in documentation_root.rglob("*.md")
        if path.is_file()
    )


def _read_llm_status() -> str:
    """Return the configured Project0 reasoning provider."""

    provider = os.getenv(
        "PROJECT0_REASONING_PROVIDER",
        "ollama",
    ).strip()

    return provider or "Not configured"


def _read_llm_model(agent_identifier: str | None = None) -> str:
    """Return the configured reasoning model for the requested agent."""

    provider = _read_llm_status().casefold()

    if provider != "ollama":
        return "Not applicable"

    default_model = os.getenv(
        "PROJECT0_OLLAMA_MODEL",
        "",
    ).strip()

    if agent_identifier == "research":
        return (
            os.getenv(
                "PROJECT0_RESEARCH_OLLAMA_MODEL",
                default_model or "qwen2.5:7b",
            ).strip()
            or default_model
            or "qwen2.5:7b"
        )

    if agent_identifier == "documentation":
        return (
            os.getenv(
                "PROJECT0_DOCUMENTATION_OLLAMA_MODEL",
                default_model or "gemma3:4b",
            ).strip()
            or default_model
            or "gemma3:4b"
        )

    return default_model or "qwen2.5:7b"


def _read_test_status(project_root: Path) -> tuple[str, str]:
    """Return the latest recorded regression test status."""

    status_path = (
        project_root
        / "docs"
        / "platform"
        / "Project0_Validation_Status.md"
    )

    try:
        lines = status_path.read_text(
            encoding="utf-8",
        ).splitlines()
    except OSError:
        return "Not run", "Unavailable"

    test_status = "Not run"
    validation_status = "Unavailable"

    for line in lines:
        if line.startswith("**Tests:** "):
            test_status = line.removeprefix(
                "**Tests:** "
            ).rstrip()
            if test_status.endswith("  "):
                test_status = test_status[:-2]
        elif line.startswith("**Validation:** "):
            validation_status = line.removeprefix(
                "**Validation:** "
            ).rstrip()
            if validation_status.endswith("  "):
                validation_status = validation_status[:-2]

    return test_status or "Not run", (
        validation_status or "Unavailable"
    )


def _read_gpu_status() -> tuple[str, str, str]:
    """Return current NVIDIA GPU name, utilization, and VRAM usage."""

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "Unavailable", "Unavailable", "Unavailable"

    lines = result.stdout.strip().splitlines()

    if not lines:
        return "Unavailable", "Unavailable", "Unavailable"

    parts = [
        item.strip()
        for item in lines[0].split(",")
    ]

    if len(parts) != 4:
        return "Unavailable", "Unavailable", "Unavailable"

    name, utilization, memory_used, memory_total = parts

    return (
        name,
        f"{utilization}%",
        f"{memory_used} / {memory_total} MiB",
    )


def build_dashboard_shell_context(
    request: Request,
    active_page: str,
) -> dict[str, object]:
    """Build context owned by the shared Dashboard Framework shell."""

    gpu_name, gpu_utilization, gpu_vram = _read_gpu_status()

    agent_identifier = None
    if active_page.startswith("agent:"):
        agent_identifier = active_page.removeprefix("agent:")

    return {
        "request": request,
        "project_name": "Project0",
        "active_page": active_page,
        "agents": DASHBOARD_AGENTS,
        "active_agent_name": "None",
        "system_state": "Idle",
        "system_operation": None,
        "elapsed_time": None,
        "llm_status": _read_llm_status(),
        "llm_model": _read_llm_model(agent_identifier),
        "gpu_name": gpu_name,
        "gpu_utilization": gpu_utilization,
        "gpu_vram": gpu_vram,
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
        test_status, validation_status = _read_test_status(
            project_root
        )
        context.update(
            {
                "repository_name": "project0",
                "project_root": project_root,
                "documentation_url": "/documentation",
                "git_branch": _read_git_branch(project_root),
                "git_status": _read_git_status(project_root),
                "git_status_class": "status-value--muted",
                "current_phase": (
                    "Phase 11 – Research Agent Functional Validation"
                ),
                "documentation_count": _count_documentation(project_root),
                "test_status": test_status,
                "test_status_class": "status-value--success",
                "validation_status": validation_status,
                "validation_status_class": "status-value--muted",
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

    @router.get(
        "/api/system-status",
        name="dashboard_system_status",
    )
    async def dashboard_system_status(
        agent: str | None = None,
    ) -> dict[str, object]:
        """Return current Project0 system status information."""

        gpu_name, gpu_utilization, gpu_vram = _read_gpu_status()

        normalized_agent = agent.strip().lower() if agent else None

        return {
            "llm_provider": _read_llm_status(),
            "llm_model": _read_llm_model(normalized_agent),
            "gpu_name": gpu_name,
            "gpu_utilization": gpu_utilization,
            "gpu_vram": gpu_vram,
        }

    return router
