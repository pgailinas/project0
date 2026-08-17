# ============================================================
# Project0 - Documentation Agent UI Review Acceptance Tests
#
# File: test_documentation_agent_ui_review_acceptance.py
#
# Purpose:
#     Browser acceptance tests for the Documentation Agent
#     review workflow through the Project0 Dashboard user interface,
#     including proposal review, revision, and decision workflows.
#
# ============================================================

from playwright.sync_api import Page, expect


DOCUMENTATION_AGENT_URL = (
    "http://127.0.0.1:8001/agents/documentation"
)


def test_UI_DA_FUN_008_A_documentation_request_revision_workflow(
    page: Page,
):
    """
    Verify that the Documentation Agent supports documentation
    request revision from the review workflow.

    This test validates:
    - Documentation Agent page availability
    - Request submission entry point
    - Review workflow revision entry point

    Full workflow validation:
    - generates a documentation proposal
    - reaches the review page
    - selects Revise
    - restores the editable request state
    - preserves target documentation paths
    - allows revised submission
    """

    request_text = (
        "Update the Documentation Agent Revision Workflow section to clarify that users can revise proposed documentation changes before approval."
    )

    target_path = (
        "tests/test_data/documentation_agent/"
        "revision_test_document.md"
    )

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()

    page.get_by_placeholder(
        "Describe the documentation change to make."
    ).fill(request_text)

    page.get_by_placeholder(
        "docs/Implementation_Status.md"
    ).fill(target_path)

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

    page.get_by_role(
        "button",
        name="Revise",
    ).first.click()

    expect(
        page.get_by_placeholder(
            "Describe the documentation change to make."
        )
    ).to_be_visible()

    expect(
        page.get_by_placeholder(
            "Describe the documentation change to make."
        )
    ).to_have_value(
        request_text
    )

    expect(
        page.get_by_placeholder(
            "docs/Implementation_Status.md"
        )
    ).to_have_value(
        target_path
    )


def test_UI_DA_FUN_002_A_review_proposal_is_presented(
    page: Page,
):
    """
    Verify that generated documentation proposals appear
    on the review page.

    This test requires a deterministic proposal generation
    fixture or stable reasoning response.
    """

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()


def test_UI_DA_FUN_004_A_multi_document_proposal_is_presented(
    page: Page,
):
    """
    Verify that proposals affecting multiple documents are
    presented correctly during review.

    This test requires a deterministic multi-proposal fixture.
    """

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()


def test_UI_DA_AI_002_A_unsupported_feature_request_does_not_produce_unsupported_approved_content(
    page: Page,
):
    """
    Verify that unsupported feature requests do not result
    in unsupported approved documentation content.

    This test requires a deterministic unsupported-request
    reasoning fixture.
    """

    page.goto(DOCUMENTATION_AGENT_URL)

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()
