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

from project0.config.constants import (
    DEFAULT_OLLAMA_CONTEXT_WINDOW_TOKENS,
)
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
    context_window_tokens: int | None = DEFAULT_OLLAMA_CONTEXT_WINDOW_TOKENS

    def build_prompt(
        self,
        request: ReasoningRequest,
    ) -> ProviderRequest:
        """Build a provider request from a reasoning request."""

        return ProviderRequest(
            system_instructions=self._build_system_instructions(request),
            user_prompt=self._build_user_prompt(request),
            response_schema=self._build_response_schema(request),
            model_name=self.model_name,
            temperature=self.temperature,
            maximum_output_tokens=self.maximum_output_tokens,
            context_window_tokens=self.context_window_tokens,
            metadata={
                "reasoning_request_id": request.request_id,
                "workflow_type": request.workflow_type,
                "skill_names": tuple(
                    skill.name
                    for skill in request.skills
                ),
            },
        )

    def _build_system_instructions(
        self,
        request: ReasoningRequest,
    ) -> str:
        """Build deterministic system instructions."""

        if request.workflow_type == "documentation_gap_analysis":
            base_instructions = (
                "You are the Project0 Documentation Agent gap-analysis stage.\n"
                "Perform Stage 1 only: compare the supplied target documentation "
                "with the supplied authoritative source evidence.\n"
                "Return only material documentation gaps that are missing, "
                "outdated, inaccurate, or materially incomplete in the target.\n"
                "Each gap item must identify the affected target document, the "
                "exact existing target section when one applies, the missing or "
                "inaccurate documented fact or contract, and the authoritative "
                "source evidence that establishes the gap.\n"
                "Do not summarize the source, describe general implementation "
                "benefits, or report implementation details merely because they "
                "exist in source. Do not infer performance, efficiency, "
                "immutability benefits, architecture benefits, or design intent "
                "unless those claims are explicitly established by the supplied "
                "authoritative evidence and are materially required by the target "
                "document's existing abstraction level.\n"
                "Do not propose wording, Markdown edits, implementation changes, "
                "new fields, new interfaces, new behaviors, mechanisms, "
                "requirements, examples, or design improvements.\n"
                "A gap is material only when the target document's existing "
                "contract is missing, outdated, inaccurate, or materially "
                "incomplete at its current abstraction level.\n"
                "Evaluate the target document's actual claims first. A source "
                "implementation detail is not a documentation gap merely because "
                "the target does not mention that framework, helper, mechanism, "
                "class, function, or implementation technique. When the target "
                "already states the behavior correctly at its current abstraction "
                "level, do not report a gap for lower-level source details.\n"
                "Prefer the smallest set of non-overlapping gaps that directly "
                "identify target claims contradicted by, or materially incomplete "
                "relative to, the authoritative source. Do not split one behavior "
                "difference into multiple implementation-detail gaps.\n"
                "When BOUNDED TARGET-SOURCE CLAIM PAIRS are supplied, each Stage 1 "
                "request contains exactly one target claim and its paired authoritative "
                "source snippets. Evaluate only that one claim. Absence of evidence in "
                "a paired snippet is not a contradiction and must not create a gap. "
                "Return a gap only when the paired source positively contradicts the "
                "claim or positively establishes that it is materially incomplete. "
                "Do not search outside the supplied pair for additional omissions. "
                "Do not return the target claim, or a substantial verbatim portion "
                "of that claim, as a gap. Do not claim that "
                "the target omits a term that is already present in that exact claim. "
                "Do not treat a paired source helper or function name as required "
                "documentation merely because that implementation name is absent "
                "from the target claim. "
                "Never treat lack of evidence in the paired source as evidence that "
                "the target is wrong. Preserve semantic polarity: when the source "
                "positively performs a behavior, do not describe the source as not "
                "guaranteeing or not performing that behavior.\n"
                "When TARGET DOCUMENTATION CLAIM CANDIDATES are supplied instead, "
                "evaluate those claims explicitly before searching for undocumented "
                "source details. If one or more candidate claims are contradicted by "
                "the authoritative source, return only those contradiction gaps in "
                "this Stage 1 run and do not add lower-priority omission gaps.\n"
                "source_evidence must state the concrete source behavior or fact "
                "that establishes the discrepancy and identify the relevant function "
                "or operation when one is supplied. A source file path by itself is "
                "not sufficient evidence.\n"
                "If no material source-established documentation gap exists, "
                "return an empty gaps array.\n"
                "Warnings must be directly supported by the supplied context.\n"
                "When providing confidence values, use a decimal number between "
                "0.0 and 1.0 inclusive or null.\n"
                "Return output that conforms exactly to the supplied JSON schema."
            )

            return base_instructions

        base_instructions = (
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
            "textual modification required to satisfy the request. "
            "proposed_content must be the actual Markdown text to apply, not "
            "instructions, a plan, or a description of content that should be "
            "written. Do not return directives such as Add, Describe, Explain, "
            "Include, or Update in place of the concrete Markdown content. When an "
            "update applies within an existing Markdown section, section must "
            "contain the exact existing heading text from the supplied target "
            "document, excluding leading Markdown # characters and surrounding "
            "whitespace. Do not invent or paraphrase section names. If no existing "
            "heading reliably identifies the update location, return section as "
            "null. In source-grounded documentation updates, do not use the "
            "level-one document title as an update section. Choose an existing "
            "section only when the proposed change directly belongs to that "
            "section's current subject matter; do not choose the closest "
            "available heading when the semantic fit is weak. anchor_text, when "
            "supplied, must be exact verbatim text from "
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

        if not request.skills:
            return base_instructions

        base_instructions = (
            "You are the Project0 Documentation Agent reasoning service.\n"
            "Analyze only the supplied repository context and request.\n"
            "Do not modify source code or claim that repository changes were "
            "applied.\n"
            "The supplied response schema constrains which documentation paths "
            "may be changed. Ground Truth Source content is read-only evidence.\n"
            "Source-grounded documentation work is synchronization, not "
            "implementation design. Do not propose new source fields, interfaces, "
            "behaviors, mechanisms, or requirements. If authoritative evidence "
            "does not establish a documentation gap, do not propose a change.\n"
            "ESTABLISHED DOCUMENTATION GAPS are a closed set for proposal "
            "generation. Generate edits only for those gaps. When an established "
            "gap includes Target Claim, treat that exact target text as the edit "
            "boundary. For a contradiction, replace only that claim with the "
            "smallest corrected version; do not rewrite surrounding paragraphs or "
            "add explanatory implementation-detail prose. Do not add private or "
            "helper function names merely to explain the correction when the target "
            "claim does not already document those names. If authoritative evidence "
            "establishes multiple behaviors, preserve that conjunction in the "
            "documentation rather than weakening it with `or`. Keep "
            "documentation_meaning equally concise and limited to the established "
            "gap.\n"
            "For update operations, proposed_content must contain only the "
            "Markdown content to insert or replace, not the complete resulting "
            "document. Use section and anchor_text only to identify the exact "
            "target location. section must use an existing target-document "
            "heading value permitted by the response schema, or null when no "
            "existing heading reliably identifies the location. anchor_text, "
            "when supplied, must be exact verbatim text from the target document.\n"
            "For create operations, proposed_content must contain the complete "
            "new document. For delete operations, proposed_content must contain "
            "the content to remove or be empty when no content is required.\n"
            "When providing confidence values, use a decimal number between "
            "0.0 and 1.0 inclusive or null. Do not use percentages or values "
            "greater than 1.0.\n"
            "Return output that conforms exactly to the supplied JSON schema."
        )

        skill_sections = tuple(
            (
                f"\n\n=== ACTIVE AGENT SKILL: {skill.name} ===\n"
                f"{skill.instructions.strip()}"
            )
            for skill in request.skills
        )

        return base_instructions + "".join(skill_sections)

    def _build_user_prompt(
        self,
        request: ReasoningRequest,
    ) -> str:
        """Build the user prompt from a reasoning request."""

        if request.workflow_type == "documentation_gap_analysis":
            sections = [
                "Objective:",
                request.objective.strip(),
                "",
                "Workflow Type:",
                "documentation_gap_analysis",
            ]

            if request.target_paths:
                sections.extend(
                    (
                        "",
                        "Target Documentation Paths:",
                        *(
                            f"- {path.as_posix()}"
                            for path in request.target_paths
                        ),
                    )
                )

            sections.extend(
                (
                    "",
                    "Stage 1 Gap Analysis Rule:",
                    (
                        "Compare the target's existing claims directly against "
                        "authoritative source evidence and return only material "
                        "source-established documentation gaps. Do not treat a "
                        "lower-level implementation detail as a gap when the target "
                        "already documents the behavior correctly at its current "
                        "abstraction level. Prefer the smallest set of non-overlapping "
                        "gaps. When BOUNDED TARGET-SOURCE CLAIM PAIRS are supplied, "
                        "this request contains exactly one target claim. Evaluate only "
                        "that claim against its paired source snippets. Missing evidence "
                        "is not a contradiction; return a gap only when paired source "
                        "evidence positively contradicts the claim or positively "
                        "establishes material incompleteness. Do not search outside the "
                        "supplied pair, do not repeat the target claim or a substantial "
                        "verbatim portion of it as the gap, and do not claim that a "
                        "term is missing when that term is already "
                        "present in the exact target claim, do not require paired "
                        "source helper/function names to appear in documentation merely "
                        "because they exist in source, and preserve semantic "
                        "polarity between the paired source behavior and the returned "
                        "gap. When TARGET "
                        "DOCUMENTATION CLAIM CANDIDATES are supplied instead, evaluate "
                        "those candidates first and return only contradiction gaps "
                        "before considering missing-detail gaps. Each gap must name the exact "
                        "target section when one "
                        "applies and state the concrete source behavior that "
                        "establishes the missing, outdated, or inaccurate documented "
                        "fact; a source path alone is not evidence. Do not propose "
                        "edits, wording, implementation changes, or design "
                        "recommendations. Return an empty gaps array when there is "
                        "no material gap."
                    ),
                    "",
                    "Repository Context:",
                    request.context.strip(),
                )
            )

            return "\n".join(sections)

        sections = [
            "Objective:",
            request.objective.strip(),
        ]

        target_headings, source_grounded = (
            self._extract_markdown_headings(
                request.context
            )
        )

        if request.workflow_type:
            sections.extend(
                (
                    "",
                    "Workflow Type:",
                    request.workflow_type,
                )
            )

        if request.target_paths and not source_grounded:
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

        if source_grounded:
            sections.extend(
                (
                    "",
                    "Source-Grounded Synchronization Rule:",
                    (
                        "Compare the authoritative source only against what the "
                        "target documentation already claims. Propose documentation "
                        "changes only for source-established gaps. ESTABLISHED "
                        "DOCUMENTATION GAPS are the complete allowed change set. When "
                        "an established gap includes Target Claim, use that exact "
                        "target text as the change boundary and make only the smallest "
                        "correction needed to resolve the gap. Do not add helper "
                        "function names or implementation explanation that the target "
                        "claim does not require. If source evidence establishes "
                        "multiple behaviors, document all of them rather than "
                        "weakening the relationship with `or`. Do not recommend new "
                        "implementation fields, interfaces, behaviors, mechanisms, "
                        "or requirements. If the source does not establish a material "
                        "documentation gap, return no proposed change for it."
                    ),
                )
            )

        if source_grounded and target_headings:
            sections.extend(
                (
                    "",
                    "Permitted Existing Target Sections:",
                    *(
                        f"- {heading}"
                        for heading in target_headings
                    ),
                    (
                        "Choose a section only when the proposed change "
                        "directly belongs to that section's existing subject "
                        "matter. Do not choose a section merely because it "
                        "is the closest available heading. If no existing "
                        "section is semantically appropriate, return section "
                        "as null."
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

    @staticmethod
    def _extract_markdown_headings(
        context: str,
    ) -> tuple[tuple[str, ...], bool]:
        """Extract valid Markdown section headings from supplied context.

        Source-grounded documentation context is explicitly segmented using
        TARGET DOCUMENTATION and AUTHORITATIVE SOURCE markers. When those
        markers are present, only target-documentation headings are eligible
        and level-one document titles are excluded as update locations.

        Generic documentation context preserves the previous behavior and
        considers all Markdown headings.
        """

        target_marker = "=== TARGET DOCUMENTATION ==="
        source_marker = "=== AUTHORITATIVE SOURCE ==="
        source_grounded = target_marker in context

        headings: list[str] = []
        in_target = not source_grounded

        for line in context.splitlines():
            stripped = line.strip()

            if source_grounded:
                if stripped == target_marker:
                    in_target = True
                    continue

                if stripped == source_marker:
                    in_target = False
                    continue

                if stripped.startswith("=== ") and stripped.endswith(" ==="):
                    in_target = False
                    continue

                if not in_target:
                    continue

            if not stripped.startswith("#"):
                continue

            marker_length = len(stripped) - len(
                stripped.lstrip("#")
            )

            if not 1 <= marker_length <= 6:
                continue

            if source_grounded and marker_length == 1:
                continue

            remainder = stripped[marker_length:]

            if not remainder.startswith(" "):
                continue

            heading = remainder.strip()

            if heading and heading not in headings:
                headings.append(heading)

        return tuple(headings), source_grounded

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

        if request.workflow_type == "documentation_gap_analysis":
            gap_document_path_schema: dict[str, object] = {
                "type": "string",
            }
            if request.target_paths:
                gap_document_path_schema["enum"] = [
                    path.as_posix()
                    for path in request.target_paths
                ]

            target_headings, source_grounded = (
                self._extract_markdown_headings(
                    request.context
                )
            )
            gap_section_value_schema: dict[str, object] = {
                "type": "string",
            }
            if target_headings:
                gap_section_value_schema["enum"] = list(target_headings)
            elif source_grounded:
                gap_section_value_schema["enum"] = []

            return {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "summary",
                    "gaps",
                    "assumptions",
                    "warnings",
                ],
                "properties": {
                    "summary": {
                        "description": (
                            "Concise result of the target-versus-source "
                            "documentation gap comparison. Do not summarize "
                            "the source implementation."
                        ),
                        "type": "string",
                    },
                    "gaps": {
                        "description": (
                            "Smallest non-overlapping set of material "
                            "source-established documentation gaps only. Do not "
                            "report lower-level implementation details when the "
                            "target already documents the behavior correctly at "
                            "its current abstraction level. Return an empty array "
                            "when there are none."
                        ),
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "document_path",
                                "section",
                                "gap",
                                "source_evidence",
                                "confidence",
                            ],
                            "properties": {
                                "document_path": gap_document_path_schema,
                                "section": {
                                    "description": (
                                        "Exact existing Markdown heading text "
                                        "from the target document, excluding "
                                        "leading # characters, or null when no "
                                        "existing section directly owns the gap."
                                    ),
                                    "anyOf": [
                                        gap_section_value_schema,
                                        {
                                            "type": "null",
                                        },
                                    ],
                                },
                                "gap": {
                                    "description": (
                                        "The specific documented fact or contract "
                                        "that is missing, outdated, inaccurate, "
                                        "or materially incomplete in the target. "
                                        "Do not describe general implementation "
                                        "benefits or propose a design change."
                                    ),
                                    "type": "string",
                                },
                                "source_evidence": {
                                    "description": (
                                        "The concrete authoritative source behavior "
                                        "or fact that establishes this gap. State "
                                        "only evidence observable in the supplied "
                                        "authoritative source. A source file path "
                                        "by itself is not sufficient evidence. Describe "
                                        "the relevant function or operation and the "
                                        "observable behavior that establishes the gap. "
                                        "Absence of a fact from a bounded paired snippet "
                                        "is not evidence of contradiction."
                                    ),
                                    "type": "string",
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
                            "Only warnings directly supported by the "
                            "supplied context."
                        ),
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                },
            }

        proposed_document_path_schema: dict[str, object] = {
            "type": "string",
        }
        if request.target_paths:
            proposed_document_path_schema["enum"] = [
                path.as_posix()
                for path in request.target_paths
            ]

        section_value_schema: dict[str, object] = {
            "type": "string",
        }
        target_headings, source_grounded = (
            self._extract_markdown_headings(
                request.context
            )
        )
        if target_headings:
            section_value_schema["enum"] = list(target_headings)
        elif source_grounded:
            section_value_schema["enum"] = []

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
                            *(
                                ["documentation_meaning"]
                                if source_grounded
                                else []
                            ),
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
                                "description": (
                                    (
                                        "Explain only why authoritative source "
                                        "evidence makes the existing target "
                                        "documentation missing, outdated, "
                                        "inaccurate, or materially incomplete. "
                                        "Do not recommend implementation changes "
                                        "or new source behavior."
                                    )
                                    if source_grounded
                                    else (
                                        "Explain why the proposed documentation "
                                        "change is needed."
                                    )
                                ),
                                "type": "string",
                            },
                            "documentation_meaning": {
                                "description": (
                                    "Concise documentation meaning derived from "
                                    "the supplied evidence. Describe the contract, "
                                    "purpose, inputs, outputs, constraints, or "
                                    "behavior that the target documentation needs "
                                    "to express. Do not copy source syntax, recommend "
                                    "implementation changes, invent new source behavior, "
                                    "or return Markdown editing instructions."
                                ),
                                "type": "string",
                            },
                            "proposed_content": {
                                "description": (
                                    (
                                        "Concrete Markdown text in the existing "
                                        "form of the affected target section. "
                                        "Translate authoritative implementation "
                                        "evidence into documentation prose when "
                                        "the target section is prose. Do not "
                                        "introduce a fenced source-code block "
                                        "unless that target section already "
                                        "contains comparable fenced source code. "
                                        "Must not be instructions, a plan, a "
                                        "recommendation, or a description of content "
                                        "that should be written. Must document only "
                                        "behavior established by the authoritative "
                                        "source."
                                    )
                                    if source_grounded
                                    else (
                                        "Concrete Markdown text to apply. Must "
                                        "not be instructions, a plan, or a "
                                        "description of content that should be "
                                        "written."
                                    )
                                ),
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
                                    section_value_schema,
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
