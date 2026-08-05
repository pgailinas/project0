# ============================================================
# Project0 - Validation Models
#
# File: validation_models.py
#
# Purpose:
#     Define shared validation request, issue, and result models
#     used by Project0 validation components and AI agents.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4


class ValidationStatus(StrEnum):
    """Supported validation execution states."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class ValidationSeverity(StrEnum):
    """Supported validation issue severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    """Request to validate repository documentation."""

    target_paths: tuple[str, ...]
    validation_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single issue identified during validation."""

    validator_name: str
    severity: ValidationSeverity
    code: str
    message: str
    repository_path: str | None = None
    line_number: int | None = None


@dataclass(frozen=True, slots=True)
class ValidatorResult:
    """Result produced by one validator."""

    validator_name: str
    status: ValidationStatus
    started_at: datetime
    completed_at: datetime
    issues: tuple[ValidationIssue, ...] = ()
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Combined result of a complete validation request."""

    validation_id: str
    status: ValidationStatus
    started_at: datetime
    completed_at: datetime
    validator_results: tuple[ValidatorResult, ...]
    issues: tuple[ValidationIssue, ...] = ()
    error_message: str | None = None


