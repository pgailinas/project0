# ============================================================
# Project0 - Reasoning Service Flow Integration Tests
#
# File: test_reasoning_service_flow.py
#
# Purpose:
#     Verify the complete provider-neutral reasoning flow using
#     real Project0 reasoning components and the stub provider.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    DocumentationEditType,
    ProviderResponse,
    ReasoningRequest,
    ReasoningStatus,
)
from project0.reasoning.prompt_builder import PromptBuilder
from project0.reasoning.providers.stub_provider import (
    StubReasoningProvider,
)
from project0.reasoning.reasoning_service import ReasoningService


def create_provider_response(
    *,
    warnings: tuple[str, ...] = (),
    response_warnings: list[str] | None = None,
) -> ProviderResponse:
    """Create a structured provider response for integration tests."""

    return ProviderResponse(
        provider_name="stub",
        model_name="stub-model",
        content='{"summary": "Documentation impact identified."}',
        structured_output={
            "summary": "Documentation impact identified.",
            "impacts": [
                {
                    "document_path": (
                        "docs/Documentation_Agent_Design.md"
                    ),
                    "summary": (
                        "The design document requires an update."
                    ),
                    "rationale": (
                        "The Reasoning Service is now implemented."
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
                    "edit_type": "replace",
                    "rationale": (
                        "Document the implemented Reasoning Service."
                    ),
                    "proposed_content": (
                        "## Reasoning Service\n"
                        "\n"
                        "Coordinates provider-neutral reasoning.\n"
                    ),
                    "section": "Component Specifications",
                    "confidence": 0.9,
                }
            ],
            "assumptions": [
                "The supplied repository context is current.",
            ],
            "warnings": (
                response_warnings
                if response_warnings is not None
                else []
            ),
        },
        input_tokens=256,
        output_tokens=96,
        duration_seconds=0.0,
        provider_request_id="stub-request-001",
        warnings=warnings,
        metadata={
            "stub": True,
        },
    )


def test_reasoning_service_flow_completes_successfully() -> None:
    """Verify the complete reasoning flow produces a result."""

    prompt_builder = PromptBuilder(
        model_name="stub-model",
        temperature=0.0,
        maximum_output_tokens=2048,
    )

    provider = StubReasoningProvider(
        response=create_provider_response()
    )

    service = ReasoningService(
        prompt_builder=prompt_builder,
        provider=provider,
    )

    request = ReasoningRequest(
        objective=(
            "Identify documentation impacted by the "
            "Reasoning Service implementation."
        ),
        context=(
            "--- Document: "
            "docs/Documentation_Agent_Design.md ---\n"
            "Title: Documentation Agent Component Design\n\n"
            "# Documentation Agent Component Design\n"
        ),
        workflow_type="documentation_update",
        target_paths=(
            Path("docs/Documentation_Agent_Design.md"),
        ),
        constraints=(
            "Preserve Markdown style.",
            "Do not modify source code.",
        ),
    )

    result = service.reason(request)

    assert result.request_id == request.request_id
    assert result.status == ReasoningStatus.COMPLETED
    assert result.summary == (
        "Documentation impact identified."
    )
    assert result.provider_name == "stub"
    assert result.model_name == "stub-model"
    assert result.error_message is None


def test_reasoning_service_flow_builds_provider_request() -> None:
    """Verify prompt construction through the complete flow."""

    prompt_builder = PromptBuilder(
        model_name="stub-model",
        temperature=0.0,
        maximum_output_tokens=2048,
    )

    provider = StubReasoningProvider(
        response=create_provider_response()
    )

    service = ReasoningService(
        prompt_builder=prompt_builder,
        provider=provider,
    )

    request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
        workflow_type="documentation_update",
        target_paths=(
            Path("docs/Documentation_Agent_Design.md"),
        ),
        constraints=("Preserve Markdown style.",),
    )

    service.reason(request)

    assert len(provider.requests) == 1

    provider_request = provider.requests[0]

    assert provider_request.model_name == "stub-model"
    assert provider_request.temperature == 0.0
    assert provider_request.maximum_output_tokens == 2048
    assert provider_request.metadata == {
        "reasoning_request_id": request.request_id,
        "workflow_type": "documentation_update",
        "skill_names": (),
    }
    assert (
        "Objective:\nAnalyze documentation impact."
        in provider_request.user_prompt
    )
    assert (
        "Target Paths:\n"
        "- docs/Documentation_Agent_Design.md"
        in provider_request.user_prompt
    )
    assert (
        "Constraints:\n"
        "- Preserve Markdown style."
        in provider_request.user_prompt
    )
    assert (
        "Repository Context:\nRepository context."
        in provider_request.user_prompt
    )


def test_reasoning_service_flow_uses_response_schema() -> None:
    """Verify the provider request contains the expected schema."""

    provider = StubReasoningProvider(
        response=create_provider_response()
    )

    service = ReasoningService(
        prompt_builder=PromptBuilder(
            model_name="stub-model"
        ),
        provider=provider,
    )

    service.reason(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
    )

    schema = provider.requests[0].response_schema

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "summary",
        "impacts",
        "proposed_changes",
        "assumptions",
        "warnings",
    ]


def test_reasoning_service_flow_parses_impact() -> None:
    """Verify impact conversion through the complete flow."""

    service = ReasoningService(
        prompt_builder=PromptBuilder(),
        provider=StubReasoningProvider(
            response=create_provider_response()
        ),
    )

    result = service.reason(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
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
        "The Reasoning Service is now implemented."
    )
    assert impact.confidence == 0.95


def test_reasoning_service_flow_parses_proposed_change() -> None:
    """Verify proposed-change conversion through the flow."""

    service = ReasoningService(
        prompt_builder=PromptBuilder(),
        provider=StubReasoningProvider(
            response=create_provider_response()
        ),
    )

    result = service.reason(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
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
        "Document the implemented Reasoning Service."
    )
    assert change.section == "Component Specifications"
    assert (
        change.edit_type
        == DocumentationEditType.REPLACE
    )
    assert change.confidence == 0.9
    assert (
        "Coordinates provider-neutral reasoning."
        in change.proposed_content
    )


def test_reasoning_service_flow_preserves_assumptions() -> None:
    """Verify assumptions are preserved through the flow."""

    service = ReasoningService(
        prompt_builder=PromptBuilder(),
        provider=StubReasoningProvider(
            response=create_provider_response()
        ),
    )

    result = service.reason(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
    )

    assert result.assumptions == (
        "The supplied repository context is current.",
    )


def test_reasoning_service_flow_combines_warnings() -> None:
    """Verify provider and response warnings are combined."""

    provider = StubReasoningProvider(
        response=create_provider_response(
            warnings=("Provider warning.",),
            response_warnings=[
                "Reasoning warning.",
            ],
        )
    )

    service = ReasoningService(
        prompt_builder=PromptBuilder(),
        provider=provider,
    )

    result = service.reason(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
    )

    assert (
        result.status
        == ReasoningStatus.COMPLETED_WITH_WARNINGS
    )
    assert result.warnings == (
        "Provider warning.",
        "Reasoning warning.",
    )


def test_reasoning_service_flow_preserves_provider_metadata() -> None:
    """Verify provider metadata is preserved through the flow."""

    service = ReasoningService(
        prompt_builder=PromptBuilder(),
        provider=StubReasoningProvider(
            response=create_provider_response()
        ),
    )

    result = service.reason(
        ReasoningRequest(
            objective="Analyze documentation.",
            context="Repository context.",
        )
    )

    assert result.metadata == {
        "provider_request_id": "stub-request-001",
        "input_tokens": 256,
        "output_tokens": 96,
        "duration_seconds": 0.0,
        "provider_metadata": {
            "stub": True,
        },
        "provider_warnings": (),
        "response_warnings": (),
    }


def test_reasoning_service_flow_converts_provider_failure() -> None:
    """Verify provider failures become structured results."""

    provider = StubReasoningProvider(
        response=create_provider_response(),
        error=RuntimeError(
            "Configured stub provider failure."
        ),
    )

    service = ReasoningService(
        prompt_builder=PromptBuilder(),
        provider=provider,
    )

    request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    result = service.reason(request)

    assert result.request_id == request.request_id
    assert result.status == ReasoningStatus.FAILED
    assert result.summary == "Reasoning failed."
    assert result.impacts == ()
    assert result.proposed_changes == ()
    assert result.provider_name == "unknown"
    assert result.model_name == "unknown"
    assert result.error_message == (
        "Configured stub provider failure."
    )
    assert len(provider.requests) == 1


def test_reasoning_service_flow_is_repeatable() -> None:
    """Verify repeated flow execution remains deterministic."""

    provider = StubReasoningProvider(
        response=create_provider_response()
    )

    service = ReasoningService(
        prompt_builder=PromptBuilder(
            model_name="stub-model",
            temperature=0.0,
        ),
        provider=provider,
    )

    request = ReasoningRequest(
        objective="Analyze documentation.",
        context="Repository context.",
    )

    first_result = service.reason(request)
    second_result = service.reason(request)

    assert first_result.status == second_result.status
    assert first_result.summary == second_result.summary
    assert first_result.impacts == second_result.impacts
    assert (
        first_result.proposed_changes
        == second_result.proposed_changes
    )
    assert first_result.assumptions == second_result.assumptions
    assert first_result.warnings == second_result.warnings
    assert len(provider.requests) == 2
    assert (
        provider.requests[0].system_instructions
        == provider.requests[1].system_instructions
    )
    assert (
        provider.requests[0].user_prompt
        == provider.requests[1].user_prompt
    )
    assert (
        provider.requests[0].response_schema
        == provider.requests[1].response_schema
    )
