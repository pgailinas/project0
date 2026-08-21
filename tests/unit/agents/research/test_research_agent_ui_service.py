# ============================================================
# Project0 - Research Agent UI Service Tests
#
# File: test_research_agent_ui_service.py
#
# Purpose:
#     Verify Research Agent UI service request handling,
#     workflow mapping, result presentation, and failure states.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project0.agents.research.research_agent_ui_service import (
    ResearchAgentUIService,
)
from project0.agents.research.research_agent_view_models import (
    ResearchAgentPageStatus,
)
from project0.models.research_models import (
    ResearchArtifactType,
    ResearchStatus,
)


@dataclass
class FakeWorkflow:
    """Simple workflow fake used by UI service tests."""

    result: object | None = None
    error: Exception | None = None
    received_arguments: dict[str, Any] | None = None

    def run_research_workflow(
        self,
        question: str,
        constraints: tuple[str, ...] = (),
        focus_areas: tuple[str, ...] = (),
        source_names: tuple[str, ...] = (),
    ) -> object:
        """Record request arguments and return or raise the configured result."""

        self.received_arguments = {
            "question": question,
            "constraints": constraints,
            "focus_areas": focus_areas,
            "source_names": source_names,
        }

        if self.error is not None:
            raise self.error

        return self.result


def test_create_ready_page() -> None:
    """The initial page should be ready with an empty request form."""

    service = ResearchAgentUIService(workflow=FakeWorkflow())

    page = service.create_ready_page()

    assert page.page_status is ResearchAgentPageStatus.READY
    assert page.status_message == "Ready for a research request."
    assert page.request_form.question == ""
    assert page.request_form.constraints == ()
    assert page.request_form.focus_areas == ()
    assert page.request_form.source_names == ()
    assert page.request_id is None
    assert page.has_results is False
    assert page.has_error is False


def test_submit_request_requires_nonempty_question() -> None:
    """Blank research questions should fail before workflow execution."""

    workflow = FakeWorkflow()
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="   ",
        constraints=(" Prefer recent research. ",),
    )

    assert page.page_status is ResearchAgentPageStatus.FAILED
    assert page.status_message == "A research question is required."
    assert page.error_message == (
        "Enter a research question before continuing."
    )
    assert page.request_form.question == ""
    assert page.request_form.constraints == (
        "Prefer recent research.",
    )
    assert workflow.received_arguments is None


def test_submit_request_normalizes_form_values() -> None:
    """Submitted research values should be stripped and filtered."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-1",
            "status": "pending",
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="  Find relevant VideoQA research.  ",
        constraints=(
            " Prefer recent research. ",
            "",
            "   ",
        ),
        focus_areas=(
            " vision-language alignment ",
            "",
        ),
        source_names=(
            " semantic_scholar ",
            "   ",
        ),
    )

    assert workflow.received_arguments == {
        "question": "Find relevant VideoQA research.",
        "constraints": (
            "Prefer recent research.",
        ),
        "focus_areas": (
            "vision-language alignment",
        ),
        "source_names": (
            "semantic_scholar",
        ),
    }
    assert page.request_form.question == (
        "Find relevant VideoQA research."
    )
    assert page.request_form.constraints == (
        "Prefer recent research.",
    )
    assert page.request_form.focus_areas == (
        "vision-language alignment",
    )
    assert page.request_form.source_names == (
        "semantic_scholar",
    )
    assert page.page_status is ResearchAgentPageStatus.PROCESSING


def test_submit_request_maps_completed_result() -> None:
    """A completed workflow should produce a completed page state."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-2",
            "status": "completed",
            "source_references": (
                {
                    "source_name": "semantic_scholar",
                    "source_id": "paper-001",
                    "title": "Example Paper",
                    "source_url": "https://example.com/paper-001",
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
                    "title": "Example Paper",
                    "authors": (
                        "Author One",
                        "Author Two",
                    ),
                    "publication_year": 2024,
                    "abstract": "Example abstract.",
                    "venue": "Example Conference",
                    "doi": "10.1000/example",
                    "source_url": "https://example.com/paper-001",
                },
            ),
            "evaluations": (
                {
                    "paper": {
                        "source_reference": {
                            "source_id": "paper-001",
                        },
                        "title": "Example Paper",
                    },
                    "relevance_score": 0.95,
                    "relevance_summary": "Highly relevant.",
                    "strengths": (
                        "Strong semantic alignment.",
                    ),
                    "limitations": (
                        "Limited VideoQA evaluation.",
                    ),
                    "research_connections": (
                        "Evaluate aligned video representations.",
                    ),
                    "warnings": (),
                },
            ),
            "artifacts": (
                {
                    "artifact_id": "artifact-001",
                    "artifact_type": "paper_summary",
                    "title": "Example Paper Summary",
                    "content": "Summary content.",
                    "source_references": (
                        {
                            "source_id": "paper-001",
                        },
                    ),
                },
            ),
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant VideoQA research."
    )

    assert page.page_status is ResearchAgentPageStatus.COMPLETED
    assert page.status_message == (
        "The research workflow completed successfully."
    )
    assert page.request_id == "research-request-2"
    assert page.workflow_status is ResearchStatus.COMPLETED

    assert len(page.sources) == 1
    assert page.sources[0].source_name == "semantic_scholar"
    assert page.sources[0].source_id == "paper-001"
    assert page.sources[0].title == "Example Paper"
    assert page.sources[0].authors == (
        "Author One",
        "Author Two",
    )
    assert page.sources[0].publication_year == 2024

    assert len(page.papers) == 1
    assert page.papers[0].source_id == "paper-001"
    assert page.papers[0].abstract == "Example abstract."
    assert page.papers[0].venue == "Example Conference"
    assert page.papers[0].doi == "10.1000/example"

    assert len(page.evaluations) == 1
    assert page.evaluations[0].source_id == "paper-001"
    assert page.evaluations[0].relevance_score == 0.95
    assert page.evaluations[0].relevance_summary == (
        "Highly relevant."
    )
    assert page.evaluations[0].strengths == (
        "Strong semantic alignment.",
    )
    assert page.evaluations[0].limitations == (
        "Limited VideoQA evaluation.",
    )
    assert page.evaluations[0].research_connections == (
        "Evaluate aligned video representations.",
    )

    assert len(page.artifacts) == 1
    assert page.artifacts[0].artifact_id == "artifact-001"
    assert (
        page.artifacts[0].artifact_type
        is ResearchArtifactType.PAPER_SUMMARY
    )
    assert page.artifacts[0].source_ids == (
        "paper-001",
    )

    assert page.workflow_summary is not None
    assert page.workflow_summary.source_count == 1
    assert page.workflow_summary.paper_count == 1
    assert page.workflow_summary.evaluation_count == 1
    assert page.workflow_summary.artifact_count == 1
    assert page.has_results is True


def test_submit_request_maps_completed_with_warnings_result() -> None:
    """Completed workflows with warnings should use the warning page state."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-3",
            "status": "completed_with_warnings",
            "warnings": (
                "One paper could not be evaluated.",
            ),
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert (
        page.page_status
        is ResearchAgentPageStatus.COMPLETED_WITH_WARNINGS
    )
    assert page.status_message == (
        "The research workflow completed with warnings."
    )
    assert page.warnings == (
        "One paper could not be evaluated.",
    )
    assert page.has_warnings is True


def test_submit_request_maps_failed_result() -> None:
    """Failed research results should produce failed page state."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-4",
            "status": "failed",
            "error_message": "Research source unavailable.",
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert page.page_status is ResearchAgentPageStatus.FAILED
    assert page.error_message == "Research source unavailable."
    assert page.has_error is True


def test_submit_request_handles_workflow_exception() -> None:
    """Workflow exceptions should become consistent failure pages."""

    workflow = FakeWorkflow(
        error=RuntimeError("Reasoning service unavailable.")
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research.",
        source_names=("semantic_scholar",),
    )

    assert page.page_status is ResearchAgentPageStatus.FAILED
    assert page.status_message == (
        "The research workflow could not be completed."
    )
    assert page.error_message == "Reasoning service unavailable."
    assert page.request_form.question == "Find relevant research."
    assert page.request_form.source_names == (
        "semantic_scholar",
    )


def test_submit_request_maps_evaluation_warnings() -> None:
    """Research evaluation warnings should be preserved for display."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-5",
            "status": "completed",
            "evaluations": (
                {
                    "paper": {
                        "source_reference": {
                            "source_id": "paper-001",
                        },
                        "title": "Example Paper",
                    },
                    "relevance_score": 0.5,
                    "relevance_summary": "Moderately relevant.",
                    "warnings": (
                        "Abstract-only evaluation.",
                    ),
                },
            ),
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert len(page.evaluations) == 1
    assert page.evaluations[0].warnings == (
        "Abstract-only evaluation.",
    )
    assert page.evaluations[0].has_warnings is True


def test_submit_request_maps_unknown_status_to_processing() -> None:
    """Unknown workflow status should fall back to processing state."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-6",
            "status": "unknown-status",
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert page.page_status is ResearchAgentPageStatus.PROCESSING
    assert page.workflow_status is None


def test_submit_request_maps_unknown_artifact_type_to_summary() -> None:
    """Unknown artifact types should use the safe summary default."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-7",
            "status": "completed",
            "artifacts": (
                {
                    "artifact_id": "artifact-001",
                    "artifact_type": "unknown-artifact",
                    "title": "Unknown Artifact",
                    "content": "Artifact content.",
                },
            ),
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert len(page.artifacts) == 1
    assert (
        page.artifacts[0].artifact_type
        is ResearchArtifactType.PAPER_SUMMARY
    )


def test_submit_request_normalizes_optional_text_values() -> None:
    """Optional text fields should be stripped or mapped to None."""

    workflow = FakeWorkflow(
        result={
            "request_id": "  research-request-8  ",
            "status": "completed",
            "source_references": (
                {
                    "source_name": "semantic_scholar",
                    "source_id": "paper-001",
                    "title": "Example Paper",
                    "source_url": "  https://example.com/paper-001  ",
                },
            ),
            "papers": (
                {
                    "source_reference": {
                        "source_id": "paper-001",
                    },
                    "title": "Example Paper",
                    "abstract": "  Example abstract.  ",
                    "venue": "   ",
                    "doi": None,
                    "source_url": "  https://example.com/paper-001  ",
                },
            ),
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert page.request_id == "research-request-8"
    assert page.sources[0].source_url == (
        "https://example.com/paper-001"
    )
    assert page.papers[0].abstract == "Example abstract."
    assert page.papers[0].venue is None
    assert page.papers[0].doi is None
    assert page.papers[0].source_url == (
        "https://example.com/paper-001"
    )


def test_warning_without_explicit_status_uses_warning_page() -> None:
    """Warnings without workflow status should use warning page state."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-9",
            "warnings": (
                "Partial metadata available.",
            ),
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="Find relevant research."
    )

    assert (
        page.page_status
        is ResearchAgentPageStatus.COMPLETED_WITH_WARNINGS
    )
    assert page.has_warnings is True
