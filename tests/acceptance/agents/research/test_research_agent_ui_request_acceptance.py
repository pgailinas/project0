# ============================================================
# Project0 - Research Agent UI Request Acceptance Tests
#
# File: test_research_agent_ui_request_acceptance.py
#
# Purpose:
#     Browser acceptance tests for the Research Agent
#     request and general workflow through the Project0 Dashboard
#     user interface.
#
# ============================================================

from playwright.sync_api import Page, expect


def test_UI_RA_FUN_001_research_agent_page_renders(
    page: Page,
):
    """
    Verify that the Research Agent request interface is
    available through the actual Project0 Dashboard UI.
    """

    print("Opening Research Agent page")

    page.goto(
        "http://127.0.0.1:8001/agents/research"
    )

    print("Verifying Research Agent heading")

    expect(
        page.get_by_role(
            "heading",
            name="Research Agent",
        )
    ).to_be_visible()

    print("Verifying Research Question field")

    expect(
        page.get_by_label("Research question")
    ).to_be_visible()

    print("Verifying Research Guidance field")

    expect(
        page.get_by_label("Research guidance")
    ).to_be_visible()

    print("Verifying Focus Areas field")

    
    print("Verifying Submit Research Request button")

    expect(
        page.get_by_role(
            "button",
            name="Submit Research Request",
        )
    ).to_be_visible()


def test_UI_RA_FUN_001_research_request_form_accepts_input(
    page: Page,
):
    """
    Verify that the Research Agent request form accepts
    user input through the Project0 Dashboard UI.
    """

    page.goto(
        "http://127.0.0.1:8001/agents/research"
    )

    question_field = page.get_by_placeholder(
        "Describe the research question to investigate."
    )

    guidance_field = page.get_by_placeholder(
        "Optional guidance, constraints, focus areas, or preferences."
    )

    question_text = (
        "Find papers relevant to improving self-supervised "
        "video representations for VideoQA."
    )

    guidance_text = (
        "Prefer recent research. "
        "vision-language alignment "
        "stub"
    )

    question_field.fill(question_text)
    guidance_field.fill(guidance_text)
    expect(question_field).to_have_value(question_text)
    expect(guidance_field).to_have_value(guidance_text)


def test_UI_RA_FUN_001_research_request_submission_starts_processing(
    page: Page,
):
    """
    Verify that submitting a Research Agent request starts
    the processing workflow through the Project0 Dashboard UI.
    """

    page.goto(
        "http://127.0.0.1:8001/agents/research"
    )

    question_field = page.get_by_placeholder(
        "Describe the research question to investigate."
    )

    guidance_field = page.get_by_placeholder(
        "Optional guidance, constraints, focus areas, or preferences."
    )

    question_field.fill(
        "Find papers relevant to improving self-supervised "
        "video representations for VideoQA."
    )

    guidance_field.fill(
        "Prefer recent research."
    )

    page.evaluate(
        """
        () => {
            const form = document.getElementById(
                "research-request-form"
            );

            form.submit = () => {};
        }
        """
    )

    page.get_by_role(
        "button",
        name="Submit Research Request",
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
            "Searching and evaluating research..."
        )
    ).to_be_visible(
        timeout=10000
    )


# Planned browser acceptance cases:
#
# UI-RA-SAF-001-A - Invalid Research Request Is Reported Safely
# UI-RA-FUN-001-D - Visible Research Results Are Presented
