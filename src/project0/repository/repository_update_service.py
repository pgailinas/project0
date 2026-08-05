# ============================================================
# Project0 - Repository Update Service
#
# File: repository_update_service.py
#
# Purpose:
#     Apply individually approved Markdown documentation changes
#     within the configured Project0 repository.
#
# ============================================================

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import tempfile

from project0.models.documentation_workflow_models import (
    AppliedDocumentationChange,
    ChangeApplicationStatus,
    DocumentationChangeProposal,
    DocumentationReview,
    ReviewDecision,
)


class RepositoryUpdateService:
    """Apply approved Markdown changes within a repository."""

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root.resolve()

    def apply(
        self,
        proposal: DocumentationChangeProposal,
        review: DocumentationReview,
    ) -> AppliedDocumentationChange:
        """Apply one reviewed documentation change."""

        if review.proposal_id != proposal.proposal_id:
            return self._failed_result(
                proposal=proposal,
                message=(
                    "The review proposal identifier does not match "
                    "the documentation proposal."
                ),
            )

        if review.decision is not ReviewDecision.APPROVE:
            return AppliedDocumentationChange(
                proposal_id=proposal.proposal_id,
                repository_path=proposal.repository_path,
                status=ChangeApplicationStatus.SKIPPED,
            )

        file_path = (
            self._repository_root / proposal.repository_path
        ).resolve()

        if not self._is_within_repository(file_path):
            return self._failed_result(
                proposal=proposal,
                message=(
                    "The documentation path resolves outside "
                    "the repository root."
                ),
            )

        if file_path.suffix.lower() != ".md":
            return self._failed_result(
                proposal=proposal,
                message="Only Markdown documentation files may be updated.",
            )

        if not file_path.is_file():
            return self._failed_result(
                proposal=proposal,
                message="The documentation file does not exist.",
            )

        try:
            current_content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            return self._failed_result(
                proposal=proposal,
                message=f"Unable to read the documentation file: {exc}",
            )

        if current_content != proposal.original_content:
            return self._failed_result(
                proposal=proposal,
                message=(
                    "The documentation file has changed since the proposal "
                    "was created."
                ),
            )

        try:
            self._write_atomically(
                file_path=file_path,
                content=proposal.proposed_content,
            )
        except OSError as exc:
            return self._failed_result(
                proposal=proposal,
                message=f"Unable to update the documentation file: {exc}",
            )

        return AppliedDocumentationChange(
            proposal_id=proposal.proposal_id,
            repository_path=proposal.repository_path,
            status=ChangeApplicationStatus.APPLIED,
            applied_at=datetime.now(UTC),
        )

    def _write_atomically(
        self,
        file_path: Path,
        content: str,
    ) -> None:
        """Write content using a temporary file and atomic replacement."""

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=file_path.parent,
                prefix=f".{file_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(content)
                temporary_file.flush()
                temporary_path = Path(temporary_file.name)

            temporary_path.replace(file_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def _is_within_repository(self, file_path: Path) -> bool:
        """Return whether a path is contained by the repository root."""

        try:
            file_path.relative_to(self._repository_root)
        except ValueError:
            return False

        return True

    @staticmethod
    def _failed_result(
        proposal: DocumentationChangeProposal,
        message: str,
    ) -> AppliedDocumentationChange:
        """Return a failed documentation change result."""

        return AppliedDocumentationChange(
            proposal_id=proposal.proposal_id,
            repository_path=proposal.repository_path,
            status=ChangeApplicationStatus.FAILED,
            error_message=message,
        )
