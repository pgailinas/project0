# ============================================================
# Project0 - Artifact Interfaces
#
# File: artifact_interfaces.py
#
# Purpose:
#     Define shared interfaces used by Project0 artifact
#     location and controlled modification capabilities.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from project0.models.artifact_models import ArtifactLocation


class ArtifactLocatorInterface(Protocol):
    """Interface for locating valid modification locations within artifacts."""

    def locate(
        self,
        artifact_path: Path,
        request: str,
    ) -> tuple[ArtifactLocation, ...]:
        """Return valid artifact locations matching a requested change."""


class ArtifactLocationServiceInterface(Protocol):
    """Interface for artifact location discovery and validation services."""

    def discover_locations(
        self,
        artifact_path: Path,
        request: str,
    ) -> tuple[ArtifactLocation, ...]:
        """Discover valid locations within an artifact."""

    def validate_location(
        self,
        location: ArtifactLocation,
    ) -> bool:
        """Validate that an artifact location is still usable."""
