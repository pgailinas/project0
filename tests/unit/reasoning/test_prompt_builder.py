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
from project0.models.skill_models import SkillDefinition
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
        "skill_names": (),
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
    assert "Target Paths identify the only documents that may be changed" in instructions
    assert "read-only reference evidence" in instructions
    assert "must never be returned as a proposed change document_path" in instructions
    assert "Ground Truth Source content is always read-only evidence" in instructions
    assert "proposed_content must contain only" in instructions
    assert (
        "For an update operation, proposed_content must contain the "
        "complete resulting document"
        not in instructions
    )
    assert "Identify the target location using section and anchor_text" in instructions
    assert "Preserve existing repository content that is unrelated" in instructions
    assert "Warnings must be directly supported" in instructions
    assert "Do not report duplicate definitions" in instructions
    assert "If a warning cannot be verified" in instructions
    assert (
        "rewrite, reorder, normalize, or reproduce unrelated Markdown content"
        in instructions
    )
    assert "minimum textual modification" in instructions
    assert "actual Markdown text to apply" in instructions
    assert "not instructions, a plan, or a description" in instructions
    assert "Do not return directives such as Add, Describe, Explain" in instructions
    assert "do not use the level-one document title" in instructions
    assert "directly belongs to that section" in instructions
    assert "do not choose the closest available heading" in instructions
    assert "Do not reproduce the surrounding document or section" in instructions
    assert "only the new list item or items" in instructions
    assert (
        "existing headings, metadata, unchanged list items, or surrounding Markdown"
        in instructions
    )
    assert "complete new document" in instructions
    assert "delete operation" in instructions
    assert (
        "proposed_content must contain the content to remove or be empty "
        "when no content is required"
        in instructions
    )
    assert "decimal number between 0.0 and 1.0" in instructions
    assert "Do not use percentages" in instructions
    assert "conforms exactly to the supplied JSON schema" in instructions


def test_gap_analysis_prompt_is_comparison_only() -> None:
    """Stage 1 prompt performs gap detection without proposing edits."""

    request = ReasoningRequest(
        objective="Synchronize documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Contract\n"
            "Existing prose.\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "VALUE = 1\n"
        ),
        workflow_type="documentation_gap_analysis",
        target_paths=(Path("docs/Example.md"),),
    )

    provider_request = PromptBuilder().build_prompt(request)

    assert "gap-analysis stage" in provider_request.system_instructions
    assert "Perform Stage 1 only" in provider_request.system_instructions
    assert "Do not propose wording" in provider_request.system_instructions
    assert "Do not summarize the source" in (
        provider_request.system_instructions
    )
    assert "Do not infer performance, efficiency" in (
        provider_request.system_instructions
    )
    assert "Evaluate the target document's actual claims first" in (
        provider_request.system_instructions
    )
    assert "is not a documentation gap merely because" in (
        provider_request.system_instructions
    )
    assert "smallest set of non-overlapping gaps" in (
        provider_request.system_instructions
    )
    assert "TARGET DOCUMENTATION CLAIM CANDIDATES" in (
        provider_request.system_instructions
    )
    assert "return only those contradiction gaps" in (
        provider_request.system_instructions
    )
    assert "a source file path by itself is not sufficient evidence" in (
        provider_request.system_instructions
    )
    assert "Stage 1 Gap Analysis Rule:" in provider_request.user_prompt
    assert "target's existing claims directly" in provider_request.user_prompt
    assert "smallest set of non-overlapping gaps" in provider_request.user_prompt
    assert "TARGET DOCUMENTATION CLAIM CANDIDATES first" in (
        provider_request.user_prompt
    )
    assert "return only contradiction gaps" in provider_request.user_prompt
    assert "a source path alone is not evidence" in provider_request.user_prompt
    assert "Do not propose edits" in provider_request.user_prompt
    assert "Target Documentation Paths:" in provider_request.user_prompt


def test_gap_analysis_schema_uses_dedicated_gap_contract() -> None:
    """Stage 1 schema exposes source-grounded gaps, not generic impacts."""

    request = ReasoningRequest(
        objective="Synchronize documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Interface Contract\n"
            "Existing prose.\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "VALUE = 1\n"
        ),
        workflow_type="documentation_gap_analysis",
        target_paths=(Path("docs/Example.md"),),
    )

    schema = PromptBuilder().build_prompt(request).response_schema

    assert schema["required"] == [
        "summary",
        "gaps",
        "assumptions",
        "warnings",
    ]
    assert set(schema["properties"]) == {
        "summary",
        "gaps",
        "assumptions",
        "warnings",
    }
    assert "impacts" not in schema["properties"]
    assert "proposed_changes" not in schema["properties"]

    gap_schema = schema["properties"]["gaps"]["items"]

    assert gap_schema["required"] == [
        "document_path",
        "section",
        "gap",
        "source_evidence",
        "confidence",
    ]
    assert set(gap_schema["properties"]) == {
        "document_path",
        "section",
        "gap",
        "source_evidence",
        "confidence",
    }
    assert gap_schema["properties"]["document_path"]["enum"] == [
        "docs/Example.md"
    ]
    assert gap_schema["properties"]["section"]["anyOf"][0] == {
        "type": "string",
        "enum": ["Interface Contract"],
    }
    assert "Smallest non-overlapping set" in (
        schema["properties"]["gaps"]["description"]
    )
    assert "current abstraction level" in (
        schema["properties"]["gaps"]["description"]
    )
    assert "concrete authoritative source behavior" in (
        gap_schema["properties"]["source_evidence"]["description"]
    )
    assert "source file path by itself is not sufficient evidence" in (
        gap_schema["properties"]["source_evidence"]["description"]
    )


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
    assert (
        "Permitted proposed_changes document_path values:\n"
        "- docs/Architecture.md\n"
        "- docs/Design.md\n"
        "Every proposed_changes item must use exactly one "
        "of the permitted document_path values above."
        in provider_request.user_prompt
    )


def test_build_prompt_includes_source_grounded_section_guidance() -> None:
    """Source-grounded prompts enumerate valid target sections."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Existing Interface Contract\n"
            "Body text.\n"
            "### Validation Behavior\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "## Source Heading\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    builder = PromptBuilder()

    user_prompt = builder.build_prompt(
        reasoning_request
    ).user_prompt

    guidance_block = user_prompt.split(
        "Permitted Existing Target Sections:\n",
        1,
    )[1].split(
        "\n\nRepository Context:\n",
        1,
    )[0]

    assert (
        "- Existing Interface Contract\n"
        "- Validation Behavior"
        in guidance_block
    )
    assert "Source Heading" not in guidance_block
    assert "Choose a section only when the proposed change" in user_prompt
    assert "directly belongs to that section's existing subject matter" in user_prompt
    assert "Do not choose a section merely because it is the closest" in user_prompt
    assert "return section as null" in user_prompt
    assert "Source-Grounded Synchronization Rule:" in user_prompt
    assert "Propose documentation changes only for source-established gaps" in (
        user_prompt
    )
    assert "Do not recommend new implementation fields" in user_prompt


def test_build_prompt_omits_section_guidance_for_generic_context() -> None:
    """Generic prompts should preserve prior user-prompt behavior."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "# Example\n"
            "## Existing Interface Contract\n"
        ),
    )

    builder = PromptBuilder()

    user_prompt = builder.build_prompt(
        reasoning_request
    ).user_prompt

    assert "Permitted Existing Target Sections:" not in user_prompt


def test_build_prompt_omits_section_guidance_without_target_subsections() -> None:
    """Source-grounded title-only targets should not list sections."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "## Source Heading\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    builder = PromptBuilder()

    user_prompt = builder.build_prompt(
        reasoning_request
    ).user_prompt

    assert "Permitted Existing Target Sections:" not in user_prompt


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
    assert (
        "Permitted proposed_changes document_path values:"
        not in provider_request.user_prompt
    )


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
        "anchor_text",
        "edit_type",
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

    assert "documentation_meaning" not in change_schema["required"]
    assert "documentation_meaning" in change_schema["properties"]
    assert "anchor_text" in change_schema["properties"]

    assert (
        change_schema["properties"]["edit_type"]["enum"]
        == [
            "insert",
            "replace",
            "delete",
        ]
    )


def test_source_grounded_response_schema_requires_documentation_meaning() -> None:
    """Source-grounded changes require an explicit semantic translation."""

    reasoning_request = ReasoningRequest(
        objective="Synchronize documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Interface Contract\n"
            "Existing prose.\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "class Example:\n"
            "    pass\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    change_schema = (
        PromptBuilder().build_prompt(reasoning_request)
        .response_schema["properties"]["proposed_changes"]["items"]
    )

    assert "documentation_meaning" in change_schema["required"]
    meaning_schema = change_schema["properties"]["documentation_meaning"]
    assert meaning_schema["type"] == "string"
    assert "documentation meaning derived from" in (
        meaning_schema["description"]
    )
    assert "Do not copy source syntax" in meaning_schema["description"]
    assert "recommend implementation changes" in meaning_schema["description"]
    assert "invent new source behavior" in meaning_schema["description"]


def test_response_schema_limits_proposed_change_paths_to_targets() -> None:
    """Target paths should constrain proposed change document paths."""

    reasoning_request = ReasoningRequest(
        objective="Update selected documentation.",
        context="Repository context.",
        target_paths=(
            Path("docs/Architecture.md"),
            Path("docs/Design.md"),
        ),
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    document_path_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["document_path"]
    )

    assert document_path_schema == {
        "type": "string",
        "enum": [
            "docs/Architecture.md",
            "docs/Design.md",
        ],
    }


def test_response_schema_leaves_proposed_change_path_open_without_targets() -> None:
    """Absent target paths should preserve the generic path schema."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    document_path_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["document_path"]
    )

    assert document_path_schema == {
        "type": "string",
    }


def test_response_schema_does_not_limit_impact_paths_to_targets() -> None:
    """Impact reporting may still identify documentation outside targets."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
        target_paths=(
            Path("docs/Architecture.md"),
        ),
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    impact_path_schema = (
        schema["properties"]["impacts"]["items"]
        ["properties"]["document_path"]
    )

    assert impact_path_schema == {
        "type": "string",
    }


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
        "description": (
            "Exact existing Markdown heading text from the supplied target "
            "document, excluding leading # characters, or null when no "
            "existing heading reliably identifies the update location."
        ),
        "anyOf": [
            {
                "type": "string",
            },
            {
                "type": "null",
            },
        ]
    }




def test_extract_markdown_headings_preserves_generic_context_behavior() -> None:
    """Generic context still includes level-one and subsection headings."""

    headings, source_grounded = PromptBuilder._extract_markdown_headings(
        "# Example\n## Existing Interface Contract\n"
    )

    assert source_grounded is False
    assert headings == (
        "Example",
        "Existing Interface Contract",
    )


def test_response_schema_constrains_section_to_context_headings() -> None:
    """Verify section values are limited to exact supplied headings."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "--- Document: docs/Example.md ---\n"
            "# Example\n"
            "## Existing Interface Contract\n"
            "Body text.\n"
            "### Validation Behavior\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    section_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["section"]
    )

    assert section_schema["anyOf"][0] == {
        "type": "string",
        "enum": [
            "Example",
            "Existing Interface Contract",
            "Validation Behavior",
        ],
    }
    assert section_schema["anyOf"][1] == {
        "type": "null",
    }


def test_response_schema_uses_only_source_grounded_target_subheadings() -> None:
    """Source-grounded section enum excludes source headings and target H1."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Existing Interface Contract\n"
            "Body text.\n"
            "### Validation Behavior\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "# Source Comment That Looks Like Markdown\n"
            "## Another Source Comment\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    section_values = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["section"]["anyOf"][0]["enum"]
    )

    assert section_values == [
        "Existing Interface Contract",
        "Validation Behavior",
    ]


def test_response_schema_source_grounded_target_with_only_h1_allows_null_only() -> None:
    """Source-grounded target title alone should not become an edit section."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "## Source Heading\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    section_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["section"]
    )

    assert section_schema["anyOf"][0] == {
        "type": "string",
        "enum": [],
    }
    assert section_schema["anyOf"][1] == {
        "type": "null",
    }


def test_response_schema_deduplicates_context_headings() -> None:
    """Verify repeated headings appear only once in the section enum."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context=(
            "# Example\n"
            "## Shared Section\n"
            "## Shared Section\n"
        ),
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    section_values = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["section"]["anyOf"][0]["enum"]
    )

    assert section_values == [
        "Example",
        "Shared Section",
    ]


def test_response_schema_requires_concrete_proposed_content() -> None:
    """Verify proposed content schema requires concrete Markdown text."""

    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    proposed_content_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["proposed_content"]
    )

    assert proposed_content_schema["type"] == "string"
    assert (
        "Concrete Markdown text to apply"
        in proposed_content_schema["description"]
    )
    assert (
        "Must not be instructions"
        in proposed_content_schema["description"]
    )


def test_source_grounded_response_schema_guides_target_form() -> None:
    """Source-grounded content should follow the existing target form."""

    reasoning_request = ReasoningRequest(
        objective="Synchronize documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Interface Contract\n"
            "Existing prose.\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "class Example:\n"
            "    pass\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    schema = PromptBuilder().build_prompt(
        reasoning_request
    ).response_schema

    proposed_content_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["proposed_content"]
    )
    description = proposed_content_schema["description"]

    assert "existing form of the affected target section" in description
    assert "Translate authoritative implementation evidence" in description
    assert "documentation prose when the target section is prose" in description
    assert "Do not introduce a fenced source-code block" in description
    assert "already contains comparable fenced source code" in description
    assert "Must not be instructions, a plan, a recommendation" in description
    assert "behavior established by the authoritative source" in description


def test_source_grounded_response_schema_rejects_design_rationale() -> None:
    """Source-grounded rationale is limited to documentation synchronization."""

    reasoning_request = ReasoningRequest(
        objective="Synchronize documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Interface Contract\n"
            "Existing prose.\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "class Example:\n"
            "    pass\n"
        ),
        target_paths=(Path("docs/Example.md"),),
    )

    change_schema = (
        PromptBuilder().build_prompt(reasoning_request)
        .response_schema["properties"]["proposed_changes"]["items"]
    )

    rationale_description = (
        change_schema["properties"]["rationale"]["description"]
    )

    assert "authoritative source evidence" in rationale_description
    assert "existing target documentation" in rationale_description
    assert "Do not recommend implementation changes" in rationale_description
    assert "new source behavior" in rationale_description


def test_response_schema_allows_nullable_anchor_text() -> None:
    """Verify proposed change anchor text may be string or null."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    anchor_schema = (
        schema["properties"]["proposed_changes"]["items"]
        ["properties"]["anchor_text"]
    )

    assert anchor_schema == {
        "description": (
            "Exact verbatim text from the supplied target document to use "
            "as an edit anchor, or null when no reliable anchor exists."
        ),
        "anyOf": [
            {
                "type": "string",
            },
            {
                "type": "null",
            },
        ]
    }


def test_response_schema_requires_grounded_warnings() -> None:
    """Verify warning schema describes context-grounded warnings."""

    reasoning_request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    builder = PromptBuilder()

    schema = builder.build_prompt(
        reasoning_request
    ).response_schema

    warnings_schema = schema["properties"]["warnings"]

    assert warnings_schema["type"] == "array"
    assert warnings_schema["items"] == {
        "type": "string",
    }
    assert (
        "directly supported by the supplied context"
        in warnings_schema["description"]
    )
    assert (
        "Omit warnings that cannot be verified"
        in warnings_schema["description"]
    )


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


def test_build_prompt_includes_active_skill_instructions() -> None:
    """Loaded Agent Skill instructions are added to the system prompt."""

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path("skills/strict-documentation-editor/SKILL.md"),
        instructions=(
            "# Strict Documentation Editing\n"
            "Apply the minimum textual modification."
        ),
    )
    reasoning_request = ReasoningRequest(
        objective="Update documentation.",
        context="Repository context.",
        skills=(skill,),
    )

    provider_request = PromptBuilder().build_prompt(reasoning_request)

    assert (
        "=== ACTIVE AGENT SKILL: strict-documentation-editor ==="
        in provider_request.system_instructions
    )
    assert (
        "# Strict Documentation Editing\n"
        "Apply the minimum textual modification."
        in provider_request.system_instructions
    )
    assert provider_request.metadata["skill_names"] == (
        "strict-documentation-editor",
    )


def test_build_prompt_omits_skill_section_when_no_skills_are_active() -> None:
    """Existing prompt behavior is preserved without active skills."""

    provider_request = PromptBuilder().build_prompt(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
    )

    assert "=== ACTIVE AGENT SKILL:" not in (
        provider_request.system_instructions
    )
    assert provider_request.metadata["skill_names"] == ()


def test_source_grounded_prompt_avoids_redundant_target_path_listing() -> None:
    """Structured source-grounded context should not repeat target paths."""

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path("skills/strict-documentation-editor/SKILL.md"),
        instructions="Apply the minimum textual modification.",
    )
    reasoning_request = ReasoningRequest(
        objective="Synchronize documentation.",
        context=(
            "=== TARGET DOCUMENTATION ===\n"
            "Path: docs/Example.md\n"
            "# Example\n"
            "## Interface Contract\n"
            "Existing details.\n"
            "\n"
            "=== AUTHORITATIVE SOURCE ===\n"
            "Path: src/project0/example.py\n"
            "class Example:\n"
            "    pass\n"
        ),
        workflow_type="documentation_update",
        target_paths=(Path("docs/Example.md"),),
        skills=(skill,),
    )

    provider_request = PromptBuilder().build_prompt(reasoning_request)

    assert "Target Paths:" not in provider_request.user_prompt
    assert (
        "Permitted proposed_changes document_path values:"
        not in provider_request.user_prompt
    )
    assert (
        provider_request.response_schema["properties"]
        ["proposed_changes"]["items"]["properties"]["document_path"]["enum"]
        == ["docs/Example.md"]
    )


def test_active_skill_uses_concise_system_instructions() -> None:
    """Active skills own persistent strict-editing policy."""

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path("skills/strict-documentation-editor/SKILL.md"),
        instructions="Apply the minimum textual modification.",
    )

    instructions = PromptBuilder().build_prompt(
        ReasoningRequest(
            objective="Synchronize documentation.",
            context="Repository context.",
            target_paths=(Path("docs/Example.md"),),
            skills=(skill,),
        )
    ).system_instructions

    assert "The supplied response schema constrains" in instructions
    assert "Source-grounded documentation work is synchronization" in instructions
    assert "Do not propose new source fields" in instructions
    assert "does not establish a documentation gap" in instructions
    assert "Target Paths identify the only documents" not in instructions
    assert "Do not return directives such as Add, Describe, Explain" not in (
        instructions
    )
    assert "=== ACTIVE AGENT SKILL: strict-documentation-editor ===" in (
        instructions
    )
