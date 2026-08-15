# ============================================================
# Project0 - Knowledge Models
#
# File: knowledge_models.py
#
# Purpose:
#     Define shared repository knowledge data models used by
#     Project0 platform components and AI agents.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
from project0.config.constants import KNOWLEDGE_MAXIMUM_DOCUMENTS


@dataclass(frozen=True, slots=True)
class DocumentHeading:
    """A heading extracted from a repository document."""

    level: int
    title: str
    line_number: int
    anchor: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentLink:
    """A link extracted from a repository document."""

    text: str
    target: str
    line_number: int
    is_internal: bool = True


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    """A parsed repository document and its metadata."""

    path: Path
    title: str
    content: str
    headings: tuple[DocumentHeading, ...] = ()
    links: tuple[DocumentLink, ...] = ()
    tags: tuple[str, ...] = ()
    modified_at: datetime | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """Selection information for a repository document."""

    path: Path
    title: str
    reason: str
    score: float = 0.0
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeRequest:
    """A request for repository knowledge."""

    query: str
    workflow_type: str | None = None
    requested_paths: tuple[Path, ...] = ()
    changed_paths: tuple[Path, ...] = ()
    required_tags: tuple[str, ...] = ()
    search_terms: tuple[str, ...] = ()
    maximum_documents: int = KNOWLEDGE_MAXIMUM_DOCUMENTS
    include_baseline_documents: bool = True
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class DocumentSelection:
    """Documents selected for a repository knowledge request."""

    documents: tuple[DocumentRecord, ...]
    references: tuple[DocumentReference, ...]
    excluded_paths: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeResult:
    """Result of a repository knowledge request."""

    request_id: str
    query: str
    selection: DocumentSelection
    context: str
    created_at: datetime
    context_metadata: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    
    
