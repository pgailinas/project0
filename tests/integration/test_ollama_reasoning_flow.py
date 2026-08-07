# ============================================================
# Project0 - Ollama Reasoning Flow Integration Tests
#
# File: test_ollama_reasoning_flow.py
#
# Purpose:
#     Verify the provider-neutral Project0 reasoning flow using
#     the real Prompt Builder, Reasoning Service, and Ollama
#     reasoning provider with a mocked Ollama HTTP boundary.
#
# ============================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    ReasoningRequest,
    ReasoningStatus,
)
from project0.reasoning.prompt_builder import PromptBuilder
from project0.reasoning.providers.ollama_provider import (
    OllamaReasoningProvider,
)
from project0.reasoning.reasoning_service import ReasoningService


def create_ollama_response() -> dict[str, Any]:
    """Create a representative structured Ollama chat response."""

    structured_output = {
        "summary": (
            "The implementation status documentation requires an update."
        ),
        "impacts": [
            {
                "document_path": "docs/Implementation_Status.md",
                "summary": (
                    "Phase 8 status should reflect Ollama integration work."
                ),
                "rationale": (
                    "The local Ollama reasoning provider is now implemented."
                ),
                "confidence": 0.95,
            },
        ],
        "proposed_changes": [
            {
                "document_path": "docs/Implementation_Status.md",
                "operation": "update",
                "rationale": (
                    "Document the addition of local Ollama reasoning."
                ),
                "proposed_content": (
                    "## Phase 8 - Documentation Agent User Interface\n"
                    "\n"
                    "Local Ollama reasoning provider integration is "
                    "in progress.\n"
                ),
                "section": "Phase 8",
                "confidence": 0.9,
            },
        ],
        "assumptions": [
            "The supplied repository context is current.",
        ],
        "warnings": [],
    }

    return {
        "model": "qwen2.5:7b",
        "created_at": "2026-08-07T23:00:00Z",
        "message": {
            "role": "assistant",
            "content": json.dumps(structured_output),
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": 3_000_000_000,
        "load_duration": 200_000_000,
        "prompt_eval_count": 300,
        "prompt_eval_duration": 800_000_000,
        "eval_count": 120,
        "eval_duration": 2_000_000_000,
    }


def create_http_response(
    data: dict[str, Any] | None = None,
) -> httpx.Response:
    """Create a successful Ollama HTTP response."""

    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/chat",
    )

    return httpx.Response(
        200,
        json=data or create_ollama_response(),
        request=request,
    )


def create_reasoning_service() -> ReasoningService:
    """Create the integrated reasoning stack using Ollama."""

    return ReasoningService(
        prompt_builder=PromptBuilder(
            model_name="qwen2.5:7b",
            temperature=0.0,
            maximum_output_tokens=4096,
        ),
        provider=OllamaReasoningProvider(),
    )


def create_reasoning_request() -> ReasoningRequest:
    """Create a representative documentation reasoning request."""

    return ReasoningRequest(
        objective=(
            "Update implementation status documentation for "
            "the Ollama reasoning provider."
        ),
        context=(
            "--- Document: docs/Implementation_Status.md ---\n"
            "# Project0 Implementation Status\n"
            "\n"
            "Phase 8 is in progress.\n"
        ),
        workflow_type="documentation_update",
        target_paths=(
            Path("docs/Implementation_Status.md"),
        ),
        constraints=(
            "Preserve Markdown style.",
            "Do not modify source code.",
        ),
    )


def test_ollama_reasoning_flow_completes_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Ollama output becomes a completed reasoning result."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(),
    )

    request = create_reasoning_request()

    result = create_reasoning_service().reason(request)

    assert result.request_id == request.request_id
    assert result.status == ReasoningStatus.COMPLETED
    assert result.summary == (
        "The implementation status documentation requires an update."
    )
    assert result.provider_name == "ollama"
    assert result.model_name == "qwen2.5:7b"
    assert result.error_message is None


def test_ollama_reasoning_flow_parses_documentation_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify structured Ollama output becomes Project0 change models."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(),
    )

    result = create_reasoning_service().reason(
        create_reasoning_request()
    )

    assert len(result.impacts) == 1
    assert len(result.proposed_changes) == 1

    impact = result.impacts[0]

    assert impact.document_path == Path(
        "docs/Implementation_Status.md"
    )
    assert impact.confidence == 0.95

    change = result.proposed_changes[0]

    assert change.document_path == Path(
        "docs/Implementation_Status.md"
    )
    assert (
        change.operation
        == DocumentationChangeOperation.UPDATE
    )
    assert change.section == "Phase 8"
    assert change.confidence == 0.9
    assert (
        "Local Ollama reasoning provider integration is in progress."
        in change.proposed_content
    )


def test_ollama_reasoning_flow_passes_prompt_schema_to_ollama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the Prompt Builder schema reaches the Ollama API."""

    captured_payload: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        captured_payload.update(json)
        return create_http_response()

    monkeypatch.setattr(httpx, "post", fake_post)

    create_reasoning_service().reason(
        create_reasoning_request()
    )

    assert captured_payload["model"] == "qwen2.5:7b"
    assert captured_payload["stream"] is False
    assert captured_payload["options"] == {
        "temperature": 0.0,
    }

    schema = captured_payload["format"]

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "summary",
        "impacts",
        "proposed_changes",
        "assumptions",
        "warnings",
    ]

    assert (
        "Project0 Documentation Agent reasoning service"
        in captured_payload["messages"][0]["content"]
    )
    assert (
        "Update implementation status documentation"
        in captured_payload["messages"][1]["content"]
    )


def test_ollama_reasoning_flow_preserves_provider_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Ollama metrics survive through the Reasoning Service."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(),
    )

    result = create_reasoning_service().reason(
        create_reasoning_request()
    )

    assert result.metadata == {
        "provider_request_id": None,
        "input_tokens": 300,
        "output_tokens": 120,
        "duration_seconds": 3.0,
        "provider_metadata": {
            "created_at": "2026-08-07T23:00:00Z",
            "done": True,
            "done_reason": "stop",
            "load_duration": 200_000_000,
            "prompt_eval_duration": 800_000_000,
            "eval_duration": 2_000_000_000,
        },
    }


def test_ollama_reasoning_flow_converts_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Ollama connection failures become failed reasoning results."""

    def fake_post(*args: Any, **kwargs: Any) -> httpx.Response:
        request = httpx.Request(
            "POST",
            "http://127.0.0.1:11434/api/chat",
        )

        raise httpx.ConnectError(
            "Connection refused.",
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    request = create_reasoning_request()

    result = create_reasoning_service().reason(request)

    assert result.request_id == request.request_id
    assert result.status == ReasoningStatus.FAILED
    assert result.summary == "Reasoning failed."
    assert result.impacts == ()
    assert result.proposed_changes == ()
    assert result.provider_name == "unknown"
    assert result.model_name == "unknown"
    assert result.error_message == (
        "Ollama service could not be reached."
    )
