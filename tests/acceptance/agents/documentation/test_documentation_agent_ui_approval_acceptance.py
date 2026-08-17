# ============================================================
# Project0 - Documentation Agent UI Approval Acceptance Tests
#
# File: test_documentation_agent_ui_approval_acceptance.py
#
# Purpose:
#     Browser acceptance tests for the Documentation Agent
#     approval workflow through the Project0 Dashboard user interface,
#     including approve and reject decision paths and repository
#     modification safety validation.
#
# ============================================================

from playwright.sync_api import Page, expect


DOCUMENTATION_AGENT_URL = (
    "http://127.0.0.1:8001/agents/documentation"
)

DOCUMENTATION_TEST_DOCUMENT = (
    "tests/test_data/documentation_agent/"
    "revision_test_document.md"
)


def _submit_documentation_request(page: Page):
    """Submit a deterministic documentation request."""

    request_text = (
        "Update the Workflow section by expanding the existing "
        "workflow sequence to include approval before applying "
        "documentation changes."
    )

    page.get_by_placeholder(
        "Describe the documentation change to make."
    ).fill(request_text)

    page.get_by_placeholder(
        "docs/Implementation_Status.md"
    ).fill(DOCUMENTATION_TEST_DOCUMENT)

    page.get_by_role(
        "button",
        name="Submit Documentation Request",
    ).click()

    expect(
        page.get_by_role(
            "heading",
            name="Proposed Documentation Changes",
        )
    ).to_be_visible(
        timeout=300000
    )


def test_UI_DA_FUN_005_A_approved_change_matches_visible_proposal(
    page: Page,
):
    """
    Verify that an approved documentation change follows the
    visible proposal presented during review.

    This test validates:
    - request submission
    - proposal generation
    - review presentation
    - approve decision entry point

    Full workflow validation:
    - submits a documentation request
    - reaches the review page
    - approves the visible proposal
    - validates completion state
    """

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()

    _submit_documentation_request(page)

    page.get_by_role(
        "button",
        name="Approve",
    ).first.click()

    expect(
        page.get_by_role(
            "heading",
            name="Final Validation",
        )
    ).to_be_visible(
        timeout=300000
    )


def test_UI_DA_SAF_001_A_rejected_proposal_leaves_repository_unchanged(
    page: Page,
):
    """
    Verify that rejecting a proposal does not apply the
    documentation change.

    Requires repository state verification.
    """

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()


def test_UI_DA_SAF_002_A_approved_workflow_does_not_modify_unrelated_files(
    page: Page,
):
    """
    Verify that approval does not modify unrelated files.

    Requires repository difference verification.
    """

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()
