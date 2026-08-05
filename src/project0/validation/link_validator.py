# ============================================================
# Project0 - Link Validator
#
# File: link_validator.py
#
# Purpose:
#     Validate repository-relative links contained in Project0
#     Markdown documentation.
#
# ============================================================

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
from urllib.parse import unquote, urlparse

from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)


class LinkValidator:
    """Validate local links contained in repository Markdown files."""

    validator_name = "link"

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root.resolve()

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Validate local Markdown links and return a structured result."""

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
                    file_path=file_path,
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
        file_path: Path,
        content: str,
    ) -> list[ValidationIssue]:
        """Validate links contained in one Markdown document."""

        issues: list[ValidationIssue] = []
        inside_fenced_block = False

        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()

            if stripped.startswith("```") or stripped.startswith("~~~"):
                inside_fenced_block = not inside_fenced_block
                continue

            if inside_fenced_block:
                continue

            for link_target in self._extract_link_targets(line):
                issue = self._validate_link_target(
                    source_repository_path=repository_path,
                    source_file_path=file_path,
                    link_target=link_target,
                    line_number=line_number,
                )

                if issue is not None:
                    issues.append(issue)

        return issues

    def _validate_link_target(
        self,
        source_repository_path: str,
        source_file_path: Path,
        link_target: str,
        line_number: int,
    ) -> ValidationIssue | None:
        """Validate one Markdown link target."""

        normalized_target = link_target.strip()

        if not normalized_target:
            return ValidationIssue(
                validator_name=self.validator_name,
                severity=ValidationSeverity.WARNING,
                code="empty-link-target",
                message="The Markdown link target is empty.",
                repository_path=source_repository_path,
                line_number=line_number,
            )

        if self._is_external_target(normalized_target):
            return None

        parsed_target = urlparse(normalized_target)
        target_path = unquote(parsed_target.path)
        fragment = unquote(parsed_target.fragment)

        if not target_path:
            target_file_path = source_file_path
        elif target_path.startswith("/"):
            target_file_path = (
                self._repository_root / target_path.lstrip("/")
            ).resolve()
        else:
            target_file_path = (
                source_file_path.parent / target_path
            ).resolve()

        if not self._is_within_repository(target_file_path):
            return ValidationIssue(
                validator_name=self.validator_name,
                severity=ValidationSeverity.ERROR,
                code="link-outside-repository",
                message="The local link resolves outside the repository root.",
                repository_path=source_repository_path,
                line_number=line_number,
            )

        if not target_file_path.exists():
            return ValidationIssue(
                validator_name=self.validator_name,
                severity=ValidationSeverity.ERROR,
                code="missing-link-target",
                message=f'The local link target does not exist: "{normalized_target}".',
                repository_path=source_repository_path,
                line_number=line_number,
            )

        if fragment and target_file_path.is_file():
            if target_file_path.suffix.lower() != ".md":
                return None

            try:
                target_content = target_file_path.read_text(encoding="utf-8")
            except OSError as exc:
                return ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="linked-file-read-error",
                    message=f"Unable to read the linked Markdown file: {exc}",
                    repository_path=source_repository_path,
                    line_number=line_number,
                )

            if fragment.casefold() not in self._extract_heading_fragments(
                target_content
            ):
                return ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.WARNING,
                    code="missing-link-fragment",
                    message=(
                        f'The linked heading fragment does not exist: '
                        f'"{normalized_target}".'
                    ),
                    repository_path=source_repository_path,
                    line_number=line_number,
                )

        return None

    @staticmethod
    def _extract_link_targets(line: str) -> tuple[str, ...]:
        """Extract inline Markdown link and image targets from one line."""

        targets: list[str] = []

        for match in re.finditer(
            r"!?\[[^\]]*\]\(([^)]+)\)",
            line,
        ):
            target = match.group(1).strip()

            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1].strip()

            if " " in target and not target.startswith("#"):
                target = target.split(" ", maxsplit=1)[0]

            targets.append(target)

        return tuple(targets)

    @staticmethod
    def _extract_heading_fragments(content: str) -> set[str]:
        """Return normalized heading fragments from Markdown content."""

        fragments: set[str] = set()
        fragment_counts: dict[str, int] = {}
        inside_fenced_block = False

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("```") or stripped.startswith("~~~"):
                inside_fenced_block = not inside_fenced_block
                continue

            if inside_fenced_block:
                continue

            match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
            if match is None:
                continue

            title = match.group(1).strip()
            base_fragment = LinkValidator._slugify_heading(title)
            count = fragment_counts.get(base_fragment, 0)

            if count == 0:
                fragment = base_fragment
            else:
                fragment = f"{base_fragment}-{count}"

            fragment_counts[base_fragment] = count + 1
            fragments.add(fragment.casefold())

        return fragments

    @staticmethod
    def _slugify_heading(title: str) -> str:
        """Convert a Markdown heading to a GitHub-style fragment."""

        normalized = title.strip().casefold()
        normalized = re.sub(r"[^\w\- ]", "", normalized)
        normalized = re.sub(r"\s+", "-", normalized)
        normalized = re.sub(r"-+", "-", normalized)

        return normalized.strip("-")

    @staticmethod
    def _is_external_target(link_target: str) -> bool:
        """Return whether a target should not be validated locally."""

        parsed_target = urlparse(link_target)

        return parsed_target.scheme in {
            "http",
            "https",
            "mailto",
            "tel",
            "ftp",
        }

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
