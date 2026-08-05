# ============================================================
# Project0 - Git Diff Service Tests
#
# File: test_git_diff_service.py
#
# Purpose:
#     Verify read-only Git diff generation for selected Project0
#     repository paths.
#
# ============================================================

from pathlib import Path
import subprocess

import pytest

from project0.repository.git_diff_service import GitDiffService


def test_generate_full_repository_diff(tmp_path: Path) -> None:
    """An empty path collection generates the full repository diff."""

    captured: dict[str, object] = {}

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["working_directory"] = working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="diff --git a/docs/index.md b/docs/index.md\n",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = service.generate_diff()

    assert result == "diff --git a/docs/index.md b/docs/index.md\n"
    assert captured["command"] == (
        "git",
        "diff",
        "--no-ext-diff",
        "--",
    )
    assert captured["working_directory"] == tmp_path.resolve()


def test_generate_diff_for_selected_paths(tmp_path: Path) -> None:
    """Selected repository paths are appended to the Git command."""

    captured: dict[str, object] = {}

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["working_directory"] = working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="selected diff\n",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = service.generate_diff(
        repository_paths=(
            "docs/index.md",
            "docs/Testing_Guide.md",
        )
    )

    assert result == "selected diff\n"
    assert captured["command"] == (
        "git",
        "diff",
        "--no-ext-diff",
        "--",
        "docs/index.md",
        "docs/Testing_Guide.md",
    )


def test_repository_paths_are_normalized(tmp_path: Path) -> None:
    """Repository paths are stripped and normalized to POSIX format."""

    captured: dict[str, object] = {}

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory
        captured["command"] = command

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    service.generate_diff(
        repository_paths=("  docs/section/../index.md  ",)
    )

    assert captured["command"] == (
        "git",
        "diff",
        "--no-ext-diff",
        "--",
        "docs/index.md",
    )


def test_absolute_path_inside_repository_is_normalized(
    tmp_path: Path,
) -> None:
    """An absolute path inside the repository becomes relative."""

    target_path = tmp_path / "docs/index.md"

    captured: dict[str, object] = {}

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory
        captured["command"] = command

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    service.generate_diff(repository_paths=(str(target_path),))

    assert captured["command"] == (
        "git",
        "diff",
        "--no-ext-diff",
        "--",
        "docs/index.md",
    )


def test_empty_repository_path_raises_value_error(
    tmp_path: Path,
) -> None:
    """An empty selected repository path is rejected."""

    service = GitDiffService(repository_root=tmp_path)

    with pytest.raises(
        ValueError,
        match="Repository paths must not be empty.",
    ):
        service.generate_diff(repository_paths=("   ",))


def test_path_outside_repository_raises_value_error(
    tmp_path: Path,
) -> None:
    """A path outside the repository root is rejected."""

    service = GitDiffService(repository_root=tmp_path)

    with pytest.raises(
        ValueError,
        match=(
            "Repository paths must remain within the repository root."
        ),
    ):
        service.generate_diff(repository_paths=("../outside.md",))


def test_git_failure_uses_standard_error_message(
    tmp_path: Path,
) -> None:
    """Git standard error is used when the command fails."""

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository\n",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    with pytest.raises(
        RuntimeError,
        match="fatal: not a git repository",
    ):
        service.generate_diff()


def test_git_failure_falls_back_to_standard_output(
    tmp_path: Path,
) -> None:
    """Git standard output is used when standard error is empty."""

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="Git diff failed.\n",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    with pytest.raises(
        RuntimeError,
        match="Git diff failed.",
    ):
        service.generate_diff()


def test_git_failure_uses_exit_code_fallback(
    tmp_path: Path,
) -> None:
    """The exit code is reported when Git produces no output."""

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=2,
            stdout="",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    with pytest.raises(
        RuntimeError,
        match="Git diff failed with exit code 2.",
    ):
        service.generate_diff()


def test_empty_diff_output_is_returned(tmp_path: Path) -> None:
    """A clean repository returns an empty diff string."""

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    assert service.generate_diff() == ""


def test_duplicate_repository_paths_are_preserved(
    tmp_path: Path,
) -> None:
    """Selected path ordering and duplicates are preserved."""

    captured: dict[str, object] = {}

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory
        captured["command"] = command

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    service = GitDiffService(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    service.generate_diff(
        repository_paths=(
            "docs/index.md",
            "docs/index.md",
        )
    )

    assert captured["command"] == (
        "git",
        "diff",
        "--no-ext-diff",
        "--",
        "docs/index.md",
        "docs/index.md",
    )


def test_default_runner_uses_subprocess_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default command runner invokes subprocess.run correctly."""

    captured: dict[str, object] = {}

    def fake_run(
        command,
        *,
        cwd,
        check,
        capture_output,
        text,
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["check"] = check
        captured["capture_output"] = capture_output
        captured["text"] = text

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    service = GitDiffService(repository_root=tmp_path)

    result = service.generate_diff(
        repository_paths=("docs/index.md",)
    )

    assert result == ""
    assert captured["command"] == (
        "git",
        "diff",
        "--no-ext-diff",
        "--",
        "docs/index.md",
    )
    assert captured["cwd"] == tmp_path.resolve()
    assert captured["check"] is False
    assert captured["capture_output"] is True
    assert captured["text"] is True
