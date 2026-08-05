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

from project0.models.documentation_workflow_models import (
    ChangeApplicationStatus,
    DocumentationChangeProposal,
    DocumentationReview,
    ReviewDecision,
)
from project0.repository.repository_update_service import (
    RepositoryUpdateService,
)


def _proposal(
    *,
    repository_path: str = "docs/index.md",
    original_content: str = "# Original\n",
    proposed_content: str = "# Updated\n",
    proposal_id: str = "proposal-001",
) -> DocumentationChangeProposal:
    """Create a standard documentation change proposal."""

    return DocumentationChangeProposal(
        repository_path=repository_path,
        original_content=original_content,
        proposed_content=proposed_content,
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
