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
from project0.models.research_models import ResearchStatus


@dataclass
class FakeWorkflow:
    """Simple workflow fake used by UI service tests."""

    result: object | None = None
    error: Exception | None = None
    received_arguments: dict[str, Any] | None = None

    def run_research_workflow(
        self,
        question: str,
        guidance: str = "",
        max_results: int = 10,
        context_source_name: str | None = None,
        context_content: bytes | None = None,
    ) -> object:
        """Record request arguments and return or raise the configured result."""

        self.received_arguments = {
            "question": question,
            "guidance": guidance,
            "max_results": max_results,
        }

        if (
            context_source_name is not None
            or context_content is not None
        ):
            self.received_arguments.update(
                {
                    "context_source_name": context_source_name,
                    "context_content": context_content,
                }
            )

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
    assert page.request_form.guidance == ""
    assert page.request_form.max_results == 10
    assert page.request_id is None
    assert page.has_results is False
    assert page.has_error is False


def test_submit_request_requires_nonempty_question() -> None:
    """Blank research questions should fail before workflow execution."""

    workflow = FakeWorkflow()
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="   ",
        guidance=" Prefer recent research. ",
    )

    assert page.page_status is ResearchAgentPageStatus.FAILED
    assert page.status_message == "A research question is required."
    assert page.error_message == (
        "Enter a research question before continuing."
    )
    assert page.request_form.question == ""
    assert page.request_form.guidance == "Prefer recent research."
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
        guidance=" vision-language alignment using semantic_scholar ",
        max_results=5,
    )

    assert workflow.received_arguments == {
        "question": "Find relevant VideoQA research.",
        "guidance": "vision-language alignment using semantic_scholar",
        "max_results": 5,
    }
    assert page.request_form.question == (
        "Find relevant VideoQA research."
    )
    assert page.request_form.guidance == "vision-language alignment using semantic_scholar"
    assert page.request_form.max_results == 5


    assert page.page_status is ResearchAgentPageStatus.PROCESSING


def test_submit_request_forwards_context_document() -> None:
    """Submitted context filename and bytes should reach the workflow."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-context",
            "status": "pending",
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    service.submit_request(
        question="What should I investigate next?",
        context_source_name="prior-research.md",
        context_content=b"# Prior Research\n",
    )

    assert workflow.received_arguments == {
        "question": "What should I investigate next?",
        "guidance": "",
        "max_results": 10,
        "context_source_name": "prior-research.md",
        "context_content": b"# Prior Research\n",
    }


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
                    "artifact_type": "literature_comparison",
                    "title": "Literature Comparison",
                    "content": "Comparison content.",
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

    assert len(page.results) == 1
    assert page.results[0].source_name == "semantic_scholar"
    assert page.results[0].source_id == "paper-001"
    assert page.results[0].title == "Example Paper"
    assert page.results[0].authors == (
        "Author One",
        "Author Two",
    )
    assert page.results[0].publication_year == 2024


    assert len(page.results) == 1
    assert page.results[0].source_id == "paper-001"
    assert page.results[0].relevance_score == 0.95
    assert page.results[0].relevance_summary == (
        "Highly relevant."
    )

    assert not hasattr(page.results[0], "artifact_content")

    assert page.workflow_summary is not None
    assert page.workflow_summary.source_count == 1
    assert page.workflow_summary.paper_count == 1
    assert page.workflow_summary.evaluation_count == 1
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
        guidance="semantic_scholar",
    )

    assert page.page_status is ResearchAgentPageStatus.FAILED
    assert page.status_message == (
        "The research workflow could not be completed."
    )
    assert page.error_message == "Reasoning service unavailable."
    assert page.request_form.question == "Find relevant research."



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

    assert page.has_results is False
    assert page.workflow_summary is not None
    assert page.workflow_summary.evaluation_count == 1


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
    assert page.results[0].source_url == (
        "https://example.com/paper-001"
    )
    assert page.results[0].source_url == (
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

def test_submit_request_maps_research_direction_analysis() -> None:
    """Research direction analysis should be preserved for display."""

    workflow = FakeWorkflow(
        result={
            "request_id": "research-request-directions",
            "status": "completed",
            "direction_analysis": {
                "synthesis": {
                    "themes": (
                        {
                            "content": (
                                "Contrastive alignment recurs across "
                                "the analyzed papers."
                            ),
                            "evidence": (
                                {
                                    "source_type": "research_paper",
                                    "source_id": "paper-001",
                                    "page_number": 4,
                                },
                                {
                                    "source_type": "research_paper",
                                    "source_id": "paper-002",
                                    "page_number": 6,
                                },
                            ),
                        },
                    ),
                    "comparisons": (),
                    "shared_limitations": (),
                    "unresolved_questions": (
                        {
                            "content": (
                                "The analyzed evidence does not establish "
                                "which alignment objective is best for VideoQA."
                            ),
                            "evidence": (
                                {
                                    "source_type": "research_paper",
                                    "source_id": "paper-002",
                                },
                            ),
                        },
                    ),
                },
                "candidate_directions": (
                    {
                        "direction": (
                            "Investigate contrastive video-language "
                            "alignment for VideoQA."
                        ),
                        "rationale": (
                            "Prior work identified semantic misalignment "
                            "and the analyzed literature supports "
                            "contrastive alignment."
                        ),
                        "context_evidence": (
                            {
                                "source_type": "context_document",
                                "source_id": "context-001",
                                "page_number": 8,
                                "section": "Limitations",
                            },
                        ),
                        "literature_evidence": (
                            {
                                "source_type": "research_paper",
                                "source_id": "paper-001",
                                "page_number": 4,
                            },
                        ),
                        "speculative": False,
                    },
                ),
            },
        }
    )
    service = ResearchAgentUIService(workflow=workflow)

    page = service.submit_request(
        question="What should I investigate next?"
    )

    assert page.page_status is ResearchAgentPageStatus.COMPLETED
    assert page.direction_analysis is not None
    assert page.has_results is True
    assert page.direction_analysis.synthesis.themes[0].content == (
        "Contrastive alignment recurs across the analyzed papers."
    )
    assert tuple(
        evidence.source_id
        for evidence
        in page.direction_analysis.synthesis.themes[0].evidence
    ) == (
        "paper-001",
        "paper-002",
    )
    assert (
        page.direction_analysis.candidate_directions[0].direction
        == "Investigate contrastive video-language alignment for VideoQA."
    )
    assert (
        page.direction_analysis.candidate_directions[0]
        .context_evidence[0].section
        == "Limitations"
    )
    assert (
        page.direction_analysis.candidate_directions[0].speculative
        is False
    )
