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
        """Discover valid locations within an artifact.

        Initial implementation supports Markdown artifacts.
        The request parameter is retained as part of the service
        contract for future location ranking and selection.
        """

        del request

        if artifact_path.suffix.lower() not in {".md", ".markdown"}:
            return ()

        return self._markdown_locator.locate_sections(
            artifact_path
        )

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
