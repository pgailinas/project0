# ============================================================
# Project0 - Markdown Validator
#
# File: markdown_validator.py
#
# Purpose:
#     Validate basic Markdown document structure for Project0
#     repository documentation.
#
# ============================================================

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re

from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)


class MarkdownValidator:
    """Validate basic Markdown structure for repository documents."""

    validator_name = "markdown"

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root.resolve()

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Validate Markdown targets and return a structured result."""

        started_at = datetime.now(UTC)
        issues: list[ValidationIssue] = []

        for repository_path in request.target_paths:
            if not repository_path.lower().endswith(".md"):
                continue

            file_path = (self._repository_root / repository_path).resolve()

            if not self._is_within_repository(file_path):
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="path-outside-repository",
                        message="The validation target is outside the repository root.",
                        repository_path=repository_path,
                    )
                )
                continue

            if not file_path.is_file():
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="file-not-found",
                        message="The Markdown validation target does not exist.",
                        repository_path=repository_path,
                    )
                )
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError as exc:
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="file-read-error",
                        message=f"Unable to read the Markdown file: {exc}",
                        repository_path=repository_path,
                    )
                )
                continue

            issues.extend(
                self._validate_content(
                    repository_path=repository_path,
                    content=content,
                )
            )

        completed_at = datetime.now(UTC)

        return ValidatorResult(
            validator_name=self.validator_name,
            status=self._determine_status(issues),
            started_at=started_at,
            completed_at=completed_at,
            issues=tuple(issues),
        )

    def _validate_content(
        self,
        repository_path: str,
        content: str,
    ) -> list[ValidationIssue]:
        """Validate one Markdown document."""

        issues: list[ValidationIssue] = []
        headings: list[tuple[int, str, int]] = []
        inside_fenced_block = False

        if not content.strip():
            return [
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="empty-document",
                    message="The Markdown document is empty.",
                    repository_path=repository_path,
                )
            ]

        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()

            if stripped.startswith("```") or stripped.startswith("~~~"):
                inside_fenced_block = not inside_fenced_block
                continue

            if inside_fenced_block:
                continue

            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if match is None:
                continue

            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((level, title, line_number))

        level_one_headings = [heading for heading in headings if heading[0] == 1]

        if not level_one_headings:
            issues.append(
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="missing-document-title",
                    message="The Markdown document does not contain a level-one heading.",
                    repository_path=repository_path,
                )
            )
        elif len(level_one_headings) > 1:
            for _, _, line_number in level_one_headings[1:]:
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.WARNING,
                        code="multiple-document-titles",
                        message="The Markdown document contains multiple level-one headings.",
                        repository_path=repository_path,
                        line_number=line_number,
                    )
                )

        previous_level: int | None = None
        seen_headings: dict[str, int] = {}

        for level, title, line_number in headings:
            normalized_title = title.casefold()

            if normalized_title in seen_headings:
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.WARNING,
                        code="duplicate-heading",
                        message=f'Duplicate heading: "{title}".',
                        repository_path=repository_path,
                        line_number=line_number,
                    )
                )
            else:
                seen_headings[normalized_title] = line_number

            if previous_level is not None and level > previous_level + 1:
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.WARNING,
                        code="heading-level-skip",
                        message=(
                            f"Heading level jumps from {previous_level} "
                            f"to {level}."
                        ),
                        repository_path=repository_path,
                        line_number=line_number,
                    )
                )

            previous_level = level

        return issues

    def _is_within_repository(self, file_path: Path) -> bool:
        """Return whether a path is contained by the repository root."""

        try:
            file_path.relative_to(self._repository_root)
        except ValueError:
            return False

        return True

    @staticmethod
    def _determine_status(
        issues: list[ValidationIssue],
    ) -> ValidationStatus:
        """Determine the validator status from collected issues."""

        if any(
            issue.severity is ValidationSeverity.ERROR
            for issue in issues
        ):
            return ValidationStatus.FAILED

        if issues:
            return ValidationStatus.PASSED_WITH_WARNINGS

        return ValidationStatus.PASSED
