# ============================================================
# Project0 - Artifact Location Service Tests
#
# File: test_artifact_location_service.py
#
# Purpose:
#     Validate artifact location discovery and validation
#     behavior provided by the Project0 artifact location
#     service layer.
#
# ============================================================

from pathlib import Path

from project0.artifacts.artifact_location_service import (
    ArtifactLocationService,
)
from project0.models.artifact_models import (
    ArtifactLocation,
    ArtifactLocationType,
)


def _create_markdown_document(
    tmp_path: Path,
) -> Path:
    """Create a sample Markdown artifact for testing."""

    document = tmp_path / "sample.md"

    document.write_text(
        """# Document Title

Introduction content.

## Workflow

Step one.

Step two.

## Validation

Validation content.
""",
        encoding="utf-8",
    )

    return document


def test_artifact_location_service_discovers_markdown_locations(
    tmp_path: Path,
) -> None:
    """Artifact location service discovers Markdown locations."""

    document = _create_markdown_document(tmp_path)

    service = ArtifactLocationService()

    locations = service.discover_locations(
        document,
        "Update workflow documentation.",
    )

    assert len(locations) == 3
    assert locations[1].locator == "Workflow"
    assert (
        locations[1].location_type
        == ArtifactLocationType.SECTION
    )


def test_artifact_location_service_ignores_unsupported_files(
    tmp_path: Path,
) -> None:
    """Unsupported artifact types return no locations."""

    document = tmp_path / "sample.yaml"

    document.write_text(
        "configuration: value",
        encoding="utf-8",
    )

    service = ArtifactLocationService()

    locations = service.discover_locations(
        document,
        "Update configuration.",
    )

    assert locations == ()


def test_validate_location_fails_for_missing_artifact() -> None:
    """Missing artifact paths are invalid."""

    service = ArtifactLocationService()

    location = ArtifactLocation(
        location_id="location-missing",
        repository_path="missing/document.md",
        location_type=ArtifactLocationType.SECTION,
        locator="Workflow",
        start_line=1,
        end_line=5,
    )

    assert service.validate_location(location) is False


def test_validate_location_accepts_valid_line_range(
    tmp_path: Path,
) -> None:
    """Valid artifact locations pass validation."""

    document = _create_markdown_document(tmp_path)

    service = ArtifactLocationService()

    location = ArtifactLocation(
        location_id="location-valid",
        repository_path=str(document),
        location_type=ArtifactLocationType.SECTION,
        locator="Workflow",
        start_line=5,
        end_line=9,
    )

    assert service.validate_location(location) is True


def test_validate_location_accepts_file_without_line_range(
    tmp_path: Path,
) -> None:
    """Locations without line ranges validate when artifact exists."""

    document = _create_markdown_document(tmp_path)

    service = ArtifactLocationService()

    location = ArtifactLocation(
        location_id="location-file",
        repository_path=str(document),
        location_type=ArtifactLocationType.FILE,
        locator="sample.md",
    )

    assert service.validate_location(location) is True
