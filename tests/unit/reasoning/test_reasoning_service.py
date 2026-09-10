# ============================================================
# Project0 - Reasoning Service Tests
#
# File: test_reasoning_service.py
#
# Purpose:
#     Verify reasoning orchestration, structured output parsing,
#     warning handling, and failure conversion.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    DocumentationEditType,
    ProviderRequest,
    ProviderResponse,
    ReasoningRequest,
    ReasoningStatus,
)
from project0.models.skill_models import SkillDefinition
from project0.reasoning.reasoning_service import ReasoningService


class StubPromptBuilder:
    """Provide deterministic prompt-builder behavior for testing."""

    def __init__(
        self,
        provider_request: ProviderRequest,
        error: Exception | None = None,
    ) -> None:
        """Initialize the configured provider request or error."""

        self.provider_request = provider_request
        self.error = error
        self.requests: list[ReasoningRequest] = []

    def build_prompt(
        self,
        request: ReasoningRequest,
    ) -> ProviderRequest:
        """Return the configured provider request or error."""

        self.requests.append(request)

        if self.error is not None:
            raise self.error

        return self.provider_request


class StubProvider:
    """Provide deterministic provider behavior for testing."""

    def __init__(
        self,
        response: ProviderResponse,
        error: Exception | None = None,
    ) -> None:
        """Initialize the configured provider response or error."""

        self.response = response
        self.error = error
        self.requests: list[ProviderRequest] = []

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Return the configured provider response or error."""

        self.requests.append(request)

        if self.error is not None:
            raise self.error

        return self.response


def create_reasoning_request() -> ReasoningRequest:
    """Create a reasoning request for testing."""

    return ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
        workflow_type="documentation_update",
        target_paths=(
            Path("docs/Documentation_Agent_Design.md"),
        ),
        constraints=("Preserve Markdown style.",),
    )


def create_provider_request() -> ProviderRequest:
    """Create a provider request for testing."""

    return ProviderRequest(
        system_instructions="System instructions.",
        user_prompt="User prompt.",
        response_schema={
            "type": "object",
        },
        model_name="qwen3:8b",
    )


def create_valid_provider_response(
    warnings: tuple[str, ...] = (),
    response_warnings: list[str] | None = None,
) -> ProviderResponse:
    """Create a valid structured provider response."""

    return ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
        structured_output={
            "summary": "One document requires an update.",
            "impacts": [
                {
                    "document_path": (
                        "docs/Documentation_Agent_Design.md"
                    ),
                    "summary": (
                        "The design document requires an update."
                    ),
                    "rationale": (
                        "The Reasoning Service was implemented."
                    ),
                    "confidence": 0.95,
                }
            ],
            "proposed_changes": [
                {
                    "document_path": (
                        "docs/Documentation_Agent_Design.md"
                    ),
                    "operation": "update",
                    "rationale": (
                        "Document the Reasoning Service."
                    ),
                    "documentation_meaning": (
                        "The Reasoning Service is part of the documented "
                        "component contract."
                    ),
                    "proposed_content": (
                        "## Reasoning Service\n"
                    ),
                    "section": "Component Specifications",
                    "anchor_text": "## Component Specifications",
                    "edit_type": "replace",
                    "confidence": 0.9,
                }
            ],
            "assumptions": [
                "Repository context is current.",
            ],
            "warnings": (
                response_warnings
                if response_warnings is not None
                else []
            ),
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
        warnings=warnings,
        metadata={
            "done": True,
        },
    )


def test_reasoning_service_creates_completed_result() -> None:
    """Verify successful reasoning result creation."""

    reasoning_request = create_reasoning_request()
    provider_request = create_provider_request()
    provider_response = create_valid_provider_response()

    prompt_builder = StubPromptBuilder(provider_request)
    provider = StubProvider(provider_response)

    service = ReasoningService(
        prompt_builder=prompt_builder,
        provider=provider,
    )

    result = service.reason(reasoning_request)

    assert result.request_id == reasoning_request.request_id
    assert result.status == ReasoningStatus.COMPLETED
    assert result.summary == (
        "One document requires an update."
    )
    assert result.provider_name == "ollama"
    assert result.model_name == "qwen3:8b"
    assert result.error_message is None
    assert result.created_at is not None


def test_reasoning_service_invokes_dependencies() -> None:
    """Verify prompt-builder and provider orchestration."""

    reasoning_request = create_reasoning_request()
    provider_request = create_provider_request()

    prompt_builder = StubPromptBuilder(provider_request)
    provider = StubProvider(
        create_valid_provider_response()
    )

    service = ReasoningService(
        prompt_builder=prompt_builder,
        provider=provider,
    )

    service.reason(reasoning_request)

    assert prompt_builder.requests == [
        reasoning_request,
    ]
    assert provider.requests == [
        provider_request,
    ]


def test_reasoning_service_parses_impacts() -> None:
    """Verify documentation impact parsing."""

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response()
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert len(result.impacts) == 1

    impact = result.impacts[0]

    assert impact.document_path == Path(
        "docs/Documentation_Agent_Design.md"
    )
    assert impact.summary == (
        "The design document requires an update."
    )
    assert impact.rationale == (
        "The Reasoning Service was implemented."
    )
    assert impact.confidence == 0.95


def test_reasoning_service_parses_proposed_changes() -> None:
    """Verify proposed documentation change parsing."""

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response()
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert len(result.proposed_changes) == 1

    change = result.proposed_changes[0]

    assert change.document_path == Path(
        "docs/Documentation_Agent_Design.md"
    )
    assert (
        change.operation
        == DocumentationChangeOperation.UPDATE
    )
    assert change.rationale == (
        "Document the Reasoning Service."
    )
    assert change.proposed_content == (
        "## Reasoning Service\n"
    )
    assert change.documentation_meaning == (
        "The Reasoning Service is part of the documented component contract."
    )
    assert change.section == "Component Specifications"
    assert change.anchor_text == "## Component Specifications"
    assert (
        change.edit_type
        == DocumentationEditType.REPLACE
    )
    assert change.confidence == 0.9


def test_reasoning_service_gap_analysis_parses_dedicated_gaps() -> None:
    """Gap analysis parses the dedicated source-grounded gap contract."""

    base_response = create_valid_provider_response()
    response = ProviderResponse(
        provider_name=base_response.provider_name,
        model_name=base_response.model_name,
        content=base_response.content,
        structured_output={
            "summary": "One material documentation gap was found.",
            "gaps": [
                {
                    "document_path": "docs/Documentation_Agent_Design.md",
                    "section": "Component Specifications",
                    "gap": "The documented contract omits existing context input.",
                    "source_evidence": (
                        "The authoritative execute signature accepts "
                        "context_content."
                    ),
                    "confidence": 0.95,
                }
            ],
            "assumptions": [],
            "warnings": [],
        },
        input_tokens=base_response.input_tokens,
        output_tokens=base_response.output_tokens,
        duration_seconds=base_response.duration_seconds,
        provider_request_id=base_response.provider_request_id,
        warnings=base_response.warnings,
        metadata=base_response.metadata,
    )

    request = ReasoningRequest(
        objective="Identify documentation gaps.",
        context="Repository context.",
        workflow_type="documentation_gap_analysis",
        target_paths=(Path("docs/Documentation_Agent_Design.md"),),
    )

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(request)

    assert result.status is ReasoningStatus.COMPLETED
    assert result.impacts == ()
    assert result.proposed_changes == ()
    assert len(result.gaps) == 1
    assert result.gaps[0].document_path == Path(
        "docs/Documentation_Agent_Design.md"
    )
    assert result.gaps[0].section == "Component Specifications"
    assert result.gaps[0].gap == (
        "The documented contract omits existing context input."
    )
    assert result.gaps[0].source_evidence == (
        "The authoritative execute signature accepts context_content."
    )
    assert result.gaps[0].confidence == 0.95


def test_reasoning_service_gap_analysis_rejects_invalid_section() -> None:
    """Gap-analysis section must be a string or null."""

    base_response = create_valid_provider_response()
    response = ProviderResponse(
        provider_name=base_response.provider_name,
        model_name=base_response.model_name,
        content=base_response.content,
        structured_output={
            "summary": "Gap analysis.",
            "gaps": [
                {
                    "document_path": "docs/Documentation_Agent_Design.md",
                    "section": 123,
                    "gap": "Missing contract.",
                    "source_evidence": "Authoritative evidence.",
                    "confidence": 0.9,
                }
            ],
            "assumptions": [],
            "warnings": [],
        },
        input_tokens=base_response.input_tokens,
        output_tokens=base_response.output_tokens,
        duration_seconds=base_response.duration_seconds,
        provider_request_id=base_response.provider_request_id,
        warnings=base_response.warnings,
        metadata=base_response.metadata,
    )

    request = ReasoningRequest(
        objective="Identify documentation gaps.",
        context="Repository context.",
        workflow_type="documentation_gap_analysis",
    )

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(request)

    assert result.status is ReasoningStatus.FAILED
    assert result.error_message == (
        "Documentation gap section must be a string or null."
    )


def test_reasoning_service_parses_assumptions() -> None:
    """Verify assumption parsing."""

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response()
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.assumptions == (
        "Repository context is current.",
    )


def test_reasoning_service_combines_warnings() -> None:
    """Verify provider and response warning combination."""

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response(
                warnings=("Provider warning.",),
                response_warnings=[
                    "Reasoning warning.",
                ],
            )
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert (
        result.status
        == ReasoningStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.warnings == (
        "Provider warning.",
        "Reasoning warning.",
    )


def test_reasoning_service_preserves_warning_provenance() -> None:
    """Verify provider and response warnings retain separate provenance."""

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response(
                warnings=("Provider warning.",),
                response_warnings=["Reasoning warning."],
            )
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.metadata["provider_warnings"] == (
        "Provider warning.",
    )
    assert result.metadata["response_warnings"] == (
        "Reasoning warning.",
    )


def test_reasoning_service_preserves_provider_metadata() -> None:
    """Verify provider execution metadata is preserved."""

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response()
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.metadata == {
        "provider_request_id": "provider-request-123",
        "input_tokens": 512,
        "output_tokens": 128,
        "duration_seconds": 1.25,
        "provider_metadata": {
            "done": True,
        },
        "provider_warnings": (),
        "response_warnings": (),
    }


def test_reasoning_service_supports_empty_results() -> None:
    """Verify valid empty reasoning collections."""

    provider_response = create_valid_provider_response()
    provider_response.structured_output[
        "impacts"
    ] = []
    provider_response.structured_output[
        "proposed_changes"
    ] = []
    provider_response.structured_output[
        "assumptions"
    ] = []

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(provider_response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.COMPLETED
    assert result.impacts == ()
    assert result.proposed_changes == ()
    assert result.assumptions == ()


def test_reasoning_service_allows_null_confidence() -> None:
    """Verify nullable confidence parsing."""

    provider_response = create_valid_provider_response()
    provider_response.structured_output[
        "impacts"
    ][0]["confidence"] = None
    provider_response.structured_output[
        "proposed_changes"
    ][0]["confidence"] = None

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(provider_response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.impacts[0].confidence is None
    assert result.proposed_changes[0].confidence is None



def test_reasoning_service_normalizes_percentage_confidence() -> None:
    """Verify percentage confidence values are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "impacts"
    ][0]["confidence"] = 95

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.impacts[0].confidence == 0.95


def test_reasoning_service_normalizes_percentage_string_confidence() -> None:
    """Verify percentage string confidence values are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "impacts"
    ][0]["confidence"] = "95%"

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.impacts[0].confidence == 0.95


def test_reasoning_service_normalizes_decimal_string_confidence() -> None:
    """Verify decimal string confidence values are normalized."""

    response = create_valid_provider_response()
    response.structured_output[
        "impacts"
    ][0]["confidence"] = "0.95"

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.impacts[0].confidence == 0.95


def test_reasoning_service_allows_null_section() -> None:
    """Verify nullable proposed-change section parsing."""

    provider_response = create_valid_provider_response()
    provider_response.structured_output[
        "proposed_changes"
    ][0]["section"] = None

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(provider_response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.proposed_changes[0].section is None



def test_reasoning_service_allows_missing_documentation_meaning() -> None:
    """Verify generic responses may omit documentation meaning."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0].pop("documentation_meaning")

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.proposed_changes[0].documentation_meaning is None


def test_reasoning_service_rejects_invalid_documentation_meaning() -> None:
    """Verify documentation meaning must be a string or null."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0]["documentation_meaning"] = 123

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "documentation_meaning must be a string or null."
    )


def test_reasoning_service_allows_null_anchor_text() -> None:
    """Verify nullable proposed-change anchor text parsing."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0]["anchor_text"] = None

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.proposed_changes[0].anchor_text is None


def test_reasoning_service_rejects_invalid_anchor_text() -> None:
    """Verify anchor text must be a string or null."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0]["anchor_text"] = 123

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "anchor_text must be a string or null."
    )


def test_reasoning_service_converts_prompt_builder_error() -> None:
    """Verify prompt-builder errors become failed results."""

    error = ValueError("Prompt construction failed.")

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request(),
            error=error,
        ),
        provider=StubProvider(
            create_valid_provider_response()
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.summary == "Reasoning failed."
    assert result.impacts == ()
    assert result.proposed_changes == ()
    assert result.provider_name == "unknown"
    assert result.model_name == "unknown"
    assert result.error_message == (
        "Prompt construction failed."
    )


def test_reasoning_service_converts_provider_error() -> None:
    """Verify provider errors become failed results."""

    error = RuntimeError("Local model server unavailable.")

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(
            create_valid_provider_response(),
            error=error,
        ),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Local model server unavailable."
    )


def test_reasoning_service_rejects_missing_structured_output() -> None:
    """Verify missing structured output becomes a failure."""

    response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="Unstructured output.",
    )

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Provider response did not include structured output."
    )


def test_reasoning_service_rejects_invalid_summary() -> None:
    """Verify invalid summary type becomes a failure."""

    response = create_valid_provider_response()
    response.structured_output["summary"] = 123

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "summary must be a string."
    )


def test_reasoning_service_rejects_invalid_impacts_type() -> None:
    """Verify impacts must be a list."""

    response = create_valid_provider_response()
    response.structured_output["impacts"] = {}

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "impacts must be a list."
    )


def test_reasoning_service_rejects_invalid_impact_item() -> None:
    """Verify each impact must be an object."""

    response = create_valid_provider_response()
    response.structured_output["impacts"] = [
        "invalid impact",
    ]

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "impact must be an object."
    )


def test_reasoning_service_rejects_invalid_operation() -> None:
    """Verify unsupported change operations become failures."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0]["operation"] = "rename"

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Unsupported documentation change operation: rename"
    )


def test_reasoning_service_rejects_invalid_edit_type() -> None:
    """Verify unsupported edit types become failures."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0]["edit_type"] = "append"

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Unsupported documentation edit type: append"
    )



def test_reasoning_service_rejects_invalid_section() -> None:
    """Verify section must be a string or null."""

    response = create_valid_provider_response()
    response.structured_output[
        "proposed_changes"
    ][0]["section"] = 123

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Proposed change section must be a string or null."
    )


def test_reasoning_service_rejects_non_numeric_confidence() -> None:
    """Verify confidence must be numeric or null."""

    response = create_valid_provider_response()
    response.structured_output[
        "impacts"
    ][0]["confidence"] = "high"

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Confidence must be numeric or null."
    )


def test_reasoning_service_rejects_out_of_range_confidence() -> None:
    """Verify confidence must be within the supported range."""

    response = create_valid_provider_response()
    response.structured_output[
        "impacts"
    ][0]["confidence"] = 1.5

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Confidence must be between 0.0 and 1.0."
    )



def test_reasoning_service_rejects_small_out_of_range_confidence() -> None:
    """Verify values above 1.0 but below percentage range are rejected."""

    response = create_valid_provider_response()
    response.structured_output[
        "impacts"
    ][0]["confidence"] = 1.5

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "Confidence must be between 0.0 and 1.0."
    )

def test_reasoning_service_rejects_non_string_assumptions() -> None:
    """Verify assumptions must contain strings only."""

    response = create_valid_provider_response()
    response.structured_output["assumptions"] = [
        "Valid assumption.",
        123,
    ]

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "assumptions must contain strings only."
    )


def test_reasoning_service_rejects_non_string_warnings() -> None:
    """Verify warnings must contain strings only."""

    response = create_valid_provider_response()
    response.structured_output["warnings"] = [
        123,
    ]

    service = ReasoningService(
        prompt_builder=StubPromptBuilder(
            create_provider_request()
        ),
        provider=StubProvider(response),
    )

    result = service.reason(
        create_reasoning_request()
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.error_message == (
        "warnings must contain strings only."
    )


def test_reasoning_service_forwards_active_skills_to_prompt_builder() -> None:
    """Reasoning requests preserve loaded Agent Skills."""

    skill = SkillDefinition(
        name="strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        skill_path=Path("skills/strict-documentation-editor/SKILL.md"),
        instructions="Apply the minimum textual modification.",
    )
    reasoning_request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
        skills=(skill,),
    )
    prompt_builder = StubPromptBuilder(create_provider_request())
    service = ReasoningService(
        prompt_builder=prompt_builder,
        provider=StubProvider(create_valid_provider_response()),
    )

    service.reason(reasoning_request)

    assert prompt_builder.requests[0].skills == (skill,)
