# ============================================================
# Project0 - Repository Update Service Tests
#
# File: test_repository_update_service.py
#
# Purpose:
#     Verify safe application of individually approved Markdown
#     documentation changes within the Project0 repository.
#
# ============================================================

from datetime import UTC
from pathlib import Path

import pytest

from project0.models.artifact_models import (
    ArtifactLocation,
    ArtifactLocationType,
)
from project0.models.documentation_workflow_models import (
    ChangeApplicationStatus,
    DocumentationAnchorMode,
    DocumentationChangeProposal,
    DocumentationReview,
    ReviewDecision,
)
from project0.repository.repository_update_service import (
    RepositoryUpdateService,
    apply_documentation_change,
)


def _proposal(
    *,
    repository_path: str = "docs/index.md",
    original_content: str = "# Original\n",
    proposed_content: str = "# Updated\n",
    anchor_text: str | None = None,
    artifact_location: ArtifactLocation | None = None,
    anchor_mode: DocumentationAnchorMode = DocumentationAnchorMode.REPLACE,
    proposal_id: str = "proposal-001",
) -> DocumentationChangeProposal:
    """Create a standard documentation change proposal."""

    return DocumentationChangeProposal(
        repository_path=repository_path,
        original_content=original_content,
        proposed_content=proposed_content,
        anchor_text=anchor_text,
        artifact_location=artifact_location,
        anchor_mode=anchor_mode,
        rationale="Update the documentation.",
        proposal_id=proposal_id,
    )


def _review(
    *,
    decision: ReviewDecision = ReviewDecision.APPROVE,
    proposal_id: str = "proposal-001",
) -> DocumentationReview:
    """Create a standard documentation review."""

    return DocumentationReview(
        proposal_id=proposal_id,
        decision=decision,
    )


def test_apply_documentation_change_creates_candidate_content() -> None:
    """The shared edit helper creates the expected candidate content."""

    original = (
        "# Documentation\n\n"
        "## Phase 8\n\n"
        "Existing text.\n"
    )

    candidate = apply_documentation_change(
        original_content=original,
        proposed_content="Updated text.",
        anchor_text="Existing text.",
    )

    assert candidate == (
        "# Documentation\n\n"
        "## Phase 8\n\n"
        "Updated text.\n"
    )


def test_apply_documentation_change_insert_after_anchor_preserves_heading() -> None:
    """An insert-after change preserves the Markdown anchor text."""

    original = (
        "# Documentation\n\n"
        "Implemented:\n\n"
        "- Existing item.\n"
    )

    candidate = apply_documentation_change(
        original_content=original,
        proposed_content="- New item.",
        anchor_text="Implemented:",
        anchor_mode=DocumentationAnchorMode.INSERT_AFTER,
    )

    assert candidate == (
        "# Documentation\n\n"
        "Implemented:\n\n"
        "- New item.\n"
        "- Existing item.\n"
    )



def test_approved_markdown_change_is_applied(tmp_path: Path) -> None:
    """An approved Markdown proposal updates the repository file."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert result.proposal_id == "proposal-001"
    assert result.repository_path == "docs/index.md"
    assert result.applied_at is not None
    assert result.applied_at.tzinfo is UTC
    assert result.error_message is None
    assert file_path.read_text(encoding="utf-8") == "# Updated\n"


def test_anchored_change_updates_only_target_content(
    tmp_path: Path,
) -> None:
    """An anchored proposal updates only the targeted location."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()

    original = (
        "# Documentation\n\n"
        "## Phase 8\n\n"
        "Existing text.\n\n"
        "## Phase 9\n\n"
        "Unchanged text.\n"
    )

    file_path.write_text(
        original,
        encoding="utf-8",
    )

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            original_content=original,
            proposed_content="Updated Phase 8 text.",
            anchor_text="Existing text.",
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert file_path.read_text(encoding="utf-8") == (
        "# Documentation\n\n"
        "## Phase 8\n\n"
        "Updated Phase 8 text.\n\n"
        "## Phase 9\n\n"
        "Unchanged text.\n"
    )


def test_missing_anchor_text_fails(
    tmp_path: Path,
) -> None:
    """An anchored proposal fails when the anchor is absent."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text(
        "# Original\n",
        encoding="utf-8",
    )

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            anchor_text="## Missing Section",
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "Unable to update the documentation file: "
        "The documentation anchor text was not found."
    )



def test_duplicate_anchor_text_fails(
    tmp_path: Path,
) -> None:
    """An ambiguous anchor does not update the document."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()

    original = (
        "# Documentation\n\n"
        "## Phase 8\n\n"
        "First occurrence.\n\n"
        "## Phase 8\n\n"
        "Second occurrence.\n"
    )

    file_path.write_text(
        original,
        encoding="utf-8",
    )

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            original_content=original,
            proposed_content="Updated content.",
            anchor_text="## Phase 8",
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "Unable to update the documentation file: "
        "The documentation anchor text is ambiguous."
    )
    assert file_path.read_text(encoding="utf-8") == original




@pytest.mark.parametrize(
    "decision",
    [
        ReviewDecision.REVISE,
        ReviewDecision.REJECT,
        ReviewDecision.SKIP,
    ],
)
def test_non_approved_change_is_skipped(
    tmp_path: Path,
    decision: ReviewDecision,
) -> None:
    """A non-approved proposal is skipped without modifying the file."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(decision=decision),
    )

    assert result.status is ChangeApplicationStatus.SKIPPED
    assert result.applied_at is None
    assert result.error_message is None
    assert file_path.read_text(encoding="utf-8") == "# Original\n"


def test_mismatched_proposal_identifier_fails(tmp_path: Path) -> None:
    """A review for another proposal is rejected."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(proposal_id="proposal-999"),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "The review proposal identifier does not match "
        "the documentation proposal."
    )
    assert file_path.read_text(encoding="utf-8") == "# Original\n"


def test_path_outside_repository_fails(tmp_path: Path) -> None:
    """A proposal outside the repository root is rejected."""

    outside_path = tmp_path.parent / "outside.md"
    outside_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(repository_path="../outside.md"),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "The documentation path resolves outside "
        "the repository root."
    )
    assert outside_path.read_text(encoding="utf-8") == "# Original\n"


def test_non_markdown_file_fails(tmp_path: Path) -> None:
    """Only Markdown files may be updated."""

    file_path = tmp_path / "docs/config.txt"
    file_path.parent.mkdir()
    file_path.write_text("original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            repository_path="docs/config.txt",
            original_content="original\n",
            proposed_content="updated\n",
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "Only Markdown documentation files may be updated."
    )
    assert file_path.read_text(encoding="utf-8") == "original\n"


def test_missing_documentation_file_fails(tmp_path: Path) -> None:
    """A proposal for a missing Markdown file fails."""

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "The documentation file does not exist."
    )


def test_stale_original_content_fails(tmp_path: Path) -> None:
    """A changed file is not overwritten by a stale proposal."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Newer Content\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(original_content="# Original\n"),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "The documentation file has changed since the proposal "
        "was created."
    )
    assert file_path.read_text(encoding="utf-8") == "# Newer Content\n"


def test_identical_content_can_be_applied(tmp_path: Path) -> None:
    """An approved no-op proposal still returns applied status."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            original_content="# Original\n",
            proposed_content="# Original\n",
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert file_path.read_text(encoding="utf-8") == "# Original\n"


def test_read_error_returns_failed_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file read error is converted into a failed result."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    original_read_text = Path.read_text

    def failing_read_text(
        self: Path,
        *args,
        **kwargs,
    ) -> str:
        if self == file_path.resolve():
            raise OSError("read failed")

        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read_text)

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "Unable to read the documentation file: read failed"
    )


def test_write_error_returns_failed_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An atomic write error is converted into a failed result."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    def failing_write_atomically(
        *,
        file_path: Path,
        content: str,
    ) -> None:
        del file_path
        del content
        raise OSError("write failed")

    monkeypatch.setattr(
        service,
        "_write_atomically",
        failing_write_atomically,
    )

    result = service.apply(
        proposal=_proposal(),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.error_message == (
        "Unable to update the documentation file: write failed"
    )
    assert file_path.read_text(encoding="utf-8") == "# Original\n"


def test_atomic_write_replaces_file_content(tmp_path: Path) -> None:
    """Atomic writing replaces content without leaving temp files."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(proposed_content="# Replacement\n"),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert file_path.read_text(encoding="utf-8") == "# Replacement\n"

    temporary_files = tuple(
        file_path.parent.glob(f".{file_path.name}.*.tmp")
    )
    assert temporary_files == ()


def test_failed_result_has_no_applied_timestamp(tmp_path: Path) -> None:
    """A failed change does not receive an applied timestamp."""

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
    assert result.applied_at is None


def test_skipped_result_has_no_applied_timestamp(tmp_path: Path) -> None:
    """A skipped change does not receive an applied timestamp."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Original\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(),
        review=_review(decision=ReviewDecision.SKIP),
    )

    assert result.status is ChangeApplicationStatus.SKIPPED
    assert result.applied_at is None


def test_artifact_location_change_updates_target_lines(
    tmp_path: Path,
) -> None:
    """An artifact location updates the precise target range."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()

    original = (
        "# Documentation\n\n"
        "## Phase 8\n\n"
        "Old content.\n\n"
        "## Phase 9\n\n"
        "Unchanged content.\n"
    )

    file_path.write_text(original, encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            original_content=original,
            proposed_content="New content.\n",
            artifact_location=ArtifactLocation(
                location_id="phase8-content",
                repository_path="docs/index.md",
                location_type=ArtifactLocationType.LINE_RANGE,
                locator="Phase 8 content",
                start_line=5,
                end_line=5,
            ),
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert "New content." in file_path.read_text(encoding="utf-8")


def test_artifact_location_insert_after_preserves_target_lines(
    tmp_path: Path,
) -> None:
    """An insert-after artifact edit preserves the located content."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()

    original = (
        "# Documentation\n"
        "## Existing Context\n"
        "Existing details.\n"
        "## Next Section\n"
        "Next details.\n"
    )

    file_path.write_text(original, encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            original_content=original,
            proposed_content="New context detail.",
            anchor_mode=DocumentationAnchorMode.INSERT_AFTER,
            artifact_location=ArtifactLocation(
                location_id="context-heading",
                repository_path="docs/index.md",
                location_type=ArtifactLocationType.LINE_RANGE,
                locator="Existing Context",
                start_line=2,
                end_line=2,
            ),
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert file_path.read_text(encoding="utf-8") == (
        "# Documentation\n"
        "## Existing Context\n"
        "New context detail.\n"
        "Existing details.\n"
        "## Next Section\n"
        "Next details.\n"
    )


def test_artifact_location_replace_behavior_is_preserved(
    tmp_path: Path,
) -> None:
    """Artifact replacement still replaces the exact located range."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()

    original = (
        "# Documentation\n"
        "Old detail.\n"
        "Unchanged detail.\n"
    )

    file_path.write_text(original, encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            original_content=original,
            proposed_content="New detail.",
            anchor_mode=DocumentationAnchorMode.REPLACE,
            artifact_location=ArtifactLocation(
                location_id="detail",
                repository_path="docs/index.md",
                location_type=ArtifactLocationType.LINE_RANGE,
                locator="Old detail",
                start_line=2,
                end_line=2,
            ),
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.APPLIED
    assert file_path.read_text(encoding="utf-8") == (
        "# Documentation\n"
        "New detail.\n"
        "Unchanged detail.\n"
    )


def test_artifact_location_invalid_range_fails(
    tmp_path: Path,
) -> None:
    """Invalid artifact ranges fail safely."""

    file_path = tmp_path / "docs/index.md"
    file_path.parent.mkdir()
    file_path.write_text("# Documentation\n", encoding="utf-8")

    service = RepositoryUpdateService(tmp_path)

    result = service.apply(
        proposal=_proposal(
            artifact_location=ArtifactLocation(
                location_id="invalid",
                repository_path="docs/index.md",
                location_type=ArtifactLocationType.LINE_RANGE,
                locator="invalid",
                start_line=100,
                end_line=110,
            ),
        ),
        review=_review(),
    )

    assert result.status is ChangeApplicationStatus.FAILED
