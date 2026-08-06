# ============================================================
# Project0 - Dashboard Framework
#
# File: dashboard_app.py
#
# Purpose:
#     Create and configure the Project0 browser-based dashboard
#     application without implementing agent-specific behavior.
#
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from project0.dashboard.dashboard_routes import create_dashboard_router


ApplicationFactory = Callable[[], FastAPI]


def create_dashboard_app(
    project_root: Path | None = None,
) -> FastAPI:
    """Create and configure the Project0 Dashboard application."""

    resolved_project_root = (
        project_root.resolve()
        if project_root is not None
        else Path.cwd().resolve()
    )

    dashboard_root = Path(__file__).resolve().parent
    static_directory = dashboard_root / "css"

    application = FastAPI(
        title="Project0 Dashboard",
        description=(
            "Browser-based interface for Project0 platform services "
            "and registered AI agents."
        ),
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    application.state.project_root = resolved_project_root
    application.state.dashboard_root = dashboard_root

    application.include_router(
        create_dashboard_router(
            project_root=resolved_project_root,
            dashboard_root=dashboard_root,
        )
    )

    if static_directory.is_dir():
        application.mount(
            "/css",
            StaticFiles(directory=static_directory),
            name="static",
        )

    return application


app = create_dashboard_app()


def main() -> None:
    """Run the Project0 Dashboard locally on port 8001."""

    import uvicorn

    uvicorn.run(
        "project0.dashboard.dashboard_app:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    main()
    

