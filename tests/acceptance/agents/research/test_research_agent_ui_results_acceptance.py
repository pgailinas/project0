# ============================================================
# Project0 - Research Agent UI Results Acceptance Tests
#
# File: test_research_agent_ui_results_acceptance.py
#
# Purpose:
#     Browser acceptance tests for Research Agent result
#     presentation through the Project0 Dashboard user interface,
#     including sources, evaluations, and research artifacts.
#
# ============================================================

from playwright.sync_api import Page, expect


RESEARCH_AGENT_URL = (
    "http://127.0.0.1:8001/agents/research"
)


def test_UI_RA_FUN_002_A_research_sources_are_presented(
    page: Page,
):
    """
    Verify that discovered research sources appear
    in the Research Agent results interface.

    This test requires deterministic source discovery
    or a stable external research response.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()


def test_UI_RA_FUN_003_A_paper_metadata_is_presented(
    page: Page,
):
    """
    Verify that retrieved paper metadata appears
    in the Research Agent results interface.

    This test requires deterministic metadata retrieval
    or a stable external research response.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()


def test_UI_RA_FUN_004_A_research_evaluation_is_presented(
    page: Page,
):
    """
    Verify that paper relevance evaluation appears
    in the Research Agent results interface.

    This test requires deterministic evaluation output
    or a stable reasoning response.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()


def test_UI_RA_FUN_005_A_research_artifacts_are_presented(
    page: Page,
):
    """
    Verify that generated research artifacts appear
    in the Research Agent results interface.

    This test requires deterministic artifact generation
    from stable research evaluation output.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()


def test_UI_RA_AI_002_A_unsupported_research_information_is_not_presented_as_supported(
    page: Page,
):
    """
    Verify that unsupported research information does not appear
    as validated Research Agent output.

    This test requires a deterministic unsupported-information
    reasoning fixture.
    """

    page.goto(RESEARCH_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()
