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
            response_schema=self._build_response_schema(request),
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
            "Target Paths identify the only documents that may be changed. "
            "Repository context outside the Target Paths is read-only "
            "reference evidence and must never be returned as a proposed "
            "change document_path. Ground Truth Source content is always "
            "read-only evidence.\n"
            "For an update operation, proposed_content must contain only "
            "the documentation content to insert or replace. It must not "
            "contain the complete resulting document. Identify the target "
            "location using section and anchor_text. Make only the minimum "
            "textual modification required to satisfy the request. When an "
            "update applies within an existing Markdown section, section must "
            "contain the exact existing heading text from the supplied target "
            "document, excluding leading Markdown # characters and surrounding "
            "whitespace. Do not invent or paraphrase section names. If no existing "
            "heading reliably identifies the update location, return section as "
            "null. anchor_text, when supplied, must be exact verbatim text from "
            "the target document rather than a generated description. Do not "
            "reproduce the surrounding document or section in proposed_content. "
            "If adding information to an existing list, proposed_content must "
            "contain only the new list item or items. Do not include existing "
            "headings, metadata, unchanged list items, or surrounding Markdown "
            "in proposed_content. Preserve existing repository content that is "
            "unrelated to the requested change. Do not rewrite, reorder, "
            "normalize, or reproduce unrelated Markdown content. Do not change "
            "metadata or other lines unless required by the requested update.\n"
            "Warnings must be directly supported by the supplied repository "
            "context. Do not report duplicate definitions, inconsistencies, "
            "missing elements, unsupported behavior, or other repository "
            "conditions unless they are explicitly observable in the supplied "
            "context. If a warning cannot be verified from the supplied context, "
            "omit it.\n"
            "For a create operation, proposed_content must contain the "
            "complete new document. For a delete operation, proposed_content "
            "must contain the content to remove or be empty when no content "
            "is required.\n"
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
                    "",
                    "Permitted proposed_changes document_path values:",
                    *(
                        f"- {path.as_posix()}"
                        for path in request.target_paths
                    ),
                    (
                        "Every proposed_changes item must use exactly one "
                        "of the permitted document_path values above."
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

    def _build_response_schema(
        self,
        request: ReasoningRequest,
    ) -> dict[str, object]:
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

        proposed_document_path_schema: dict[str, object] = {
            "type": "string",
        }
        if request.target_paths:
            proposed_document_path_schema["enum"] = [
                path.as_posix()
                for path in request.target_paths
            ]

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
                            "anchor_text",
                            "edit_type",
                            "confidence",
                        ],
                        "properties": {
                            "document_path": (
                                proposed_document_path_schema
                            ),
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
                                "description": (
                                    "Exact existing Markdown heading text from "
                                    "the supplied target document, excluding "
                                    "leading # characters, or null when no "
                                    "existing heading reliably identifies the "
                                    "update location."
                                ),
                                "anyOf": [
                                    {
                                        "type": "string",
                                    },
                                    {
                                        "type": "null",
                                    },
                                ]
                            },
                            "anchor_text": {
                                "description": (
                                    "Exact verbatim text from the supplied "
                                    "target document to use as an edit anchor, "
                                    "or null when no reliable anchor exists."
                                ),
                                "anyOf": [
                                    {
                                        "type": "string",
                                    },
                                    {
                                        "type": "null",
                                    },
                                ]
                            },
                            "edit_type": {
                                "type": "string",
                                "enum": [
                                    "insert",
                                    "replace",
                                    "delete",
                                ],
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
                    "description": (
                        "Only repository warnings directly supported by "
                        "the supplied context. Omit warnings that cannot "
                        "be verified from that context."
                    ),
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        }
