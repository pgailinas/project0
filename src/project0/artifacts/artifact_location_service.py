# ============================================================
# Project0 - Artifact Location Service
#
# File: artifact_location_service.py
#
# Purpose:
#     Provide the platform service layer for discovering and
#     validating precise artifact locations used by controlled
#     modification workflows.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

from project0.artifacts.markdown_locator import MarkdownLocator
from project0.models.artifact_models import ArtifactLocation


class ArtifactLocationService:
    """Platform service for artifact location discovery and validation."""

    def __init__(
        self,
        markdown_locator: MarkdownLocator | None = None,
    ) -> None:
        self._markdown_locator = (
            markdown_locator
            if markdown_locator is not None
            else MarkdownLocator()
        )

    def discover_locations(
        self,
        artifact_path: Path,
        request: str,
    ) -> tuple[ArtifactLocation, ...]:
        """Discover one unambiguous location within an artifact.

        Markdown section discovery is narrowed using the supplied
        request. A section is returned only when exactly one heading
        is explicitly referenced by the request. Ambiguous or
        unmatched requests fail closed by returning no location.
        """

        if artifact_path.suffix.lower() not in {".md", ".markdown"}:
            return ()

        locations = self._markdown_locator.locate_sections(
            artifact_path
        )
        normalized_request = request.casefold()

        matching_locations = tuple(
            location
            for location in locations
            if location.locator.strip().casefold()
            and location.locator.strip().casefold()
            in normalized_request
        )

        if len(matching_locations) != 1:
            return ()

        return matching_locations

    def validate_location(
        self,
        location: ArtifactLocation,
    ) -> bool:
        """Validate that an artifact location remains usable."""

        artifact_path = Path(location.repository_path)

        if not artifact_path.exists():
            return False

        if location.start_line is None:
            return True

        lines = artifact_path.read_text(
            encoding="utf-8",
        ).splitlines()

        return location.start_line <= len(lines)
