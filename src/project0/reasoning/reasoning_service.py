# ============================================================
# Project0 - Reasoning Service
#
# File: reasoning_service.py
#
# Purpose:
#     Coordinate prompt construction, provider execution, and
#     structured Project0 reasoning result generation.
#
# ============================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from project0.interfaces.reasoning_interfaces import (
    PromptBuilderProtocol,
    ReasoningProviderProtocol,
)
from project0.models.reasoning_models import (
    DocumentationChangeOperation,
    DocumentationImpact,
    ProposedDocumentationChange,
    ProviderResponse,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)


class ReasoningService:
    """Execute AI-assisted repository reasoning."""

    def __init__(
        self,
        prompt_builder: PromptBuilderProtocol,
        provider: ReasoningProviderProtocol,
    ) -> None:
        """Initialize the reasoning service dependencies."""

        self._prompt_builder = prompt_builder
        self._provider = provider

    def reason(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResult:
        """Execute repository reasoning for a request."""

        try:
            provider_request = self._prompt_builder.build_prompt(
                request
            )

            provider_response = self._provider.generate(
                provider_request
            )

            return self._create_completed_result(
                request=request,
                provider_response=provider_response,
            )

        except (OSError, RuntimeError, ValueError, TypeError) as error:
            return self._create_failed_result(
                request=request,
                error=error,
            )

    def _create_completed_result(
        self,
        request: ReasoningRequest,
        provider_response: ProviderResponse,
    ) -> ReasoningResult:
        """Create a reasoning result from a provider response."""

        structured_output = provider_response.structured_output

        if structured_output is None:
            raise ValueError(
                "Provider response did not include structured output."
            )

        summary = self._require_string(
            structured_output,
            "summary",
        )

        impacts = self._parse_impacts(
            structured_output.get("impacts")
        )

        proposed_changes = self._parse_proposed_changes(
            structured_output.get("proposed_changes")
        )

        assumptions = self._parse_string_tuple(
            structured_output.get("assumptions"),
            "assumptions",
        )

        response_warnings = self._parse_string_tuple(
            structured_output.get("warnings"),
            "warnings",
        )

        warnings = (
            *provider_response.warnings,
            *response_warnings,
        )

        status = (
            ReasoningStatus.COMPLETED_WITH_WARNINGS
            if warnings
            else ReasoningStatus.COMPLETED
        )

        return ReasoningResult(
            request_id=request.request_id,
            status=status,
            summary=summary,
            impacts=impacts,
            proposed_changes=proposed_changes,
            created_at=datetime.now(),
            provider_name=provider_response.provider_name,
            model_name=provider_response.model_name,
            assumptions=assumptions,
            warnings=warnings,
            metadata={
                "provider_request_id": (
                    provider_response.provider_request_id
                ),
                "input_tokens": provider_response.input_tokens,
                "output_tokens": provider_response.output_tokens,
                "duration_seconds": (
                    provider_response.duration_seconds
                ),
                "provider_metadata": dict(
                    provider_response.metadata
                ),
            },
        )

    def _create_failed_result(
        self,
        request: ReasoningRequest,
        error: Exception,
    ) -> ReasoningResult:
        """Create a failed reasoning result."""

        return ReasoningResult(
            request_id=request.request_id,
            status=ReasoningStatus.FAILED,
            summary="Reasoning failed.",
            impacts=(),
            proposed_changes=(),
            created_at=datetime.now(),
            provider_name="unknown",
            model_name="unknown",
            error_message=str(error),
        )

    def _parse_impacts(
        self,
        value: Any,
    ) -> tuple[DocumentationImpact, ...]:
        """Parse documentation impacts from structured output."""

        items = self._require_list(
            value,
            "impacts",
        )

        impacts: list[DocumentationImpact] = []

        for item in items:
            mapping = self._require_mapping(
                item,
                "impact",
            )

            impacts.append(
                DocumentationImpact(
                    document_path=Path(
                        self._require_string(
                            mapping,
                            "document_path",
                        )
                    ),
                    summary=self._require_string(
                        mapping,
                        "summary",
                    ),
                    rationale=self._require_string(
                        mapping,
                        "rationale",
                    ),
                    confidence=self._parse_confidence(
                        mapping.get("confidence")
                    ),
                )
            )

        return tuple(impacts)

    def _parse_proposed_changes(
        self,
        value: Any,
    ) -> tuple[ProposedDocumentationChange, ...]:
        """Parse proposed changes from structured output."""

        items = self._require_list(
            value,
            "proposed_changes",
        )

        changes: list[ProposedDocumentationChange] = []

        for item in items:
            mapping = self._require_mapping(
                item,
                "proposed change",
            )

            operation_value = self._require_string(
                mapping,
                "operation",
            )

            try:
                operation = DocumentationChangeOperation(
                    operation_value
                )
            except ValueError as error:
                raise ValueError(
                    "Unsupported documentation change operation: "
                    f"{operation_value}"
                ) from error

            section = mapping.get("section")

            if section is not None and not isinstance(
                section,
                str,
            ):
                raise TypeError(
                    "Proposed change section must be a string or null."
                )

            changes.append(
                ProposedDocumentationChange(
                    document_path=Path(
                        self._require_string(
                            mapping,
                            "document_path",
                        )
                    ),
                    operation=operation,
                    rationale=self._require_string(
                        mapping,
                        "rationale",
                    ),
                    proposed_content=self._require_string(
                        mapping,
                        "proposed_content",
                    ),
                    section=section,
                    anchor_text=self._parse_optional_string(
                        mapping.get("anchor_text"),
                        "anchor_text",
                    ),
                    confidence=self._parse_confidence(
                        mapping.get("confidence")
                    ),
                )
            )

        return tuple(changes)

    def _parse_string_tuple(
        self,
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        """Parse a list of strings into a tuple."""

        items = self._require_list(
            value,
            field_name,
        )

        if not all(
            isinstance(item, str)
            for item in items
        ):
            raise TypeError(
                f"{field_name} must contain strings only."
            )

        return tuple(items)

    def _parse_optional_string(
        self,
        value: Any,
        field_name: str,
    ) -> str | None:
        """Parse an optional string value."""

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string or null."
            )

        return value

    def _parse_confidence(
        self,
        value: Any,
    ) -> float | None:
        """Parse an optional confidence value."""

        if value is None:
            return None

        if not isinstance(value, (int, float)):
            raise TypeError(
                "Confidence must be numeric or null."
            )

        confidence = float(value)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "Confidence must be between 0.0 and 1.0."
            )

        return confidence

    def _require_string(
        self,
        mapping: dict[str, Any],
        field_name: str,
    ) -> str:
        """Return a required string value."""

        value = mapping.get(field_name)

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        return value

    def _require_list(
        self,
        value: Any,
        field_name: str,
    ) -> list[Any]:
        """Return a required list value."""

        if not isinstance(value, list):
            raise TypeError(
                f"{field_name} must be a list."
            )

        return value

    def _require_mapping(
        self,
        value: Any,
        field_name: str,
    ) -> dict[str, Any]:
        """Return a required mapping value."""

        if not isinstance(value, dict):
            raise TypeError(
                f"{field_name} must be an object."
            )

        return value
