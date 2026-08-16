# ============================================================
# Project0 - Documentation Agent UI Request Acceptance Tests
#
# File: test_documentation_agent_browser_acceptance.py
#
# Purpose:
#     Browser acceptance tests for the Documentation Agent
#     request and general workflow through the Project0 Dashboard
#     user interface.
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


def test_UI_DA_FUN_001_documentation_request_form_accepts_input(
    page: Page,
):
    """
    Verify that the Documentation Agent request form accepts
    user input through the Project0 Dashboard UI.
    """

    page.goto(
        "http://127.0.0.1:8001/agents/documentation"
    )

    request_field = page.get_by_placeholder(
        "Describe the documentation change to make."
    )

    target_paths_field = page.get_by_placeholder(
        "docs/implementation_status.md"
    )

    request_text = (
        "Update the documentation to describe "
        "the new testing workflow."
    )

    target_paths = (
        "docs/agents/documentation/"
        "Documentation_Agent_Testing_Guide.md"
    )

    request_field.fill(request_text)
    target_paths_field.fill(target_paths)

    expect(request_field).to_have_value(request_text)
    expect(target_paths_field).to_have_value(target_paths)


def test_UI_DA_FUN_001_documentation_request_submission_starts_processing(
    page: Page,
):
    """
    Verify that submitting a Documentation Agent request starts
    the processing workflow through the Project0 Dashboard UI.
    """

    page.goto(
        "http://127.0.0.1:8001/agents/documentation"
    )

    request_field = page.get_by_placeholder(
        "Describe the documentation change to make."
    )

    target_paths_field = page.get_by_placeholder(
        "docs/implementation_status.md"
    )

    request_field.fill(
        "Update the documentation to describe "
        "the new testing workflow."
    )

    target_paths_field.fill(
        "docs/agents/documentation/"
        "Documentation_Agent_Testing_Guide.md"
    )

    page.evaluate(
        """
        () => {
            const form = document.getElementById(
                "documentation-request-form"
            );

            form.submit = () => {};
        }
        """
    )

    page.get_by_role(
        "button",
        name="Submit Documentation Request",
    ).click()

    expect(
        page.get_by_role(
            "button",
            name="Processing...",
        )
    ).to_be_visible(
        timeout=10000
    )

    expect(
        page.get_by_text(
            "Running AI reasoning and validation..."
        )
    ).to_be_visible(
        timeout=10000
    )


# Planned browser acceptance cases:
#
# UI-DA-SAF-003-A - Invalid Request Is Reported Safely
# UI-DA-FUN-001-D - Visible Workflow Result Is Presented
# UI-DA-FUN-008-A - Documentation Request Revision Workflow
