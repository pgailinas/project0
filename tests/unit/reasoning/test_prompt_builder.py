# ============================================================
# Project0 - Prompt Builder Tests
#
# File: test_prompt_builder.py
#
# Purpose:
#     Verify deterministic provider-neutral prompt construction
#     for Project0 reasoning services.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.models.reasoning_models import ReasoningRequest
from project0.reasoning.prompt_builder import PromptBuilder


def test_prompt_builder_defaults() -> None:
    """Verify default prompt builder configuration."""

    builder = PromptBuilder()

    assert builder.model_name is None
    assert builder.temperature == 0.0
    assert builder.maximum_output_tokens == 4096


def test_build_prompt_creates_provider_request() -> None:
    """Verify creation of a provider-neutral request."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
    )

    builder = PromptBuilder(
        model_name="qwen3:8b",
        temperature=0.2,
        maximum_output_tokens=2048,
    )

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert provider_request.model_name == "qwen3:8b"
    assert provider_request.temperature == 0.2
    assert provider_request.maximum_output_tokens == 2048
    assert provider_request.request_id


def test_build_prompt_preserves_reasoning_request_metadata() -> None:
    """Verify reasoning request metadata is propagated."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
        workflow_type="documentation_update",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert provider_request.metadata == {
        "reasoning_request_id": reasoning_request.request_id,
        "workflow_type": "documentation_update",
    }


def test_build_prompt_includes_system_instructions() -> None:
    """Verify required system instructions are present."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    instructions = provider_request.system_instructions

    assert (
        "Project0 Documentation Agent reasoning service"
        in instructions
    )
    assert "Analyze only the supplied repository context" in instructions
    assert "Do not modify source code" in instructions
    assert "Preserve repository-relative paths" in instructions
    assert "conforms exactly to the supplied JSON schema" in instructions


def test_build_prompt_includes_objective_and_context() -> None:
    """Verify objective and repository context are included."""

    reasoning_request = ReasoningRequest(
        objective="Identify impacted documentation.",
        context=(
            "--- Document: docs/Example.md ---\n"
            "# Example\n"
        ),
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert provider_request.user_prompt == (
        "Objective:\n"
        "Identify impacted documentation.\n"
        "\n"
        "Repository Context:\n"
        "--- Document: docs/Example.md ---\n"
        "# Example"
    )


def test_build_prompt_includes_workflow_type() -> None:
    """Verify workflow type is included when supplied."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
        workflow_type="documentation_update",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert (
        "Workflow Type:\n"
        "documentation_update"
        in provider_request.user_prompt
    )


def test_build_prompt_omits_workflow_type_when_missing() -> None:
    """Verify workflow type section is omitted when absent."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert "Workflow Type:" not in provider_request.user_prompt


def test_build_prompt_includes_target_paths() -> None:
    """Verify target repository paths are included."""

    reasoning_request = ReasoningRequest(
        objective="Update selected documentation.",
        context="Repository context.",
        target_paths=(
            Path("docs/Architecture.md"),
            Path("docs/Design.md"),
        ),
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert (
        "Target Paths:\n"
        "- docs/Architecture.md\n"
        "- docs/Design.md"
        in provider_request.user_prompt
    )


def test_build_prompt_omits_target_paths_when_empty() -> None:
    """Verify target path section is omitted when empty."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert "Target Paths:" not in provider_request.user_prompt


def test_build_prompt_includes_constraints() -> None:
    """Verify reasoning constraints are included."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context="Repository context.",
        constraints=(
            "Preserve Markdown style.",
            "Do not modify source code.",
        ),
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert (
        "Constraints:\n"
        "- Preserve Markdown style.\n"
        "- Do not modify source code."
        in provider_request.user_prompt
    )


def test_build_prompt_omits_constraints_when_empty() -> None:
    """Verify constraints section is omitted when empty."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert "Constraints:" not in provider_request.user_prompt


def test_build_prompt_strips_outer_whitespace() -> None:
    """Verify objective and context outer whitespace is removed."""

    reasoning_request = ReasoningRequest(
        objective="  Analyze documentation.  ",
        context="\n\nRepository context.\n\n",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    assert (
        "Objective:\n"
        "Analyze documentation."
        in provider_request.user_prompt
    )
    assert provider_request.user_prompt.endswith(
        "Repository context."
    )


def test_response_schema_has_required_top_level_properties() -> None:
    """Verify required response schema properties."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    provider_request = builder.build_prompt(
        reasoning_request
    )

    schema = provider_request.response_schema

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "summary",
        "impacts",
        "proposed_changes",
        "assumptions",
        "warnings",
    ]

    assert set(schema["properties"]) == {
        "summary",
        "impacts",
        "proposed_changes",
        "assumptions",
        "warnings",
    }


def test_response_schema_defines_impact_shape() -> None:
    """Verify documentation impact schema shape."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    impact_schema = schema["properties"]["impacts"]["items"]

    assert impact_schema["type"] == "object"
    assert impact_schema["additionalProperties"] is False
    assert impact_schema["required"] == [
        "document_path",
        "summary",
        "rationale",
        "confidence",
    ]

    assert set(impact_schema["properties"]) == {
        "document_path",
        "summary",
        "rationale",
        "confidence",
    }


def test_response_schema_defines_change_shape() -> None:
    """Verify proposed documentation change schema shape."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    change_schema = (
        schema["properties"]["proposed_changes"]["items"]
    )

    assert change_schema["type"] == "object"
    assert change_schema["additionalProperties"] is False
    assert change_schema["required"] == [
        "document_path",
        "operation",
        "rationale",
        "proposed_content",
        "section",
        "confidence",
    ]

    assert (
        change_schema["properties"]["operation"]["enum"]
        == [
            "create",
            "update",
            "delete",
        ]
    )


def test_response_schema_allows_nullable_confidence() -> None:
    """Verify confidence may be a number or null."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    confidence_schema = (
        schema["properties"]["impacts"]["items"]
        ["properties"]["confidence"]
    )

    assert confidence_schema == {
        "anyOf": [
            {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            {
                "type": "null",
            },
        ]
    }


def test_response_schema_allows_nullable_section() -> None:
    """Verify proposed change section may be string or null."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    section_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["section"]
    )

    assert section_schema == {
        "anyOf": [
            {
                "type": "string",
            },
            {
                "type": "null",
            },
        ]
    }


def test_build_prompt_is_deterministic_except_request_id() -> None:
    """Verify repeated prompt content and schema are deterministic."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
        workflow_type="documentation_update",
        target_paths=(Path("docs/Example.md"),),
        constraints=("Preserve style.",),
    )

    builder = PromptBuilder(
        model_name="qwen3:8b",
        temperature=0.0,
        maximum_output_tokens=4096,
    )

    first_request = builder.build_prompt(
        reasoning_request
    )
    second_request = builder.build_prompt(
        reasoning_request
    )

    assert (
        first_request.system_instructions
        == second_request.system_instructions
    )
    assert first_request.user_prompt == second_request.user_prompt
    assert (
        first_request.response_schema
        == second_request.response_schema
    )
    assert first_request.model_name == second_request.model_name
    assert first_request.temperature == second_request.temperature
    assert (
        first_request.maximum_output_tokens
        == second_request.maximum_output_tokens
    )
    assert first_request.metadata == second_request.metadata
    assert first_request.request_id != second_request.request_id


def test_response_schema_instances_are_independent() -> None:
    """Verify provider requests receive independent schema dictionaries."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    first_request = builder.build_prompt(
        reasoning_request
    )
    second_request = builder.build_prompt(
        reasoning_request
    )

    assert (
        first_request.response_schema
        is not second_request.response_schema
    )
