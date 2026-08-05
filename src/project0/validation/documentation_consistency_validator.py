# ============================================================
# Project0 - Documentation Consistency Validator
#
# File: documentation_consistency_validator.py
#
# Purpose:
#     Validate deterministic consistency rules across Project0
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


DEFAULT_REQUIRED_DOCUMENTS = (
    "docs/Project_Charter.md",
    "docs/Documentation_Standards.md",
    "docs/Documentation_Agent_Functional_Spec.md",
    "docs/Documentation_Agent_Architecture.md",
    "docs/Documentation_Agent_Design.md",
    "docs/Component_Communication_Design.md",
    "docs/Shared_Data_Models_and_Error_Contracts.md",
    "docs/Implementation_Roadmap.md",
    "docs/Implementation_Status.md",
    "docs/Project_Directory_Structure.md",
)


class DocumentationConsistencyValidator:
    """Validate deterministic consistency across Project0 documents."""

    validator_name = "documentation_consistency"

    def __init__(
        self,
        repository_root: Path,
        required_document_paths: tuple[str, ...] = DEFAULT_REQUIRED_DOCUMENTS,
    ) -> None:
        self._repository_root = repository_root.resolve()
        self._required_document_paths = required_document_paths

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Validate documentation consistency and return a structured result."""

        del request

        started_at = datetime.now(UTC)
        issues: list[ValidationIssue] = []

        issues.extend(self._validate_required_documents())
        issues.extend(self._validate_roadmap_status_consistency())

        completed_at = datetime.now(UTC)

        return ValidatorResult(
            validator_name=self.validator_name,
            status=self._determine_status(issues),
            started_at=started_at,
            completed_at=completed_at,
            issues=tuple(issues),
        )

    def _validate_required_documents(self) -> list[ValidationIssue]:
        """Verify that required Project0 documentation files exist."""

        issues: list[ValidationIssue] = []

        for repository_path in self._required_document_paths:
            file_path = (self._repository_root / repository_path).resolve()

            if not self._is_within_repository(file_path):
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="required-document-outside-repository",
                        message=(
                            "A configured required document resolves outside "
                            "the repository root."
                        ),
                        repository_path=repository_path,
                    )
                )
                continue

            if not file_path.is_file():
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="required-document-missing",
                        message="A required project document does not exist.",
                        repository_path=repository_path,
                    )
                )

        return issues

    def _validate_roadmap_status_consistency(
        self,
    ) -> list[ValidationIssue]:
        """Verify that status phase references exist in the roadmap."""

        issues: list[ValidationIssue] = []

        roadmap_path = self._repository_root / "docs/Implementation_Roadmap.md"
        status_path = self._repository_root / "docs/Implementation_Status.md"

        if not roadmap_path.is_file() or not status_path.is_file():
            return issues

        try:
            roadmap_content = roadmap_path.read_text(encoding="utf-8")
            status_content = status_path.read_text(encoding="utf-8")
        except OSError as exc:
            return [
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="documentation-read-error",
                    message=f"Unable to read implementation documents: {exc}",
                )
            ]

        roadmap_phases = self._extract_roadmap_phases(roadmap_content)
        status_phases = self._extract_status_phases(status_content)

        if not roadmap_phases:
            issues.append(
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="roadmap-phases-not-found",
                    message=(
                        "No implementation phase headings were found in "
                        "Implementation_Roadmap.md."
                    ),
                    repository_path="docs/Implementation_Roadmap.md",
                )
            )
            return issues

        if not status_phases:
            issues.append(
                ValidationIssue(
                    validator_name=self.validator_name,
                    severity=ValidationSeverity.WARNING,
                    code="status-phases-not-found",
                    message=(
                        "No implementation phase references were found in "
                        "Implementation_Status.md."
                    ),
                    repository_path="docs/Implementation_Status.md",
                )
            )
            return issues

        for phase_number, phase_name, line_number in status_phases:
            roadmap_name = roadmap_phases.get(phase_number)

            if roadmap_name is None:
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.ERROR,
                        code="status-phase-not-in-roadmap",
                        message=(
                            f"Phase {phase_number} is referenced by the "
                            "implementation status but is not defined in "
                            "the roadmap."
                        ),
                        repository_path="docs/Implementation_Status.md",
                        line_number=line_number,
                    )
                )
                continue

            if self._normalize_phase_name(phase_name) != (
                self._normalize_phase_name(roadmap_name)
            ):
                issues.append(
                    ValidationIssue(
                        validator_name=self.validator_name,
                        severity=ValidationSeverity.WARNING,
                        code="phase-name-mismatch",
                        message=(
                            f'Phase {phase_number} is named "{phase_name}" '
                            f'in the status document and "{roadmap_name}" '
                            "in the roadmap."
                        ),
                        repository_path="docs/Implementation_Status.md",
                        line_number=line_number,
                    )
                )

        return issues

    @staticmethod
    def _extract_roadmap_phases(
        content: str,
    ) -> dict[int, str]:
        """Extract numbered implementation phases from roadmap headings."""

        phases: dict[int, str] = {}

        for line in content.splitlines():
            match = re.match(
                r"^##\s+Phase\s+(\d+)\s*[—–-]\s*(.+?)\s*$",
                line,
            )

            if match is None:
                continue

            phase_number = int(match.group(1))
            phase_name = match.group(2).strip()
            phases[phase_number] = phase_name

        return phases

    @staticmethod
    def _extract_status_phases(
        content: str,
    ) -> tuple[tuple[int, str, int], ...]:
        """Extract numbered phase references from the status document."""

        phases: list[tuple[int, str, int]] = []
        seen: set[tuple[int, str]] = set()

        for line_number, line in enumerate(content.splitlines(), start=1):
            match = re.search(
                r"Phase\s+(\d+)\s*[—–-]\s*"
                r"(.+?)(?:\s*\([^)]*\)|\s*:\s*.+|$)",
                line,
            )

            if match is None:
                continue

            phase_number = int(match.group(1))
            phase_name = match.group(2).strip()
            phase_key = (
                phase_number,
                DocumentationConsistencyValidator._normalize_phase_name(
                    phase_name
                ),
            )

            if phase_key in seen:
                continue

            seen.add(phase_key)
            phases.append((phase_number, phase_name, line_number))

        return tuple(phases)

    @staticmethod
    def _normalize_phase_name(phase_name: str) -> str:
        """Normalize a phase name for deterministic comparison."""

        normalized = phase_name.casefold().strip()
        normalized = re.sub(r"^[✅☑✔\-\*\s]+", "", normalized)
        normalized = re.sub(
            r"\s*(completed|in progress|ready to begin)\s*$",
            "",
            normalized,
        )
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip(" :-")

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
