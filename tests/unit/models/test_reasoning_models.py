# ============================================================
# Project0 - Reasoning Model Tests
#
# File: test_reasoning_models.py
#
# Purpose:
#     Verify shared reasoning and provider data models used by
#     Project0 platform components and AI agents.
#
# ============================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    DocumentationImpact,
    ProposedDocumentationChange,
    ProviderRequest,
    ProviderResponse,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)


def test_reasoning_status_values() -> None:
    """Verify supported reasoning status values."""

    assert ReasoningStatus.PENDING == "pending"
    assert ReasoningStatus.COMPLETED == "completed"
    assert (
        ReasoningStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert ReasoningStatus.FAILED == "failed"


def test_documentation_change_operation_values() -> None:
    """Verify supported documentation change operation values."""

    assert DocumentationChangeOperation.CREATE == "create"
    assert DocumentationChangeOperation.UPDATE == "update"
    assert DocumentationChangeOperation.DELETE == "delete"


def test_documentation_impact_creation() -> None:
    """Verify creation of a documentation impact."""

    impact = DocumentationImpact(
        document_path=Path(
            "docs/Documentation_Agent_Architecture.md"
        ),
        summary="Architecture documentation requires an update.",
        rationale=(
            "The repository knowledge pipeline has changed."
        ),
        confidence=0.95,
    )

    assert impact.document_path == Path(
        "docs/Documentation_Agent_Architecture.md"
    )
    assert impact.summary == (
        "Architecture documentation requires an update."
    )
    assert impact.rationale == (
        "The repository knowledge pipeline has changed."
    )
    assert impact.confidence == 0.95


def test_documentation_impact_default_confidence() -> None:
    """Verify the default documentation impact confidence."""

    impact = DocumentationImpact(
        document_path=Path("docs/Example.md"),
        summary="Example impact.",
        rationale="Example rationale.",
    )

    assert impact.confidence is None


def test_proposed_documentation_change_creation() -> None:
    """Verify creation of a proposed documentation change."""

    change = ProposedDocumentationChange(
        document_path=Path(
            "docs/Documentation_Agent_Design.md"
        ),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Add the Reasoning Service design.",
        proposed_content="## Reasoning Service\n",
        section="Component Specifications",
        confidence=0.9,
    )

    assert change.document_path == Path(
        "docs/Documentation_Agent_Design.md"
    )
    assert (
        change.operation
        == DocumentationChangeOperation.UPDATE
    )
    assert change.rationale == (
        "Add the Reasoning Service design."
    )
    assert change.proposed_content == (
        "## Reasoning Service\n"
    )
    assert change.section == "Component Specifications"
    assert change.confidence == 0.9


def test_proposed_documentation_change_defaults() -> None:
    """Verify default proposed documentation change values."""

    change = ProposedDocumentationChange(
        document_path=Path("docs/New_Document.md"),
        operation=DocumentationChangeOperation.CREATE,
        rationale="Create a new document.",
        proposed_content="# New Document\n",
    )

    assert change.section is None
    assert change.confidence is None


def test_reasoning_request_creation() -> None:
    """Verify creation of a reasoning request."""

    request = ReasoningRequest(
        objective=(
            "Identify documentation impacted by the "
            "Reasoning Service implementation."
        ),
        context="Repository knowledge context.",
        workflow_type="documentation_update",
        target_paths=(
            Path("docs/Documentation_Agent_Design.md"),
        ),
        constraints=(
            "Preserve Markdown style.",
            "Do not modify source code.",
        ),
        metadata={
            "phase": 4,
        },
    )

    assert request.objective == (
        "Identify documentation impacted by the "
        "Reasoning Service implementation."
    )
    assert request.context == "Repository knowledge context."
    assert request.workflow_type == "documentation_update"
    assert request.target_paths == (
        Path("docs/Documentation_Agent_Design.md"),
    )
    assert request.constraints == (
        "Preserve Markdown style.",
        "Do not modify source code.",
    )
    assert request.metadata == {
        "phase": 4,
    }
    assert request.request_id


def test_reasoning_request_defaults() -> None:
    """Verify default reasoning request values."""

    request = ReasoningRequest(
        objective="Analyze documentation impact.",
        context="Repository context.",
    )

    assert request.workflow_type is None
    assert request.target_paths == ()
    assert request.constraints == ()
    assert request.metadata == {}
    assert request.request_id


def test_reasoning_request_ids_are_unique() -> None:
    """Verify reasoning requests receive unique identifiers."""

    first_request = ReasoningRequest(
        objective="First request.",
        context="First context.",
    )

    second_request = ReasoningRequest(
        objective="Second request.",
        context="Second context.",
    )

    assert first_request.request_id != second_request.request_id


def test_reasoning_request_metadata_is_independent() -> None:
    """Verify reasoning requests receive independent metadata."""

    first_request = ReasoningRequest(
        objective="First request.",
        context="First context.",
    )

    second_request = ReasoningRequest(
        objective="Second request.",
        context="Second context.",
    )

    assert first_request.metadata is not second_request.metadata


def test_provider_request_creation() -> None:
    """Verify creation of a provider request."""

    request = ProviderRequest(
        system_instructions=(
            "You are the Project0 Documentation Agent."
        ),
        user_prompt="Analyze the supplied repository context.",
        response_schema={
            "type": "object",
        },
        model_name="qwen3:8b",
        temperature=0.2,
        maximum_output_tokens=2048,
        metadata={
            "provider": "ollama",
        },
    )

    assert request.system_instructions == (
        "You are the Project0 Documentation Agent."
    )
    assert request.user_prompt == (
        "Analyze the supplied repository context."
    )
    assert request.response_schema == {
        "type": "object",
    }
    assert request.model_name == "qwen3:8b"
    assert request.temperature == 0.2
    assert request.maximum_output_tokens == 2048
    assert request.metadata == {
        "provider": "ollama",
    }
    assert request.request_id


def test_provider_request_defaults() -> None:
    """Verify default provider request values."""

    request = ProviderRequest(
        system_instructions="System instructions.",
        user_prompt="User prompt.",
        response_schema={},
    )

    assert request.model_name is None
    assert request.temperature is None
    assert request.maximum_output_tokens is None
    assert request.metadata == {}
    assert request.request_id


def test_provider_request_ids_are_unique() -> None:
    """Verify provider requests receive unique identifiers."""

    first_request = ProviderRequest(
        system_instructions="First system instructions.",
        user_prompt="First user prompt.",
        response_schema={},
    )

    second_request = ProviderRequest(
        system_instructions="Second system instructions.",
        user_prompt="Second user prompt.",
        response_schema={},
    )

    assert first_request.request_id != second_request.request_id


def test_provider_request_metadata_is_independent() -> None:
    """Verify provider requests receive independent metadata."""

    first_request = ProviderRequest(
        system_instructions="First system instructions.",
        user_prompt="First user prompt.",
        response_schema={},
    )

    second_request = ProviderRequest(
        system_instructions="Second system instructions.",
        user_prompt="Second user prompt.",
        response_schema={},
    )

    assert first_request.metadata is not second_request.metadata


def test_provider_response_creation() -> None:
    """Verify creation of a provider response."""

    response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content='{"summary": "Documentation impact found."}',
        structured_output={
            "summary": "Documentation impact found.",
        },
        input_tokens=512,
        output_tokens=128,
        duration_seconds=1.25,
        provider_request_id="provider-request-123",
        warnings=("Example warning.",),
        metadata={
            "done": True,
        },
    )

    assert response.provider_name == "ollama"
    assert response.model_name == "qwen3:8b"
    assert response.content == (
        '{"summary": "Documentation impact found."}'
    )
    assert response.structured_output == {
        "summary": "Documentation impact found.",
    }
    assert response.input_tokens == 512
    assert response.output_tokens == 128
    assert response.duration_seconds == 1.25
    assert response.provider_request_id == (
        "provider-request-123"
    )
    assert response.warnings == (
        "Example warning.",
    )
    assert response.metadata == {
        "done": True,
    }


def test_provider_response_defaults() -> None:
    """Verify default provider response values."""

    response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
    )

    assert response.structured_output is None
    assert response.input_tokens is None
    assert response.output_tokens is None
    assert response.duration_seconds is None
    assert response.provider_request_id is None
    assert response.warnings == ()
    assert response.metadata == {}


def test_provider_response_metadata_is_independent() -> None:
    """Verify provider responses receive independent metadata."""

    first_response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
    )

    second_response = ProviderResponse(
        provider_name="ollama",
        model_name="qwen3:8b",
        content="{}",
    )

    assert first_response.metadata is not second_response.metadata


def test_reasoning_result_creation() -> None:
    """Verify creation of a completed reasoning result."""

    created_at = datetime(2026, 8, 4, 17, 0)

    impact = DocumentationImpact(
        document_path=Path(
            "docs/Documentation_Agent_Design.md"
        ),
        summary="Design documentation requires an update.",
        rationale="The Reasoning Service was implemented.",
        confidence=0.95,
    )

    change = ProposedDocumentationChange(
        document_path=Path(
            "docs/Documentation_Agent_Design.md"
        ),
        operation=DocumentationChangeOperation.UPDATE,
        rationale="Document the Reasoning Service.",
        proposed_content="## Reasoning Service\n",
        section="Component Specifications",
        confidence=0.9,
    )

    result = ReasoningResult(
        request_id="reasoning-request-123",
        status=ReasoningStatus.COMPLETED,
        summary="One documentation update is proposed.",
        impacts=(impact,),
        proposed_changes=(change,),
        created_at=created_at,
        provider_name="ollama",
        model_name="qwen3:8b",
        assumptions=("Repository context is current.",),
        warnings=(),
        metadata={
            "input_tokens": 512,
            "output_tokens": 128,
        },
    )

    assert result.request_id == "reasoning-request-123"
    assert result.status == ReasoningStatus.COMPLETED
    assert result.summary == (
        "One documentation update is proposed."
    )
    assert result.impacts == (impact,)
    assert result.proposed_changes == (change,)
    assert result.created_at == created_at
    assert result.provider_name == "ollama"
    assert result.model_name == "qwen3:8b"
    assert result.assumptions == (
        "Repository context is current.",
    )
    assert result.warnings == ()
    assert result.error_message is None
    assert result.metadata == {
        "input_tokens": 512,
        "output_tokens": 128,
    }


def test_reasoning_result_failure_creation() -> None:
    """Verify creation of a failed reasoning result."""

    result = ReasoningResult(
        request_id="reasoning-request-456",
        status=ReasoningStatus.FAILED,
        summary="Reasoning failed.",
        impacts=(),
        proposed_changes=(),
        created_at=datetime(2026, 8, 4, 17, 5),
        provider_name="ollama",
        model_name="qwen3:8b",
        error_message="Local model server was unavailable.",
    )

    assert result.status == ReasoningStatus.FAILED
    assert result.impacts == ()
    assert result.proposed_changes == ()
    assert result.error_message == (
        "Local model server was unavailable."
    )


def test_reasoning_result_defaults() -> None:
    """Verify default reasoning result values."""

    result = ReasoningResult(
        request_id="reasoning-request-789",
        status=ReasoningStatus.COMPLETED,
        summary="Reasoning completed.",
        impacts=(),
        proposed_changes=(),
        created_at=datetime(2026, 8, 4, 17, 10),
        provider_name="ollama",
        model_name="qwen3:8b",
    )

    assert result.assumptions == ()
    assert result.warnings == ()
    assert result.error_message is None
    assert result.metadata == {}


def test_reasoning_result_metadata_is_independent() -> None:
    """Verify reasoning results receive independent metadata."""

    first_result = ReasoningResult(
        request_id="first-request",
        status=ReasoningStatus.COMPLETED,
        summary="First result.",
        impacts=(),
        proposed_changes=(),
        created_at=datetime(2026, 8, 4, 17, 15),
        provider_name="ollama",
        model_name="qwen3:8b",
    )

    second_result = ReasoningResult(
        request_id="second-request",
        status=ReasoningStatus.COMPLETED,
        summary="Second result.",
        impacts=(),
        proposed_changes=(),
        created_at=datetime(2026, 8, 4, 17, 16),
        provider_name="ollama",
        model_name="qwen3:8b",
    )

    assert first_result.metadata is not second_result.metadata
