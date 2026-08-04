# ============================================================
# Project0 - Stub Reasoning Provider Tests
#
# File: test_stub_provider.py
#
# Purpose:
#     Verify deterministic stub reasoning provider behavior for
#     Project0 tests, demonstrations, and integration flows.
#
# ============================================================

from __future__ import annotations

import pytest

from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)
from project0.reasoning.providers.stub_provider import (
    StubReasoningProvider,
)


def create_provider_request(
    prompt: str = "User prompt.",
) -> ProviderRequest:
    """Create a provider request for testing."""

    return ProviderRequest(
        system_instructions="System instructions.",
        user_prompt=prompt,
        response_schema={
            "type": "object",
        },
        model_name="qwen3:8b",
    )


def create_provider_response() -> ProviderResponse:
    """Create a provider response for testing."""

    return ProviderResponse(
        provider_name="stub",
        model_name="stub-model",
        content='{"summary": "Stub response."}',
        structured_output={
            "summary": "Stub response.",
            "impacts": [],
            "proposed_changes": [],
            "assumptions": [],
            "warnings": [],
        },
        input_tokens=10,
        output_tokens=5,
        duration_seconds=0.0,
        provider_request_id="stub-request-123",
        metadata={
            "stub": True,
        },
    )


def test_stub_provider_returns_configured_response() -> None:
    """Verify the configured response is returned."""

    request = create_provider_request()
    response = create_provider_response()

    provider = StubReasoningProvider(
        response=response,
    )

    result = provider.generate(request)

    assert result is response


def test_stub_provider_records_request() -> None:
    """Verify generated requests are recorded."""

    request = create_provider_request()
    provider = StubReasoningProvider(
        response=create_provider_response(),
    )

    provider.generate(request)

    assert provider.requests == [
        request,
    ]


def test_stub_provider_records_multiple_requests() -> None:
    """Verify multiple requests are recorded in call order."""

    first_request = create_provider_request(
        "First prompt."
    )
    second_request = create_provider_request(
        "Second prompt."
    )

    provider = StubReasoningProvider(
        response=create_provider_response(),
    )

    provider.generate(first_request)
    provider.generate(second_request)

    assert provider.requests == [
        first_request,
        second_request,
    ]


def test_stub_provider_returns_same_configured_response() -> None:
    """Verify repeated calls return the configured response."""

    response = create_provider_response()
    provider = StubReasoningProvider(
        response=response,
    )

    first_result = provider.generate(
        create_provider_request("First prompt.")
    )
    second_result = provider.generate(
        create_provider_request("Second prompt.")
    )

    assert first_result is response
    assert second_result is response


def test_stub_provider_starts_with_empty_request_history() -> None:
    """Verify a new stub provider has no recorded requests."""

    provider = StubReasoningProvider(
        response=create_provider_response(),
    )

    assert provider.requests == []


def test_stub_provider_request_histories_are_independent() -> None:
    """Verify provider instances have independent histories."""

    first_provider = StubReasoningProvider(
        response=create_provider_response(),
    )
    second_provider = StubReasoningProvider(
        response=create_provider_response(),
    )

    first_provider.generate(
        create_provider_request()
    )

    assert len(first_provider.requests) == 1
    assert second_provider.requests == []
    assert (
        first_provider.requests
        is not second_provider.requests
    )


def test_stub_provider_raises_configured_error() -> None:
    """Verify a configured provider error is raised."""

    error = RuntimeError(
        "Configured stub provider failure."
    )

    provider = StubReasoningProvider(
        response=create_provider_response(),
        error=error,
    )

    with pytest.raises(
        RuntimeError,
        match="Configured stub provider failure",
    ):
        provider.generate(
            create_provider_request()
        )


def test_stub_provider_records_request_before_error() -> None:
    """Verify failed requests are recorded before raising."""

    request = create_provider_request()

    provider = StubReasoningProvider(
        response=create_provider_response(),
        error=OSError("Stub provider unavailable."),
    )

    with pytest.raises(OSError):
        provider.generate(request)

    assert provider.requests == [
        request,
    ]


def test_stub_provider_error_defaults_to_none() -> None:
    """Verify provider errors are disabled by default."""

    provider = StubReasoningProvider(
        response=create_provider_response(),
    )

    assert provider.error is None


def test_stub_provider_error_can_be_cleared() -> None:
    """Verify a configured error can be removed."""

    provider = StubReasoningProvider(
        response=create_provider_response(),
        error=RuntimeError("Temporary failure."),
    )

    provider.error = None

    result = provider.generate(
        create_provider_request()
    )

    assert result is provider.response
