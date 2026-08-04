# ============================================================
# Project0 - Context Models
#
# File: context_models.py
#
# Purpose:
#     Define shared data models used to request, build,
#     and exchange Project0 context packages.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ContextBuildStatus(StrEnum):
    """Supported context-package build states."""

    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ContextRequest:
    """Request used to build context for a Project0 task."""

    context_id: str
    project_id: str = "Project0"


@dataclass(frozen=True, slots=True)
class ContextDocument:
    """One repository document included in a context package."""

    relative_path: str
    content: str
    size_bytes: int
    modified_at: datetime


@dataclass(frozen=True, slots=True)
class ContextPackage:
    """Context assembled for use by a Project0 component or AI agent."""

    context_id: str
    project_id: str
    status: ContextBuildStatus
    created_at: datetime
    documents: tuple[ContextDocument, ...]
    source_count: int
    total_characters: int
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        """Return True when context creation did not fail."""

        return self.status in {
            ContextBuildStatus.COMPLETED,
            ContextBuildStatus.COMPLETED_WITH_WARNINGS,
        }

    @property
    def has_warnings(self) -> bool:
        """Return True when the package contains warnings."""

        return bool(self.warnings)

    @property
    def has_errors(self) -> bool:
        """Return True when the package contains errors."""

        return bool(self.errors)
