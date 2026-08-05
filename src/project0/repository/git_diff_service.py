# ============================================================
# Project0 - Git Diff Service
#
# File: git_diff_service.py
#
# Purpose:
#     Generate read-only Git diffs for selected Project0
#     repository paths.
#
# ============================================================

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
import subprocess


CommandRunner = Callable[
    [Sequence[str], Path],
    subprocess.CompletedProcess[str],
]


class GitDiffService:
    """Generate read-only Git diffs for repository paths."""

    def __init__(
        self,
        repository_root: Path,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._command_runner = command_runner or self._run_command

    def generate_diff(
        self,
        repository_paths: tuple[str, ...] = (),
    ) -> str:
        """Generate a Git diff for selected repository paths."""

        normalized_paths = tuple(
            self._normalize_repository_path(repository_path)
            for repository_path in repository_paths
        )

        command: list[str] = [
            "git",
            "diff",
            "--no-ext-diff",
            "--",
        ]
        command.extend(normalized_paths)

        completed_process = self._command_runner(
            tuple(command),
            self._repository_root,
        )

        if completed_process.returncode != 0:
            error_message = (
                completed_process.stderr.strip()
                or completed_process.stdout.strip()
                or (
                    "Git diff failed with exit code "
                    f"{completed_process.returncode}."
                )
            )

            raise RuntimeError(error_message)

        return completed_process.stdout

    def _normalize_repository_path(
        self,
        repository_path: str,
    ) -> str:
        """Normalize and validate one repository-relative path."""

        normalized_path = repository_path.strip()

        if not normalized_path:
            raise ValueError("Repository paths must not be empty.")

        candidate_path = (
            self._repository_root / normalized_path
        ).resolve()

        if not self._is_within_repository(candidate_path):
            raise ValueError(
                "Repository paths must remain within the repository root."
            )

        return candidate_path.relative_to(
            self._repository_root
        ).as_posix()

    def _is_within_repository(self, file_path: Path) -> bool:
        """Return whether a path is contained by the repository root."""

        try:
            file_path.relative_to(self._repository_root)
        except ValueError:
            return False

        return True

    @staticmethod
    def _run_command(
        command: Sequence[str],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        """Run a Git command and capture its text output."""

        return subprocess.run(
            command,
            cwd=working_directory,
            check=False,
            capture_output=True,
            text=True,
        )
