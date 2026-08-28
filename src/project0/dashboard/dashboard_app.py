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
from fastapi.templating import Jinja2Templates

from project0.agents.documentation.documentation_agent_routes import (
    create_documentation_agent_router,
)
from project0.agents.documentation.documentation_agent_ui_service import (
    DocumentationAgentUIService,
)
from project0.agents.research.research_agent_routes import (
    create_research_agent_router,
)
from project0.agents.research.research_agent_ui_service import (
    ResearchAgentUIService,
)
from project0.common.logging_config import configure_logging
from project0.config.settings import SETTINGS
from project0.dashboard.dashboard_routes import create_dashboard_router
from project0.models.reasoning_models import ProviderResponse
from project0.platform.platform_dispatcher import create_platform_dispatcher
from project0.reasoning.providers.ollama_provider import (
    OllamaReasoningProvider,
)
from project0.reasoning.providers.stub_provider import (
    StubReasoningProvider,
)


ApplicationFactory = Callable[[], FastAPI]


def create_dashboard_app(
    project_root: Path | None = None,
    documentation_agent_ui_service: DocumentationAgentUIService | None = None,
    research_agent_ui_service: ResearchAgentUIService | None = None,
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

    if documentation_agent_ui_service is not None:
        documentation_agent_root = (
            dashboard_root.parent / "agents" / "documentation"
        )
        documentation_agent_templates = Jinja2Templates(
            directory=[
                str(dashboard_root / "templates"),
                str(documentation_agent_root / "templates"),
            ]
        )

        application.state.documentation_agent_root = documentation_agent_root
        application.state.documentation_agent_ui_service = (
            documentation_agent_ui_service
        )

        application.include_router(
            create_documentation_agent_router(
                ui_service=documentation_agent_ui_service,
                templates=documentation_agent_templates,
            )
        )

        documentation_agent_static_directory = (
            documentation_agent_root / "css"
        )
        if documentation_agent_static_directory.is_dir():
            application.mount(
                "/agents/documentation/css",
                StaticFiles(
                    directory=documentation_agent_static_directory
                ),
                name="documentation-agent-static",
            )

    if research_agent_ui_service is not None:
        research_agent_root = (
            dashboard_root.parent / "agents" / "research"
        )
        research_agent_templates = Jinja2Templates(
            directory=[
                str(dashboard_root / "templates"),
                str(research_agent_root / "templates"),
            ]
        )

        application.state.research_agent_root = research_agent_root
        application.state.research_agent_ui_service = (
            research_agent_ui_service
        )

        application.include_router(
            create_research_agent_router(
                ui_service=research_agent_ui_service,
                templates=research_agent_templates,
            )
        )

        research_agent_static_directory = (
            research_agent_root / "css"
        )

        if research_agent_static_directory.is_dir():
            application.mount(
                "/agents/research/css",
                StaticFiles(
                    directory=research_agent_static_directory
                ),
                name="research-agent-static",
            )

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


def _create_reasoning_provider():
    """Create the configured Project0 reasoning provider.

    Used for production Ollama execution and retained as the shared
    provider path when no agent-specific provider overrides are required.
    """

    if SETTINGS.reasoning_provider == "ollama":
        return OllamaReasoningProvider(
            base_url=SETTINGS.ollama_base_url,
            timeout_seconds=SETTINGS.ollama_timeout_seconds,
        )

    if SETTINGS.reasoning_provider == "stub":
        return StubReasoningProvider(
            response=ProviderResponse(
                provider_name="stub",
                model_name="stub-model",
                content=(
                    '{"evaluations": ['
                    '{"paper_id": "stub-paper-001", '
                    '"relevance_score": 95, '
                    '"research_connections": '
                    '["vision-language alignment"], '
                    '"summary": "Stub research evaluation.", '
                    '"limitations": '
                    '"Stub evaluation for deterministic testing."'
                    '}]}'
                ),
                structured_output={
                    "evaluations": [
                        {
                            "source_id": "stub-paper-001",
                            "relevance_score": 95,
                            "relevance_summary": (
                                "Stub research evaluation."
                            ),
                            "strengths": [
                                "Vision-language alignment relevance",
                            ],
                            "limitations": [
                                "Stub evaluation for deterministic testing",
                            ],
                            "research_connections": [
                                "vision-language alignment",
                            ],
                            "warnings": [],
                        },
                    ],
                },
                duration_seconds=0.0,
                metadata={
                    "stub": True,
                    "purpose": "research-agent-development",
                },
            )
        )

    raise ValueError(
        "Unsupported Project0 reasoning provider: "
        f"{SETTINGS.reasoning_provider}"
    )




def _create_documentation_reasoning_provider():
    """Create deterministic Documentation Agent reasoning behavior."""

    return StubReasoningProvider(
        response=ProviderResponse(
            provider_name="stub",
            model_name="stub-model",
            content=(
                '{"summary": "Generated documentation proposal."}'
            ),
            structured_output={
                "summary": (
                    "Generated documentation proposal."
                ),
                "assumptions": [],
                "warnings": [],
                "impacts": [
                    {
                        "document_path": (
                            "tests/test_data/documentation_agent/"
                            "revision_test_document.md"
                        ),
                        "summary": "Documentation update",
                        "rationale": (
                            "Expand the workflow sequence to include "
                            "approval before applying "
                            "documentation changes."
                        ),
                        "confidence": 0.95,
                    }
                ],
                "proposed_changes": [
                    {
                        "document_path": (
                            "tests/test_data/documentation_agent/"
                            "revision_test_document.md"
                        ),
                        "operation": "update",
                        "rationale": (
                            "Expand the workflow sequence to include "
                            "approval before applying "
                            "documentation changes."
                        ),
                        "proposed_content": (
                            "# Updated Documentation\\n\\n"
                            "Workflow changes require approval "
                            "before applying documentation changes.\\n"
                        ),
                        "anchor_text": "Implemented:",
                        "edit_type": "insert",
                        "confidence": 0.95,
                    }
                ],
            },
            duration_seconds=0.0,
            metadata={
                "stub": True,
                "purpose": "documentation-agent-development",
            },
        )
    )


def _create_research_reasoning_provider():
    """Create deterministic Research Agent reasoning behavior."""

    return StubReasoningProvider(
        response=ProviderResponse(
            provider_name="stub",
            model_name="stub-model",
            content=(
                '{"evaluations": ['
                '{"paper_id": "stub-paper-001", '
                '"relevance_score": 95, '
                '"research_connections": '
                '["vision-language alignment"], '
                '"summary": "Stub research evaluation.", '
                '"limitations": '
                '"Stub evaluation for deterministic testing."'
                '}]}'
            ),
            structured_output={
                "evaluations": [
                    {
                        "source_id": "stub-paper-001",
                        "relevance_score": 95,
                        "relevance_summary": (
                            "Stub research evaluation."
                        ),
                        "strengths": [
                            "Vision-language alignment relevance",
                        ],
                        "limitations": [
                            "Stub evaluation for deterministic testing",
                        ],
                        "research_connections": [
                            "vision-language alignment",
                        ],
                        "warnings": [],
                    },
                ],
            },
            duration_seconds=0.0,
            metadata={
                "stub": True,
                "purpose": "research-agent-development",
            },
        )
    )


def create_project0_dashboard_app() -> FastAPI:
    """Create the configured Project0 Dashboard application."""

    configure_logging()

    if SETTINGS.reasoning_provider == "stub":
        documentation_reasoning_provider = (
            _create_documentation_reasoning_provider()
        )
        research_reasoning_provider = (
            _create_research_reasoning_provider()
        )

        dispatcher = create_platform_dispatcher(
            documentation_reasoning_provider=(
                documentation_reasoning_provider
            ),
            research_reasoning_provider=(
                research_reasoning_provider
            ),
            reasoning_model_name=SETTINGS.ollama_model,
        )

    else:
        reasoning_provider = _create_reasoning_provider()

        dispatcher = create_platform_dispatcher(
            reasoning_provider=reasoning_provider,
            reasoning_model_name=SETTINGS.ollama_model,
        )
    documentation_agent_ui_service = DocumentationAgentUIService(
        workflow=dispatcher,
    )

    research_agent_ui_service = ResearchAgentUIService(
        workflow=dispatcher,
    )

    return create_dashboard_app(
        project_root=SETTINGS.project_root,
        documentation_agent_ui_service=(
            documentation_agent_ui_service
        ),
        research_agent_ui_service=(
            research_agent_ui_service
        ),
    )


app = create_dashboard_app()


def main() -> None:
    """Run the Project0 Dashboard locally on port 8001."""

    import uvicorn

    uvicorn.run(
        (
            "project0.dashboard.dashboard_app:"
            "create_project0_dashboard_app"
        ),
        host="127.0.0.1",
        port=8001,
        reload=True,
        factory=True,
    )


if __name__ == "__main__":
    main()
