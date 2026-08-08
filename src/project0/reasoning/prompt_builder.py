# ============================================================
# Project0 - Prompt Builder
#
# File: prompt_builder.py
#
# Purpose:
#     Build deterministic provider-neutral prompts for
#     Project0 reasoning services.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass

from project0.models.reasoning_models import (
    ProviderRequest,
    ReasoningRequest,
)


@dataclass(slots=True)
class PromptBuilder:
    """Build provider-neutral prompts for repository reasoning."""

    model_name: str | None = None
    temperature: float | None = 0.0
    maximum_output_tokens: int | None = 4096

    def build_prompt(
        self,
        request: ReasoningRequest,
    ) -> ProviderRequest:
        """Build a provider request from a reasoning request."""

        return ProviderRequest(
            system_instructions=self._build_system_instructions(),
            user_prompt=self._build_user_prompt(request),
            response_schema=self._build_response_schema(),
            model_name=self.model_name,
            temperature=self.temperature,
            maximum_output_tokens=self.maximum_output_tokens,
            metadata={
                "reasoning_request_id": request.request_id,
                "workflow_type": request.workflow_type,
            },
        )

    def _build_system_instructions(self) -> str:
        """Build deterministic system instructions."""

        return (
            "You are the Project0 Documentation Agent reasoning service.\n"
            "Analyze only the supplied repository context and request.\n"
            "Identify documentation impacts and propose documentation changes "
            "only when supported by the supplied context.\n"
            "Do not modify source code or claim that repository changes were "
            "applied.\n"
            "Preserve repository-relative paths and Markdown formatting.\n"
            "Target Paths identify the documents that may be changed. "
            "Repository context outside the Target Paths is reference-only "
            "and must not be proposed for modification unless explicitly "
            "requested.\n"
            "For an update operation, proposed_content must contain the "
            "complete resulting document, including all unchanged existing "
            "content. Preserve existing content that is unrelated to the "
            "requested change and prefer the smallest change necessary to "
            "satisfy the request.\n"
            "For a create operation, proposed_content must contain the "
            "complete new document. For a delete operation, proposed_content "
            "must be empty.\n"
            "When providing confidence values, use a decimal number between "
            "0.0 and 1.0 inclusive or null. Do not use percentages or values "
            "greater than 1.0.\n"
            "Return output that conforms exactly to the supplied JSON schema."
        )

    def _build_user_prompt(
        self,
        request: ReasoningRequest,
    ) -> str:
        """Build the user prompt from a reasoning request."""

        sections = [
            "Objective:",
            request.objective.strip(),
        ]

        if request.workflow_type:
            sections.extend(
                (
                    "",
                    "Workflow Type:",
                    request.workflow_type,
                )
            )

        if request.target_paths:
            sections.extend(
                (
                    "",
                    "Target Paths:",
                    *(
                        f"- {path.as_posix()}"
                        for path in request.target_paths
                    ),
                )
            )

        if request.constraints:
            sections.extend(
                (
                    "",
                    "Constraints:",
                    *(
                        f"- {constraint}"
                        for constraint in request.constraints
                    ),
                )
            )

        sections.extend(
            (
                "",
                "Repository Context:",
                request.context.strip(),
            )
        )

        return "\n".join(sections)

    def _build_response_schema(self) -> dict[str, object]:
        """Build the structured reasoning response schema."""

        confidence_schema = {
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

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "summary",
                "impacts",
                "proposed_changes",
                "assumptions",
                "warnings",
            ],
            "properties": {
                "summary": {
                    "type": "string",
                },
                "impacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "document_path",
                            "summary",
                            "rationale",
                            "confidence",
                        ],
                        "properties": {
                            "document_path": {
                                "type": "string",
                            },
                            "summary": {
                                "type": "string",
                            },
                            "rationale": {
                                "type": "string",
                            },
                            "confidence": confidence_schema,
                        },
                    },
                },
                "proposed_changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "document_path",
                            "operation",
                            "rationale",
                            "proposed_content",
                            "section",
                            "confidence",
                        ],
                        "properties": {
                            "document_path": {
                                "type": "string",
                            },
                            "operation": {
                                "type": "string",
                                "enum": [
                                    "create",
                                    "update",
                                    "delete",
                                ],
                            },
                            "rationale": {
                                "type": "string",
                            },
                            "proposed_content": {
                                "type": "string",
                            },
                            "section": {
                                "anyOf": [
                                    {
                                        "type": "string",
                                    },
                                    {
                                        "type": "null",
                                    },
                                ]
                            },
                            "confidence": confidence_schema,
                        },
                    },
                },
                "assumptions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "warnings": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        }
