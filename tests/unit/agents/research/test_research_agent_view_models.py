# ============================================================
# Project0 - Research Agent View Model Tests
#
# File: test_research_agent_view_models.py
#
# Purpose:
#     Verify Research Agent presentation models, defaults,
#     enum values, and convenience properties.
#
# ============================================================

from dataclasses import FrozenInstanceError

import pytest

from project0.agents.research.research_agent_view_models import (
    ResearchAgentPageStatus,
    ResearchAgentPageView,
    ResearchEvaluationView,
    ResearchRequestForm,
    ResearchResultView,
    ResearchWorkflowSummaryView,
)
from project0.models.research_models import ResearchStatus


def test_research_agent_page_status_values() -> None:
    """Research Agent page states should expose stable string values."""

    assert ResearchAgentPageStatus.READY == "ready"
    assert ResearchAgentPageStatus.PROCESSING == "processing"
    assert ResearchAgentPageStatus.COMPLETED == "completed"
    assert (
        ResearchAgentPageStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert ResearchAgentPageStatus.FAILED == "failed"


def test_research_request_form_defaults() -> None:
    """A new research request form should begin empty."""

    request_form = ResearchRequestForm()

    assert request_form.question == ""
    assert request_form.guidance == ""
    assert request_form.context_source_name is None


def test_research_result_view_defaults() -> None:
    """Research results should expose safe presentation defaults."""

    result = ResearchResultView(
        rank=1,
        source_id="paper-001",
        title="Example Paper",
    )

    assert not hasattr(result, "artifact_content")

    assert result.publication_year is None
    assert result.source_name is None
    assert result.relevance_score is None
    assert result.relevance_summary == ""
    assert result.authors == ()
    assert result.source_url is None
    assert result.analysis is None


def test_research_evaluation_has_warnings_property() -> None:
    """Research evaluations should report whether warnings exist."""

    no_warnings = ResearchEvaluationView(
        source_id="paper-001",
        title="Example Paper",
        relevance_score=0.9,
        relevance_summary="Highly relevant.",
    )
    with_warnings = ResearchEvaluationView(
        source_id="paper-002",
        title="Second Paper",
        relevance_score=0.7,
        relevance_summary="Relevant with limitations.",
        warnings=("Full paper review is required.",),
    )

    assert no_warnings.has_warnings is False
    assert with_warnings.has_warnings is True


def test_research_agent_page_has_results_property() -> None:
    """Page helpers should identify empty and populated research results."""

    empty_page = ResearchAgentPageView(
        page_status=ResearchAgentPageStatus.READY,
        status_message="Ready for a research request.",
        request_form=ResearchRequestForm(),
    )

    populated_page = ResearchAgentPageView(
        page_status=ResearchAgentPageStatus.COMPLETED,
        status_message="The research workflow completed successfully.",
        request_form=ResearchRequestForm(
            question="Find relevant VideoQA research."
        ),
        results=(
            ResearchResultView(
                rank=1,
                source_id="paper-001",
                title="Example Paper",
            ),
        ),
    )

    assert empty_page.has_results is False
    assert populated_page.has_results is True


def test_research_agent_page_defaults() -> None:
    """Optional page collections and results should have safe defaults."""

    page = ResearchAgentPageView(
        page_status=ResearchAgentPageStatus.READY,
        status_message="Ready for a research request.",
        request_form=ResearchRequestForm(),
    )

    assert page.request_id is None
    assert page.workflow_status is None
    assert page.results == ()
    assert page.workflow_summary is None
    assert page.warnings == ()
    assert page.error_message is None
    assert page.has_results is False
    assert page.has_warnings is False
    assert page.has_error is False


def test_research_workflow_summary_defaults() -> None:
    """Workflow summary counters should default to zero."""

    summary = ResearchWorkflowSummaryView()

    assert summary.source_count == 0
    assert summary.paper_count == 0
    assert summary.evaluation_count == 0


def test_research_evaluation_view_defaults() -> None:
    """Optional research evaluation collections should be empty."""

    evaluation = ResearchEvaluationView(
        source_id="paper-001",
        title="Example Paper",
        relevance_score=None,
        relevance_summary="Relevance could not be determined.",
    )

    assert evaluation.strengths == ()
    assert evaluation.limitations == ()
    assert evaluation.research_connections == ()
    assert evaluation.warnings == ()
    assert evaluation.has_warnings is False


def test_research_agent_page_preserves_workflow_status() -> None:
    """Page view should preserve Research Agent workflow status."""

    page = ResearchAgentPageView(
        page_status=ResearchAgentPageStatus.COMPLETED,
        status_message="The research workflow completed successfully.",
        request_form=ResearchRequestForm(
            question="Find relevant VideoQA research."
        ),
        workflow_status=ResearchStatus.COMPLETED,
    )

    assert page.workflow_status is ResearchStatus.COMPLETED


def test_view_models_are_immutable() -> None:
    """Presentation models should not be mutable after construction."""

    request_form = ResearchRequestForm(
        question="Find relevant VideoQA research."
    )

    with pytest.raises(FrozenInstanceError):
        request_form.question = "Changed question"
