# ============================================================
# Project0 - Artifact Models
#
# File: artifact_models.py
#
# Purpose:
#     Define shared data models used to represent Project0
#     repository artifacts, artifact locations, and controlled
#     modification requests.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ArtifactLocationType(StrEnum):
    """Supported artifact location types."""

    FILE = "file"
    SECTION = "section"
    HEADING = "heading"
    LINE_RANGE = "line_range"


class ArtifactModificationOperation(StrEnum):
    """Supported controlled artifact modification operations."""

    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class ArtifactLocation:
    """Precise location within a Project0 repository artifact."""

    location_id: str
    repository_path: str
    location_type: ArtifactLocationType
    locator: str
    start_line: int | None = None
    end_line: int | None = None
    content_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactModification:
    """Controlled modification request for an artifact location."""

    location: ArtifactLocation
    operation: ArtifactModificationOperation
    content: str
