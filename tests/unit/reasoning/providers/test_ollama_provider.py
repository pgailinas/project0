# ============================================================
# Project0 - Ollama Reasoning Provider Tests
#
# File: test_ollama_provider.py
#
# Purpose:
#     Verify Ollama reasoning provider request construction,
#     response parsing, metadata mapping, and error handling.
#
# ============================================================

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from project0.models.reasoning_models import ProviderRequest
from project0.reasoning.providers.ollama_provider import (
    OllamaReasoningProvider,
)


def create_provider_request() -> ProviderRequest:
    """Create a representative Ollama provider request."""

    return ProviderRequest(
        system_instructions="Return structured documentation reasoning.",
        user_prompt="Update docs/Implementation_Status.md.",
        response_schema={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                },
                "impacts": {
                    "type": "array",
                },
                "proposed_changes": {
                    "type": "array",
                },
                "assumptions": {
                    "type": "array",
                },
                "warnings": {
                    "type": "array",
                },
            },
            "required": [
                "summary",
                "impacts",
                "proposed_changes",
                "assumptions",
                "warnings",
            ],
        },
        model_name="qwen2.5:7b",
    )


def create_ollama_response_data() -> dict[str, Any]:
    """Create a representative Ollama chat response."""

    structured_output = {
        "summary": "Update the implementation status.",
        "impacts": [],
        "proposed_changes": [],
        "assumptions": [],
        "warnings": [],
    }

    return {
        "model": "qwen2.5:7b",
        "created_at": "2026-08-07T22:00:00Z",
        "message": {
            "role": "assistant",
            "content": json.dumps(structured_output),
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": 2_500_000_000,
        "load_duration": 100_000_000,
        "prompt_eval_count": 125,
        "prompt_eval_duration": 500_000_000,
        "eval_count": 50,
        "eval_duration": 1_900_000_000,
    }


def create_http_response(
    status_code: int = 200,
    data: Any | None = None,
    content: bytes | None = None,
) -> httpx.Response:
    """Create an HTTP response with request metadata attached."""

    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/chat",
    )

    if content is not None:
        return httpx.Response(
            status_code,
            content=content,
            request=request,
        )

    return httpx.Response(
        status_code,
        json=(
            create_ollama_response_data()
            if data is None
            else data
        ),
        request=request,
    )


def test_ollama_provider_builds_expected_chat_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Project0 requests map to the Ollama chat API."""

    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return create_http_response()

    monkeypatch.setattr(httpx, "post", fake_post)

    request = create_provider_request()
    provider = OllamaReasoningProvider(
        timeout_seconds=45.0,
    )

    provider.generate(request)

    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["timeout"] == 45.0
    assert captured["json"] == {
        "model": "qwen2.5:7b",
        "messages": [
            {
                "role": "system",
                "content": request.system_instructions,
            },
            {
                "role": "user",
                "content": request.user_prompt,
            },
        ],
        "stream": False,
        "format": request.response_schema,
        "options": {
            "temperature": 0.0,
        },
    }


def test_ollama_provider_normalizes_trailing_base_url_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify a trailing base URL slash does not duplicate separators."""

    captured_url = ""

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        nonlocal captured_url
        captured_url = url
        return create_http_response()

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = OllamaReasoningProvider(
        base_url="http://localhost:11434/",
    )

    provider.generate(create_provider_request())

    assert captured_url == "http://localhost:11434/api/chat"


def test_ollama_provider_returns_provider_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify a successful Ollama response maps to ProviderResponse."""

    response_data = create_ollama_response_data()

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    provider = OllamaReasoningProvider()

    result = provider.generate(create_provider_request())

    assert result.provider_name == "ollama"
    assert result.model_name == "qwen2.5:7b"
    assert result.structured_output == {
        "summary": "Update the implementation status.",
        "impacts": [],
        "proposed_changes": [],
        "assumptions": [],
        "warnings": [],
    }
    assert result.content == response_data["message"]["content"]


def test_ollama_provider_maps_token_counts_and_duration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify provider-neutral metrics are populated from Ollama."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(),
    )

    result = OllamaReasoningProvider().generate(
        create_provider_request()
    )

    assert result.input_tokens == 125
    assert result.output_tokens == 50
    assert result.duration_seconds == 2.5


def test_ollama_provider_preserves_provider_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify useful Ollama-specific metadata is retained."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(),
    )

    result = OllamaReasoningProvider().generate(
        create_provider_request()
    )

    assert result.metadata == {
        "created_at": "2026-08-07T22:00:00Z",
        "done": True,
        "done_reason": "stop",
        "load_duration": 100_000_000,
        "prompt_eval_duration": 500_000_000,
        "eval_duration": 1_900_000_000,
    }


def test_ollama_provider_uses_request_model_when_response_omits_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify request model is used when Ollama omits model metadata."""

    response_data = create_ollama_response_data()
    response_data.pop("model")

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    result = OllamaReasoningProvider().generate(
        create_provider_request()
    )

    assert result.model_name == "qwen2.5:7b"


def test_ollama_provider_raises_runtime_error_for_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify non-success HTTP responses become provider failures."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            status_code=500,
            data={"error": "model failure"},
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Ollama request failed with HTTP status 500",
    ):
        OllamaReasoningProvider().generate(
            create_provider_request()
        )


def test_ollama_provider_raises_runtime_error_when_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify connection failures become provider failures."""

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

    with pytest.raises(
        RuntimeError,
        match="Ollama service could not be reached",
    ):
        OllamaReasoningProvider().generate(
            create_provider_request()
        )


def test_ollama_provider_rejects_non_json_http_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify malformed HTTP response JSON is rejected."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            content=b"not-json"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Ollama response was not valid JSON",
    ):
        OllamaReasoningProvider().generate(
            create_provider_request()
        )


def test_ollama_provider_requires_message_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the Ollama response must contain a message object."""

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            data={
                "model": "qwen2.5:7b",
                "done": True,
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="did not include a message object",
    ):
        OllamaReasoningProvider().generate(
            create_provider_request()
        )


def test_ollama_provider_rejects_invalid_structured_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify assistant content must contain valid structured JSON."""

    response_data = create_ollama_response_data()
    response_data["message"]["content"] = "not structured json"

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        ValueError,
        match="not valid structured JSON",
    ):
        OllamaReasoningProvider().generate(
            create_provider_request()
        )


def test_ollama_provider_requires_structured_output_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify structured output must be a JSON object."""

    response_data = create_ollama_response_data()
    response_data["message"]["content"] = json.dumps(
        ["unexpected", "list"]
    )

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: create_http_response(
            data=response_data
        ),
    )

    with pytest.raises(
        TypeError,
        match="structured output must be a JSON object",
    ):
        OllamaReasoningProvider().generate(
            create_provider_request()
        )
