# ============================================================
# Project0 - Documentation Agent
#
# File: test_documentation_agent_browser_acceptance.py
#
# Purpose:
#     Browser acceptance tests for the Documentation Agent
#     through the Project0 Dashboard user interface.
#
# ============================================================

from playwright.sync_api import Page, expect


def test_UI_DA_FUN_001_documentation_agent_page_renders(
    page: Page,
):
    """
    Verify that the Documentation Agent request interface is
    available through the actual Project0 Dashboard UI.
    """

    print("Opening Documentation Agent page")

    page.goto(
        "http://127.0.0.1:8001/agents/documentation"
    )

    print("Verifying Documentation Agent heading")

    expect(
        page.get_by_role(
            "heading",
            name="Documentation Agent",
        )
    ).to_be_visible()

    print("Verifying Documentation Request field")

    expect(
        page.get_by_label("Documentation Request")
    ).to_be_visible()

    print("Verifying Target Documentation Paths field")

    expect(
        page.get_by_label("Target Documentation Paths")
    ).to_be_visible()

    print("Verifying Submit Documentation Request button")

    expect(
        page.get_by_role(
            "button",
            name="Submit Documentation Request",
        )
    ).to_be_visible()
