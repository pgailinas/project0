# ============================================================
# Project0 - MkDocs Validator
#
# File: mkdocs_validator.py
#
# Purpose:
#     Validate the Project0 MkDocs documentation build and
#     return structured validation results.
#
# ============================================================

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
import re
import subprocess

from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)


CommandRunner = Callable[
    [Sequence[str], Path],
    subprocess.CompletedProcess[str],
]


ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"
)


class MkDocsValidator:
    """Validate the repository MkDocs build."""

    validator_name = "mkdocs"

    def __init__(
        self,
        repository_root: Path,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._command_runner = command_runner or self._run_command

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Run the MkDocs build and return a structured result."""

        del request

        started_at = datetime.now(UTC)
        issues: list[ValidationIssue] = []

        config_path = self._repository_root / "mkdocs.yml"

        if not config_path.is_file():
            issues.append(
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="mkdocs-config-not-found",
                    message="The repository does not contain mkdocs.yml.",
                    repository_path="mkdocs.yml",
                )
            )

            completed_at = datetime.now(UTC)

            return ValidatorResult(
                validator_name=self.validator_name,
                status=ValidationStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                issues=tuple(issues),
            )

        try:
            completed_process = self._command_runner(
                (
                    "mkdocs",
                    "build",
                    "--strict",
                    "--config-file",
                    str(config_path),
                ),
                self._repository_root,
            )
        except OSError as exc:
            completed_at = datetime.now(UTC)

            return ValidatorResult(
                validator_name=self.validator_name,
                status=ValidationStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                issues=(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="mkdocs-execution-error",
                        message=f"Unable to execute MkDocs: {exc}",
                        repository_path="mkdocs.yml",
                    ),
                ),
                error_message=str(exc),
            )

        issues.extend(
            self._parse_output(
                completed_process.stdout,
                ValidationSeverity.INFO,
            )
        )
        issues.extend(
            self._parse_output(
                completed_process.stderr,
                ValidationSeverity.WARNING,
            )
        )

        if completed_process.returncode != 0:
            issues.append(
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="mkdocs-build-failed",
                    message=(
                        "MkDocs build failed with exit code "
                        f"{completed_process.returncode}."
                    ),
                    repository_path="mkdocs.yml",
                )
            )

        completed_at = datetime.now(UTC)

        return ValidatorResult(
            validator_name=self.validator_name,
            status=self._determine_status(
                issues=issues,
                returncode=completed_process.returncode,
            ),
            started_at=started_at,
            completed_at=completed_at,
            issues=tuple(issues),
        )

    def _parse_output(
        self,
        output: str,
        default_severity: ValidationSeverity,
    ) -> list[ValidationIssue]:
        """Convert MkDocs output lines into structured issues."""

        issues: list[ValidationIssue] = []

        for line in output.splitlines():
            message = ANSI_ESCAPE_PATTERN.sub("", line).strip()

            if not message or self._is_decorative_output(message):
                continue

            normalized_message = message.casefold()

            if self._is_material_mkdocs_advisory(message):
                continue

            severity = default_severity

            if normalized_message.startswith("error"):
                severity = ValidationSeverity.ERROR
            elif normalized_message.startswith("warning"):
                severity = ValidationSeverity.WARNING
            elif normalized_message.startswith("info"):
                severity = ValidationSeverity.INFO

            issues.append(
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=severity,
                    code="mkdocs-output",
                    message=message,
                    repository_path="mkdocs.yml",
                )
            )

        return issues

    @staticmethod
    def _is_decorative_output(message: str) -> bool:
        """Return whether MkDocs output contains only decoration."""

        return not any(character.isalnum() for character in message)

    @staticmethod
    def _is_material_mkdocs_advisory(message: str) -> bool:
        """Return whether output belongs to the Material MkDocs 2.0 advisory."""

        normalized_message = message.casefold()

        advisory_fragments = (
            "warning from the material for mkdocs team",
            "mkdocs 2.0, the underlying framework of material for mkdocs",
            "will introduce backward-incompatible changes, including",
            "all plugins will stop working",
            "all theme overrides will break",
            "no migration path exists",
            "closed contribution model",
            "currently unlicensed",
            "our full analysis:",
            "squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/",
        )

        return any(
            fragment in normalized_message
            for fragment in advisory_fragments
        )

    @staticmethod
    def _determine_status(
        issues: list[ValidationIssue],
        returncode: int,
    ) -> ValidationStatus:
        """Determine the MkDocs validation status."""

        if returncode != 0:
            return ValidationStatus.FAILED

        if any(
            issue.severity is ValidationSeverity.ERROR
            for issue in issues
        ):
            return ValidationStatus.FAILED

        if any(
            issue.severity is ValidationSeverity.WARNING
            for issue in issues
        ):
            return ValidationStatus.PASSED_WITH_WARNINGS

        return ValidationStatus.PASSED

    @staticmethod
    def _run_command(
        command: Sequence[str],
        working_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command and capture its text output."""

        return subprocess.run(
            command,
            cwd=working_directory,
            check=False,
            capture_output=True,
            text=True,
        )
