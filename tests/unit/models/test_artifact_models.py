# ============================================================
# Project0 - Artifact Model Tests
#
# File: test_artifact_models.py
#
# Purpose:
#     Validate shared artifact location and controlled
#     modification data models used by Project0.
#
# ============================================================

import pytest

from project0.models.artifact_models import (
    ArtifactLocation,
    ArtifactLocationType,
    ArtifactModification,
    ArtifactModificationOperation,
)


def test_artifact_location_can_be_created() -> None:
    """Artifact locations can be created with required fields."""

    location = ArtifactLocation(
        location_id="location-001",
        repository_path="docs/example.md",
        location_type=ArtifactLocationType.SECTION,
        locator="Workflow",
        start_line=10,
        end_line=20,
        content_hash="abc123",
    )

    assert location.location_id == "location-001"
    assert location.repository_path == "docs/example.md"
    assert location.location_type == ArtifactLocationType.SECTION
    assert location.locator == "Workflow"
    assert location.start_line == 10
    assert location.end_line == 20
    assert location.content_hash == "abc123"


def test_artifact_location_supports_optional_line_information() -> None:
    """Artifact locations may omit optional range information."""

    location = ArtifactLocation(
        location_id="location-002",
        repository_path="docs/example.md",
        location_type=ArtifactLocationType.FILE,
        locator="example.md",
    )

    assert location.start_line is None
    assert location.end_line is None
    assert location.content_hash is None


def test_artifact_location_is_immutable() -> None:
    """Artifact locations cannot be modified after creation."""

    location = ArtifactLocation(
        location_id="location-003",
        repository_path="docs/example.md",
        location_type=ArtifactLocationType.SECTION,
        locator="Workflow",
    )

    with pytest.raises(AttributeError):
        location.locator = "Changed"


def test_artifact_modification_can_be_created() -> None:
    """Artifact modification requests can be created."""

    location = ArtifactLocation(
        location_id="location-004",
        repository_path="docs/example.md",
        location_type=ArtifactLocationType.SECTION,
        locator="Workflow",
    )

    modification = ArtifactModification(
        location=location,
        operation=ArtifactModificationOperation.INSERT,
        content="New workflow information.",
    )

    assert modification.location == location
    assert modification.operation == ArtifactModificationOperation.INSERT
    assert modification.content == "New workflow information."


@pytest.mark.parametrize(
    "location_type",
    [
        ArtifactLocationType.FILE,
        ArtifactLocationType.SECTION,
        ArtifactLocationType.HEADING,
        ArtifactLocationType.LINE_RANGE,
    ],
)
def test_supported_artifact_location_types(
    location_type: ArtifactLocationType,
) -> None:
    """All defined artifact location types are available."""

    assert location_type.value is not None


@pytest.mark.parametrize(
    "operation",
    [
        ArtifactModificationOperation.INSERT,
        ArtifactModificationOperation.REPLACE,
        ArtifactModificationOperation.DELETE,
    ],
)
def test_supported_artifact_modification_operations(
    operation: ArtifactModificationOperation,
) -> None:
    """All defined artifact modification operations are available."""

    assert operation.value is not None
