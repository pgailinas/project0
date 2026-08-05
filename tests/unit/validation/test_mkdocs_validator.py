# ============================================================
# Project0 - MkDocs Validator Tests
#
# File: test_mkdocs_validator.py
#
# Purpose:
#     Verify deterministic MkDocs build validation used by
#     Project0 validation components.
#
# ============================================================

from pathlib import Path
import subprocess

from project0.models.validation_models import (
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
)
from project0.validation.mkdocs_validator import MkDocsValidator


def test_successful_mkdocs_build_passes(tmp_path: Path) -> None:
    """A successful MkDocs build with no warnings passes validation."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        assert command == (
            "mkdocs",
            "build",
            "--strict",
            "--config-file",
            str(config_path),
        )
        assert working_directory == tmp_path.resolve()

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="INFO - Documentation built successfully.\n",
            stderr="",
        )

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )
    request = ValidationRequest(target_paths=("docs/index.md",))

    result = validator.validate(request)

    assert result.validator_name == "mkdocs"
    assert result.status is ValidationStatus.PASSED
    assert len(result.issues) == 1
    assert result.issues[0].severity is ValidationSeverity.INFO
    assert result.issues[0].code == "mkdocs-output"
    assert result.error_message is None


def test_successful_build_with_warning_passes_with_warnings(
    tmp_path: Path,
) -> None:
    """A successful MkDocs build with warnings returns warning status."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="WARNING - A documentation file is not in the nav.\n",
        )

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert len(result.issues) == 1
    assert result.issues[0].severity is ValidationSeverity.WARNING
    assert result.issues[0].message == (
        "WARNING - A documentation file is not in the nav."
    )


def test_failed_mkdocs_build_returns_failed_status(tmp_path: Path) -> None:
    """A nonzero MkDocs exit code produces a failed result."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="ERROR - Configuration error.\n",
        )

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert any(
        issue.code == "mkdocs-build-failed"
        and issue.severity is ValidationSeverity.ERROR
        for issue in result.issues
    )
    assert any(
        issue.code == "mkdocs-output"
        and issue.severity is ValidationSeverity.ERROR
        for issue in result.issues
    )


def test_missing_mkdocs_configuration_fails(tmp_path: Path) -> None:
    """A missing mkdocs.yml file produces a failed result."""

    validator = MkDocsValidator(repository_root=tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "mkdocs-config-not-found"
    assert result.issues[0].severity is ValidationSeverity.ERROR
    assert result.issues[0].repository_path == "mkdocs.yml"


def test_command_execution_error_fails(tmp_path: Path) -> None:
    """An operating-system error while starting MkDocs is reported."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del command
        del working_directory

        raise FileNotFoundError("mkdocs command not found")

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].code == "mkdocs-execution-error"
    assert result.issues[0].severity is ValidationSeverity.ERROR
    assert result.error_message == "mkdocs command not found"


def test_empty_command_output_passes(tmp_path: Path) -> None:
    """A successful build with no output passes validation."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

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

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED
    assert result.issues == ()


def test_blank_output_lines_are_ignored(tmp_path: Path) -> None:
    """Blank MkDocs output lines do not create validation issues."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="\nINFO - Build complete.\n\n",
            stderr="\n",
        )

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED
    assert len(result.issues) == 1
    assert result.issues[0].message == "INFO - Build complete."


def test_warning_in_stdout_is_classified_as_warning(
    tmp_path: Path,
) -> None:
    """Warning text in standard output is classified correctly."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="WARNING - Navigation warning.\n",
            stderr="",
        )

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert len(result.issues) == 1
    assert result.issues[0].severity is ValidationSeverity.WARNING


def test_error_text_with_zero_exit_code_fails(tmp_path: Path) -> None:
    """Error output produces failure even when the exit code is zero."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

    def command_runner(
        command: tuple[str, ...],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        del working_directory

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ERROR - Unexpected build condition.\n",
            stderr="",
        )

    validator = MkDocsValidator(
        repository_root=tmp_path,
        command_runner=command_runner,
    )

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.issues) == 1
    assert result.issues[0].severity is ValidationSeverity.ERROR


def test_default_runner_uses_subprocess_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The default command runner invokes subprocess.run correctly."""

    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Project0\n", encoding="utf-8")

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

    validator = MkDocsValidator(repository_root=tmp_path)

    result = validator.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.PASSED
    assert captured["command"] == (
        "mkdocs",
        "build",
        "--strict",
        "--config-file",
        str(config_path),
    )
    assert captured["cwd"] == tmp_path.resolve()
    assert captured["check"] is False
    assert captured["capture_output"] is True
    assert captured["text"] is True
