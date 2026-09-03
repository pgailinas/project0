# ============================================================
# Project0 - Research Agent UI Flow Integration Tests
#
# File: test_research_agent_ui_flow.py
#
# Purpose:
#     Verify the browser-facing Research Agent workflow across
#     routes, UI service, templates, research results, and
#     generated research artifacts.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from project0.agents.research.research_agent_routes import (
    create_research_agent_router,
)
from project0.agents.research.research_agent_ui_service import (
    ResearchAgentUIService,
)


@dataclass
class FakeResearchWorkflow:
    """Workflow fake for the browser-facing Research Agent UI flow."""

    received_request: dict[str, Any] | None = None

    def run_research_workflow(
        self,
        question: str,
        guidance: str = "",
        max_results: int = 10,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> object:
        """Return a representative completed research workflow result."""

        self.received_request = {
            "question": question,
            "guidance": guidance,
            "max_results": max_results,
        }

        if (
            context_source_name is not None
            or context_content is not None
        ):
            self.received_request.update(
                {
                    "context_source_name": context_source_name,
                    "context_content": context_content,
                }
            )

        return {
            "request_id": "research-integration-1",
            "status": "completed",
            "source_references": (
                {
                    "source_name": "semantic_scholar",
                    "source_id": "paper-001",
                    "title": "Example Video Representation Paper",
                    "source_url": (
                        "https://www.semanticscholar.org/"
                        "paper/paper-001"
                    ),
                    "authors": (
                        "Author One",
                        "Author Two",
                    ),
                    "publication_year": 2024,
                },
            ),
            "papers": (
                {
                    "source_reference": {
                        "source_id": "paper-001",
                    },
                    "title": "Example Video Representation Paper",
                    "authors": (
                        "Author One",
                        "Author Two",
                    ),
                    "publication_year": 2024,
                    "abstract": (
                        "A paper about semantic video representation "
                        "learning."
                    ),
                    "venue": "Example Conference",
                    "doi": "https://www.semanticscholar.org/",
                    "source_url": (
                        "https://www.semanticscholar.org/"
                        "paper/paper-001"
                    ),
                },
            ),
            "evaluations": (
                {
                    "paper": {
                        "source_reference": {
                            "source_id": "paper-001",
                        },
                        "title": "Example Video Representation Paper",
                    },
                    "relevance_score": 0.95,
                    "relevance_summary": (
                        "The paper is highly relevant to "
                        "vision-language alignment for VideoQA."
                    ),
                    "strengths": (
                        "The paper is highly relevant to",
                    ),
                    "limitations": (
                        "The paper is highly relevant to",
                    ),
                    "research_connections": (
                        (
                            "Evaluate alignment between self-supervised "
                            "video representations and language models."
                        ),
                    ),
                    "warnings": (),
                },
            ),
            "existing_research_context": {
                "research_problem": {
                    "content": "Improve video-text alignment for VideoQA.",
                },
                "findings": (
                    {
                        "content": "Self-supervised video representations "
                        "did not improve VideoQA performance.",
                    },
                    {
                        "content": "CLIP-based representations achieved "
                        "higher VideoQA accuracy.",
                    },
                ),
            },
            "direction_analysis": {
                "synthesis": {
                    "themes": (
                        {
                            "content": "Video-text alignment is a shared theme.",
                            "evidence": (
                                {
                                    "source_type": "research_paper",
                                    "source_id": "internal-evidence-001",
                                },
                            ),
                        },
                    ),
                },
                "candidate_directions": (),
            },
            "paper_analyses": (
                {
                    "paper": {
                        "source_reference": {
                            "source_id": "paper-001",
                        },
                        "title": "Example Video Representation Paper",
                    },
                    "analysis_basis": "abstract_metadata",
                    "problem": {
                        "content": "Improve video-text alignment.",
                    },
                    "approach": {
                        "content": "Contrastive pre-training.",
                    },
                },
            ),
            "artifacts": (
                {
                    "artifact_id": "artifact-001",
                    "artifact_type": "literature_comparison",
                    "title": "Literature Comparison",
                    "content": (
                        "Comparison of selected research papers."
                    ),
                },
                {
                    "artifact_id": "artifact-002",
                    "artifact_type": "research_gap",
                    "title": "Research Gap Analysis",
                    "content": (
                        "Potential research gap in semantic alignment "
                        "for VideoQA representations."
                    ),
                    "source_references": (
                        {
                            "source_id": "paper-001",
                        },
                    ),
                },
            ),
        }


def _project_root() -> Path:
    """Locate the repository root containing pyproject.toml."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent

    raise RuntimeError("Unable to locate Project0 repository root")


def _template_directories() -> list[str]:
    """Return shared Dashboard and Research Agent template paths."""

    source_root = _project_root() / "src" / "project0"

    return [
        str(source_root / "dashboard" / "templates"),
        str(
            source_root
            / "agents"
            / "research"
            / "templates"
        ),
    ]


def _build_client() -> tuple[
    TestClient,
    FakeResearchWorkflow,
]:
    """Create an integrated FastAPI application for the UI flow."""

    workflow = FakeResearchWorkflow()

    ui_service = ResearchAgentUIService(
        workflow=workflow,
    )

    templates = Jinja2Templates(directory=_template_directories())

    app = FastAPI()
    app.include_router(
        create_research_agent_router(
            ui_service=ui_service,
            templates=templates,
        )
    )

    return TestClient(app), workflow


def test_research_agent_home_page_renders_shared_dashboard() -> None:
    """The Research Agent should render inside the Dashboard shell."""

    client, _ = _build_client()

    response = client.get("/agents/research")

    assert response.status_code == 200
    assert "Research Agent" in response.text
    assert "Research Request" in response.text
    assert "Research Workflow" in response.text
    assert "Ready for a research request." in response.text
    assert 'action="/agents/research/request"' in response.text
    assert 'enctype="multipart/form-data"' in response.text
    assert 'name="context_document"' in response.text
    assert 'name="max_results"' in response.text
    assert '<option' in response.text


def test_research_request_presents_consolidated_paper_results() -> None:
    """A submitted request should present the complete research result."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/research/request",
        data={
            "question": (
                "How can self-supervised video representations "
                "be improved for VideoQA?"
            ),
            "guidance": (
                "Prefer recent research. "
                "vision-language alignment "
                "semantic_scholar"
            ),
            "max_results": "5",
        },
    )

    assert response.status_code == 200
    assert workflow.received_request == {
        "question": (
            "How can self-supervised video representations "
            "be improved for VideoQA?"
        ),
        "guidance": (
            "Prefer recent research. "
            "vision-language alignment "
            "semantic_scholar"
        ),
        "max_results": 5,
    }

    assert "The research workflow completed successfully." in response.text
    assert "Research Results" in response.text
    assert "Example Video Representation Paper" in response.text
    assert (
        'href="https://www.semanticscholar.org/paper/paper-001"'
        in response.text
    )
    assert 'target="_blank"' in response.text
    assert 'rel="noopener noreferrer"' in response.text
    assert "Source Details" in response.text
    assert "Relevance Assessment" in response.text
    assert "Paper Summary" in response.text
    assert "Structured Analysis" in response.text
    assert "Contrastive pre-training." in response.text
    assert "A paper about semantic video representation learning." in response.text
    assert "Example Conference" not in response.text
    assert response.text.count(
        "https://www.semanticscholar.org/paper/paper-001"
    ) == 1
    assert "Structured Paper Analysis" not in response.text
    assert "Research Synthesis Artifacts" not in response.text
    assert "Workflow Summary" in response.text
    assert "Existing Research Context Analysis" in response.text
    assert "<dt>Research Problem</dt>" in response.text
    assert response.text.count("<dt>Findings</dt>") == 1
    assert (
        "Self-supervised video representations did not improve "
        "VideoQA performance."
    ) in response.text
    assert (
        "CLIP-based representations achieved higher VideoQA accuracy."
    ) in response.text
    assert "Research Direction Analysis" in response.text
    assert "Video-text alignment is a shared theme." in response.text
    assert "internal-evidence-001" not in response.text


def test_research_request_forwards_uploaded_context_document() -> None:
    """An uploaded context document should reach the workflow as bytes."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/research/request",
        data={
            "question": "What should I investigate next?",
            "guidance": "",
        },
        files={
            "context_document": (
                "prior-research.md",
                b"# Prior Research\nExisting findings.\n",
                "text/markdown",
            ),
        },
    )

    assert response.status_code == 200
    assert workflow.received_request == {
        "question": "What should I investigate next?",
        "guidance": "",
        "max_results": 10,
        "context_source_name": "prior-research.md",
        "context_content": b"# Prior Research\nExisting findings.\n",
    }
    assert "prior-research.md" in response.text


def test_research_request_preserves_multiline_form_values() -> None:
    """Multiline browser values should reach the Research Agent workflow."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/research/request",
        data={
            "question": "Find relevant VideoQA research.",
            "guidance": (
                "Prefer recent research.\n"
                "Prefer peer-reviewed work.\n"
                "vision-language alignment\n"
                "self-supervised video representations\n"
                "semantic_scholar"
            ),
        },
    )

    assert response.status_code == 200
    assert workflow.received_request == {
        "question": "Find relevant VideoQA research.",
        "guidance": (
            "Prefer recent research.\n"
            "Prefer peer-reviewed work.\n"
            "vision-language alignment\n"
            "self-supervised video representations\n"
            "semantic_scholar"
        ),
        "max_results": 10,
    }


def test_blank_research_question_renders_error_state() -> None:
    """A blank browser research question should render safely."""

    client, workflow = _build_client()

    response = client.post(
        "/agents/research/request",
        data={
            "question": "",
            "guidance": "",
        },
    )

    assert response.status_code == 200
    assert workflow.received_request is None
    assert "A research question is required." in response.text
    assert "Enter a research question before continuing." in response.text
