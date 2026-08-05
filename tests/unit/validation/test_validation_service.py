# ============================================================
# Project0 - Validation Service Tests
#
# File: test_validation_service.py
#
# Purpose:
#     Verify validator orchestration and combined validation
#     results produced by the Project0 Validation Service.
#
# ============================================================

from datetime import UTC, datetime

from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)
from project0.validation.validation_service import ValidationService


class StubValidator:
    """Return a configured validator result."""

    def __init__(
        self,
        validator_name: str,
        result: ValidatorResult,
    ) -> None:
        self.validator_name = validator_name
        self._result = result
        self.received_requests: list[ValidationRequest] = []

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Record the request and return the configured result."""

        self.received_requests.append(request)
        return self._result


class FailingValidator:
    """Raise a configured exception during validation."""

    validator_name = "failing"

    def __init__(self, error: Exception) -> None:
        self._error = error
        self.received_requests: list[ValidationRequest] = []

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Record the request and raise the configured exception."""

        self.received_requests.append(request)
        raise self._error


def _validator_result(
    validator_name: str,
    status: ValidationStatus,
    *,
    issues: tuple[ValidationIssue, ...] = (),
    error_message: str | None = None,
) -> ValidatorResult:
    """Create a deterministic validator result for tests."""

    started_at = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    completed_at = datetime(2026, 8, 5, 10, 1, tzinfo=UTC)

    return ValidatorResult(
        validator_name=validator_name,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        issues=issues,
        error_message=error_message,
    )


def test_all_passing_validators_produce_passed_result() -> None:
    """All passing validators produce a passed combined result."""

    first = StubValidator(
        "markdown",
        _validator_result("markdown", ValidationStatus.PASSED),
    )
    second = StubValidator(
        "link",
        _validator_result("link", ValidationStatus.PASSED),
    )
    request = ValidationRequest(
        target_paths=("docs/index.md",),
        validation_id="validation-001",
    )

    service = ValidationService(validators=(first, second))

    result = service.validate(request)

    assert result.validation_id == "validation-001"
    assert result.status is ValidationStatus.PASSED
    assert result.validator_results == (
        first._result,
        second._result,
    )
    assert result.issues == ()
    assert result.error_message is None


def test_warning_result_produces_passed_with_warnings() -> None:
    """Any warning validator produces warning combined status."""

    issue = ValidationIssue(
        validator_name="markdown",
        severity=ValidationSeverity.WARNING,
        code="duplicate-heading",
        message="Duplicate heading.",
        repository_path="docs/index.md",
    )

    passing = StubValidator(
        "link",
        _validator_result("link", ValidationStatus.PASSED),
    )
    warning = StubValidator(
        "markdown",
        _validator_result(
            "markdown",
            ValidationStatus.PASSED_WITH_WARNINGS,
            issues=(issue,),
        ),
    )

    service = ValidationService(validators=(passing, warning))

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.PASSED_WITH_WARNINGS
    assert result.issues == (issue,)


def test_failed_result_takes_precedence_over_warning() -> None:
    """A failed validator takes precedence over warning results."""

    warning_issue = ValidationIssue(
        validator_name="markdown",
        severity=ValidationSeverity.WARNING,
        code="duplicate-heading",
        message="Duplicate heading.",
    )
    error_issue = ValidationIssue(
        validator_name="link",
        severity=ValidationSeverity.ERROR,
        code="missing-link-target",
        message="Missing target.",
    )

    warning = StubValidator(
        "markdown",
        _validator_result(
            "markdown",
            ValidationStatus.PASSED_WITH_WARNINGS,
            issues=(warning_issue,),
        ),
    )
    failed = StubValidator(
        "link",
        _validator_result(
            "link",
            ValidationStatus.FAILED,
            issues=(error_issue,),
        ),
    )

    service = ValidationService(validators=(warning, failed))

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert result.issues == (
        warning_issue,
        error_issue,
    )


def test_validator_results_preserve_configured_order() -> None:
    """Validator results retain configured validator ordering."""

    first = StubValidator(
        "first",
        _validator_result("first", ValidationStatus.PASSED),
    )
    second = StubValidator(
        "second",
        _validator_result("second", ValidationStatus.PASSED),
    )
    third = StubValidator(
        "third",
        _validator_result("third", ValidationStatus.PASSED),
    )

    service = ValidationService(
        validators=(first, second, third)
    )

    result = service.validate(
        ValidationRequest(target_paths=())
    )

    assert tuple(
        validator_result.validator_name
        for validator_result in result.validator_results
    ) == (
        "first",
        "second",
        "third",
    )


def test_request_is_forwarded_to_each_validator() -> None:
    """The original validation request is passed to each validator."""

    first = StubValidator(
        "first",
        _validator_result("first", ValidationStatus.PASSED),
    )
    second = StubValidator(
        "second",
        _validator_result("second", ValidationStatus.PASSED),
    )
    request = ValidationRequest(
        target_paths=("docs/index.md",),
        validation_id="validation-001",
    )

    service = ValidationService(validators=(first, second))

    service.validate(request)

    assert first.received_requests == [request]
    assert second.received_requests == [request]


def test_validator_exception_is_converted_to_failed_result() -> None:
    """An unexpected validator exception becomes a failed result."""

    failing = FailingValidator(RuntimeError("unexpected failure"))
    service = ValidationService(validators=(failing,))

    result = service.validate(
        ValidationRequest(target_paths=("docs/index.md",))
    )

    assert result.status is ValidationStatus.FAILED
    assert len(result.validator_results) == 1

    validator_result = result.validator_results[0]

    assert validator_result.validator_name == "failing"
    assert validator_result.status is ValidationStatus.FAILED
    assert validator_result.error_message == "unexpected failure"
    assert len(validator_result.issues) == 1
    assert validator_result.issues[0].code == (
        "validator-execution-error"
    )
    assert validator_result.issues[0].severity is (
        ValidationSeverity.ERROR
    )


def test_validation_continues_after_validator_exception() -> None:
    """A validator exception does not prevent later validators."""

    failing = FailingValidator(RuntimeError("failure"))
    passing = StubValidator(
        "passing",
        _validator_result("passing", ValidationStatus.PASSED),
    )

    service = ValidationService(validators=(failing, passing))
    request = ValidationRequest(target_paths=())

    result = service.validate(request)

    assert len(result.validator_results) == 2
    assert result.validator_results[0].status is ValidationStatus.FAILED
    assert result.validator_results[1].status is ValidationStatus.PASSED
    assert passing.received_requests == [request]


def test_exception_without_message_uses_exception_class_name() -> None:
    """An empty exception message falls back to its class name."""

    failing = FailingValidator(RuntimeError())
    service = ValidationService(validators=(failing,))

    result = service.validate(
        ValidationRequest(target_paths=())
    )

    validator_result = result.validator_results[0]

    assert validator_result.error_message == "RuntimeError"
    assert "RuntimeError" in validator_result.issues[0].message


def test_validator_class_name_is_used_when_name_is_missing() -> None:
    """A validator without validator_name uses its class name."""

    class UnnamedFailingValidator:
        def validate(
            self,
            request: ValidationRequest,
        ) -> ValidatorResult:
            del request
            raise ValueError("bad value")

    service = ValidationService(
        validators=(UnnamedFailingValidator(),)
    )

    result = service.validate(
        ValidationRequest(target_paths=())
    )

    assert result.validator_results[0].validator_name == (
        "UnnamedFailingValidator"
    )
    assert result.issues[0].validator_name == (
        "UnnamedFailingValidator"
    )


def test_validator_error_messages_are_combined() -> None:
    """Validator execution error messages are combined in order."""

    first = StubValidator(
        "first",
        _validator_result(
            "first",
            ValidationStatus.FAILED,
            error_message="first error",
        ),
    )
    second = StubValidator(
        "second",
        _validator_result(
            "second",
            ValidationStatus.FAILED,
            error_message="second error",
        ),
    )

    service = ValidationService(validators=(first, second))

    result = service.validate(
        ValidationRequest(target_paths=())
    )

    assert result.error_message == (
        "first: first error; second: second error"
    )


def test_issue_only_failure_does_not_create_error_message() -> None:
    """Validation issues alone do not create an execution error message."""

    issue = ValidationIssue(
        validator_name="link",
        severity=ValidationSeverity.ERROR,
        code="missing-link-target",
        message="Missing target.",
    )
    validator = StubValidator(
        "link",
        _validator_result(
            "link",
            ValidationStatus.FAILED,
            issues=(issue,),
        ),
    )

    service = ValidationService(validators=(validator,))

    result = service.validate(
        ValidationRequest(target_paths=())
    )

    assert result.status is ValidationStatus.FAILED
    assert result.error_message is None


def test_empty_validator_collection_passes() -> None:
    """An empty validator collection produces an empty passed result."""

    request = ValidationRequest(
        target_paths=(),
        validation_id="validation-empty",
    )
    service = ValidationService(validators=())

    result = service.validate(request)

    assert result.validation_id == "validation-empty"
    assert result.status is ValidationStatus.PASSED
    assert result.validator_results == ()
    assert result.issues == ()
    assert result.error_message is None


def test_combined_timestamps_are_timezone_aware() -> None:
    """Combined validation timestamps are timezone-aware."""

    validator = StubValidator(
        "markdown",
        _validator_result("markdown", ValidationStatus.PASSED),
    )
    service = ValidationService(validators=(validator,))

    result = service.validate(
        ValidationRequest(target_paths=())
    )

    assert result.started_at.tzinfo is not None
    assert result.completed_at.tzinfo is not None
    assert result.completed_at >= result.started_at
