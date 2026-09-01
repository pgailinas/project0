# ============================================================
# Project0 - Ollama Reasoning Provider
#
# File: ollama_provider.py
#
# Purpose:
#     Execute Project0 reasoning requests against a local Ollama
#     service and return provider-neutral reasoning responses.
#
# ============================================================

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import time

import httpx

from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class OllamaReasoningProvider:
    """Execute reasoning requests against the Ollama chat API."""

    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 120.0
    temperature: float = 0.0

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Generate a provider response using a local Ollama model."""

        endpoint = f"{self.base_url.rstrip('/')}/api/chat"

        payload = {
            "model": request.model_name,
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
                "temperature": self.temperature,
            },
        }

        debug_capture_path = request.metadata.get(
            "debug_capture_path"
        )
        if isinstance(debug_capture_path, str) and debug_capture_path:
            Path(debug_capture_path).write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            LOGGER.debug(
                "Ollama request payload captured: %s",
                debug_capture_path,
            )

        LOGGER.debug(
            "Ollama request endpoint=%s model=%s system_length=%d "
            "user_length=%d",
            endpoint,
            request.model_name,
            len(request.system_instructions),
            len(request.user_prompt),
        )
        start_time = time.time()

        try:
            response = httpx.post(
                endpoint,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            LOGGER.debug(
                "Ollama response completed in %.2f seconds",
                time.time() - start_time,
            )

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "Ollama request failed with HTTP status "
                f"{error.response.status_code}."
            ) from error
        except httpx.RequestError as error:
            raise RuntimeError(
                f"Ollama service could not be reached: {type(error).__name__}: {error}"
            ) from error

        try:
            response_data = response.json()
        except ValueError as error:
            raise ValueError(
                "Ollama response was not valid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise TypeError(
                "Ollama response must be a JSON object."
            )

        message = response_data.get("message")

        if not isinstance(message, dict):
            raise TypeError(
                "Ollama response did not include a message object."
            )

        content = message.get("content")

        if not isinstance(content, str):
            raise TypeError(
                "Ollama response message content must be a string."
            )

        try:
            structured_output = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Ollama response content was not valid structured JSON."
            ) from error

        if not isinstance(structured_output, dict):
            raise TypeError(
                "Ollama structured output must be a JSON object."
            )

        return ProviderResponse(
            provider_name="ollama",
            model_name=self._get_string(
                response_data,
                "model",
                default=request.model_name,
            ),
            content=content,
            structured_output=structured_output,
            input_tokens=self._get_optional_int(
                response_data,
                "prompt_eval_count",
            ),
            output_tokens=self._get_optional_int(
                response_data,
                "eval_count",
            ),
            duration_seconds=self._duration_seconds(
                response_data.get("total_duration")
            ),
            provider_request_id=None,
            metadata=self._create_metadata(response_data),
        )

    def _duration_seconds(
        self,
        value: Any,
    ) -> float | None:
        """Convert an Ollama nanosecond duration to seconds."""

        if value is None:
            return None

        if not isinstance(value, (int, float)):
            raise TypeError(
                "Ollama total_duration must be numeric or null."
            )

        return float(value) / 1_000_000_000

    def _create_metadata(
        self,
        response_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create provider-specific metadata from an Ollama response."""

        metadata_keys = (
            "created_at",
            "done",
            "done_reason",
            "load_duration",
            "prompt_eval_duration",
            "eval_duration",
        )

        return {
            key: response_data[key]
            for key in metadata_keys
            if key in response_data
        }

    def _get_optional_int(
        self,
        mapping: dict[str, Any],
        field_name: str,
    ) -> int | None:
        """Return an optional integer response field."""

        value = mapping.get(field_name)

        if value is None:
            return None

        if not isinstance(value, int):
            raise TypeError(
                f"Ollama {field_name} must be an integer or null."
            )

        return value

    def _get_string(
        self,
        mapping: dict[str, Any],
        field_name: str,
        default: str,
    ) -> str:
        """Return a string response field or its provided default."""

        value = mapping.get(field_name, default)

        if not isinstance(value, str):
            raise TypeError(
                f"Ollama {field_name} must be a string."
            )

        return value
