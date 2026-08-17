# ============================================================
# Project0 - Markdown Locator
#
# File: markdown_locator.py
#
# Purpose:
#     Provide Markdown artifact location discovery for Project0
#     artifact understanding capabilities.
#
# ============================================================

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from project0.models.artifact_models import (
    ArtifactLocation,
    ArtifactLocationType,
)


class MarkdownLocator:
    """Locate structural modification points within Markdown artifacts."""

    def locate_sections(
        self,
        artifact_path: Path,
    ) -> tuple[ArtifactLocation, ...]:
        """Return Markdown section locations within an artifact."""

        content = artifact_path.read_text(
            encoding="utf-8",
        )

        lines = content.splitlines()

        locations: list[ArtifactLocation] = []

        current_heading: str | None = None
        current_start: int | None = None

        for index, line in enumerate(lines, start=1):
            if line.startswith("#"):
                if current_heading is not None:
                    locations.append(
                        self._create_location(
                            artifact_path,
                            current_heading,
                            current_start,
                            index - 1,
                            lines,
                        )
                    )

                current_heading = line.lstrip("#").strip()
                current_start = index

        if current_heading is not None:
            locations.append(
                self._create_location(
                    artifact_path,
                    current_heading,
                    current_start,
                    len(lines),
                    lines,
                )
            )

        return tuple(locations)

    def _create_location(
        self,
        artifact_path: Path,
        heading: str,
        start_line: int | None,
        end_line: int | None,
        lines: list[str],
    ) -> ArtifactLocation:
        """Create an artifact location for one Markdown section."""

        selected_lines = lines[
            (start_line or 1) - 1 : end_line
        ]

        content = "\n".join(selected_lines)

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        return ArtifactLocation(
            location_id=str(uuid4()),
            repository_path=str(artifact_path),
            location_type=ArtifactLocationType.SECTION,
            locator=heading,
            start_line=start_line,
            end_line=end_line,
            content_hash=content_hash,
        )
