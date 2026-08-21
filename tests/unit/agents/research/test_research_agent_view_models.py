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
    PaperMetadataView,
    ResearchAgentPageStatus,
    ResearchAgentPageView,
    ResearchArtifactView,
    ResearchEvaluationView,
    ResearchRequestForm,
    ResearchSourceView,
    ResearchWorkflowSummaryView,
)
from project0.models.research_models import (
    ResearchArtifactType,
    ResearchStatus,
)


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
    assert request_form.constraints == ()
    assert request_form.focus_areas == ()
    assert request_form.source_names == ()


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


def test_research_artifact_has_sources_property() -> None:
    """Research artifacts should report whether source references exist."""

    without_sources = ResearchArtifactView(
        artifact_id="artifact-001",
        artifact_type=ResearchArtifactType.RESEARCH_GAP,
        title="Research Gap",
        content="Potential research gap.",
    )
    with_sources = ResearchArtifactView(
        artifact_id="artifact-002",
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Paper Summary",
        content="Summary content.",
        source_ids=("paper-001",),
    )

    assert without_sources.has_sources is False
    assert with_sources.has_sources is True


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
        sources=(
            ResearchSourceView(
                source_name="semantic_scholar",
                source_id="paper-001",
                title="Example Paper",
            ),
        ),
    )

    assert empty_page.has_results is False
    assert populated_page.has_results is True


def test_research_agent_page_warning_and_error_properties() -> None:
    """Page helpers should identify warning and error states."""

    page = ResearchAgentPageView(
        page_status=ResearchAgentPageStatus.FAILED,
        status_message="The research workflow failed.",
        request_form=ResearchRequestForm(
            question="Find relevant VideoQA research."
        ),
        warnings=("One paper could not be evaluated.",),
        error_message="Reasoning service unavailable.",
    )

    assert page.has_warnings is True
    assert page.has_error is True


def test_research_agent_page_defaults() -> None:
    """Optional page collections and results should have safe defaults."""

    page = ResearchAgentPageView(
        page_status=ResearchAgentPageStatus.READY,
        status_message="Ready for a research request.",
        request_form=ResearchRequestForm(),
    )

    assert page.request_id is None
    assert page.workflow_status is None
    assert page.sources == ()
    assert page.papers == ()
    assert page.evaluations == ()
    assert page.artifacts == ()
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
    assert summary.artifact_count == 0


def test_research_source_view_defaults() -> None:
    """Optional research source values should have safe defaults."""

    source = ResearchSourceView(
        source_name="semantic_scholar",
        source_id="paper-001",
        title="Example Paper",
    )

    assert source.source_url is None
    assert source.authors == ()
    assert source.publication_year is None


def test_paper_metadata_view_defaults() -> None:
    """Optional paper metadata values should have safe defaults."""

    paper = PaperMetadataView(
        source_id="paper-001",
        title="Example Paper",
    )

    assert paper.authors == ()
    assert paper.publication_year is None
    assert paper.abstract is None
    assert paper.venue is None
    assert paper.doi is None
    assert paper.source_url is None


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


def test_research_artifact_view_defaults() -> None:
    """Optional research artifact values should have safe defaults."""

    artifact = ResearchArtifactView(
        artifact_id="artifact-001",
        artifact_type=ResearchArtifactType.PAPER_SUMMARY,
        title="Paper Summary",
        content="Summary content.",
    )

    assert artifact.source_ids == ()
    assert artifact.has_sources is False


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
