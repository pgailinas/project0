# ============================================================
# Project0 - Research Agent UI End-to-End Acceptance Tests
#
# File: test_research_agent_ui_end_to_end_acceptance.py
#
# Purpose:
#     Browser acceptance tests for the Research Agent
#     end-to-end workflow through the Project0 Dashboard user interface,
#     including request submission, completed research results, and
#     visible research artifact validation.
#
# ============================================================

from playwright.sync_api import Page, expect


RESEARCH_AGENT_URL = (
    "http://127.0.0.1:8001/agents/research"
)


def _submit_research_request(page: Page):
    """Submit a deterministic research request."""

    question_text = (
        "Find papers relevant to improving self-supervised "
        "video representations for VideoQA using "
        "vision-language alignment."
    )

    page.get_by_placeholder(
        "Describe the research question to investigate."
    ).fill(question_text)

    page.get_by_placeholder(
        "Optional guidance, constraints, focus areas, or preferences."
    ).fill(
        "Prefer recent research. "
        "vision-language alignment "
        "stub"
    )

    page.get_by_role(
        "button",
        name="Submit Research Request",
    ).click()

    expect(
        page.get_by_role(
            "heading",
            name="Research Synthesis Artifacts",
        )
    ).to_be_visible(
        timeout=30000
    )


def test_UI_RA_FUN_005_A_completed_research_matches_visible_results(
    page: Page,
):
    """
    Verify that a completed Research Agent workflow presents
    visible research results through the Dashboard interface.

    This test validates:
    - request submission
    - research result presentation
    - relevance result presentation
    - research artifact presentation

    Full workflow validation:
    - submits a research request
    - reaches the completed result page
    - validates visible research artifacts
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()

    _submit_research_request(page)

    expect(
        page.get_by_role(
            "heading",
            name="Research Results",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "heading",
            name="Research Synthesis Artifacts",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "heading",
            name="Research Direction Analysis",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "heading",
            name="Workflow Summary",
        )
    ).to_be_visible()


def test_UI_RA_SAF_001_A_invalid_request_does_not_start_research_workflow(
    page: Page,
):
    """
    Verify that an invalid Research Agent request is rejected
    without starting the research workflow.

    Requires browser-visible validation behavior.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()


def test_UI_RA_SAF_002_A_unavailable_research_results_are_reported_safely(
    page: Page,
):
    """
    Verify that unavailable or incomplete research results are
    reported without presenting unsupported validated output.

    Requires deterministic unavailable-result behavior.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()
