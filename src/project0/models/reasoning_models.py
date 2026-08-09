# ============================================================
# Project0 - Reasoning Models
#
# File: reasoning_models.py
#
# Purpose:
#     Define shared reasoning and provider data models used by
#     Project0 platform components and AI agents.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


class ReasoningStatus(StrEnum):
    """Supported reasoning execution states."""

    PENDING = "pending"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class DocumentationChangeOperation(StrEnum):
    """Supported documentation change operations."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class DocumentationEditType(StrEnum):
    """Supported documentation edit types."""

    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class DocumentationImpact:
    """A repository documentation impact identified by reasoning."""

    document_path: Path
    summary: str
    rationale: str
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ProposedDocumentationChange:
    """A proposed documentation edit to one repository document."""

    document_path: Path
    operation: DocumentationChangeOperation
    rationale: str
    proposed_content: str
    section: str | None = None
    anchor_text: str | None = None
    edit_type: DocumentationEditType = DocumentationEditType.REPLACE
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    """A request for AI-assisted repository reasoning."""

    objective: str
    context: str
    workflow_type: str | None = None
    target_paths: tuple[Path, ...] = ()
    constraints: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """A provider-neutral model generation request."""

    system_instructions: str
    user_prompt: str
    response_schema: dict[str, Any]
    model_name: str | None = None
    temperature: float | None = None
    maximum_output_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """A provider-neutral model generation response."""

    provider_name: str
    model_name: str
    content: str
    structured_output: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    duration_seconds: float | None = None
    provider_request_id: str | None = None
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    """Result of an AI-assisted repository reasoning request."""

    request_id: str
    status: ReasoningStatus
    summary: str
    impacts: tuple[DocumentationImpact, ...]
    proposed_changes: tuple[ProposedDocumentationChange, ...]
    created_at: datetime
    provider_name: str
    model_name: str
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
