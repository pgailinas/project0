# ============================================================
# Project0 - Validation Models Tests
#
# File: test_validation_models.py
#
# Purpose:
#     Verify shared validation request, issue, and result
#     data models used by Project0 validation components.
#
# ============================================================

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest

from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)


def test_validation_status_values() -> None:
    assert ValidationStatus.PENDING == "pending"
    assert ValidationStatus.RUNNING == "running"
    assert ValidationStatus.PASSED == "passed"
    assert ValidationStatus.PASSED_WITH_WARNINGS == "passed_with_warnings"
    assert ValidationStatus.FAILED == "failed"


def test_validation_severity_values() -> None:
    assert ValidationSeverity.INFO == "info"
    assert ValidationSeverity.WARNING == "warning"
    assert ValidationSeverity.ERROR == "error"


def test_validation_request_stores_target_paths() -> None:
    request = ValidationRequest(
        target_paths=(
            "docs/Documentation_Agent_Architecture.md",
            "docs/Documentation_Agent_Design.md",
        )
    )
    assert len(request.target_paths) == 2


def test_validation_request_generates_unique_identifier() -> None:
    first = ValidationRequest(target_paths=("docs/index.md",))
    second = ValidationRequest(target_paths=("docs/index.md",))
    UUID(first.validation_id)
    UUID(second.validation_id)
    assert first.validation_id != second.validation_id


def test_validation_issue_defaults() -> None:
    issue = ValidationIssue(
        validator_name="markdown",
        severity=ValidationSeverity.ERROR,
        code="missing-title",
        message="Missing H1.",
    )
    assert issue.repository_path is None
    assert issue.line_number is None


def test_validator_result_defaults() -> None:
    start = datetime(2026,8,5,9,0,tzinfo=UTC)
    end = datetime(2026,8,5,9,1,tzinfo=UTC)
    result = ValidatorResult(
        validator_name="markdown",
        status=ValidationStatus.PASSED,
        started_at=start,
        completed_at=end,
    )
    assert result.issues == ()
    assert result.error_message is None


def test_validation_result_defaults() -> None:
    start = datetime(2026,8,5,9,0,tzinfo=UTC)
    end = datetime(2026,8,5,9,2,tzinfo=UTC)
    result = ValidationResult(
        validation_id="validation-001",
        status=ValidationStatus.PASSED,
        started_at=start,
        completed_at=end,
        validator_results=(),
    )
    assert result.issues == ()
    assert result.validator_results == ()


@pytest.mark.parametrize(
    ("model","attribute","value"),
    [
        (ValidationRequest(target_paths=("docs/index.md",)), "target_paths", ()),
        (
            ValidationIssue(
                validator_name="markdown",
                severity=ValidationSeverity.INFO,
                code="test",
                message="Test",
            ),
            "message",
            "Changed",
        ),
    ],
)
def test_models_are_immutable(model: object, attribute: str, value: object) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(model, attribute, value)
