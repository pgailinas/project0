# ============================================================
# Project0 - Validation Service
#
# File: validation_service.py
#
# Purpose:
#     Coordinate Project0 validators and return a combined
#     validation result.
#
# ============================================================

from __future__ import annotations

from datetime import UTC, datetime

from project0.interfaces.validation_interfaces import ValidatorInterface
from project0.models.validation_models import (
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
    ValidatorResult,
)


class ValidationService:
    """Coordinate validators and aggregate their results."""

    def __init__(
        self,
        validators: tuple[ValidatorInterface, ...],
    ) -> None:
        self._validators = validators

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidationResult:
        """Execute configured validators and return a combined result."""

        started_at = datetime.now(UTC)
        validator_results: list[ValidatorResult] = []

        for validator in self._validators:
            try:
                validator_result = validator.validate(request)
            except Exception as exc:
                validator_result = self._build_exception_result(
                    validator=validator,
                    error=exc,
                )

            validator_results.append(validator_result)

        issues = tuple(
            issue
            for validator_result in validator_results
            for issue in validator_result.issues
        )

        completed_at = datetime.now(UTC)

        return ValidationResult(
            validation_id=request.validation_id,
            status=self._determine_status(validator_results),
            started_at=started_at,
            completed_at=completed_at,
            validator_results=tuple(validator_results),
            issues=issues,
            error_message=self._build_error_message(validator_results),
        )

    @staticmethod
    def _build_exception_result(
        validator: ValidatorInterface,
        error: Exception,
    ) -> ValidatorResult:
        """Convert an unexpected validator exception into a result."""

        occurred_at = datetime.now(UTC)
        validator_name = getattr(
            validator,
            "validator_name",
            validator.__class__.__name__,
        )
        error_message = str(error) or error.__class__.__name__

        return ValidatorResult(
            validator_name=validator_name,
            status=ValidationStatus.FAILED,
            started_at=occurred_at,
            completed_at=occurred_at,
            issues=(
                ValidationIssue(
                    validator_name=validator_name,
                    severity=ValidationSeverity.ERROR,
                    code="validator-execution-error",
                    message=(
                        "The validator failed with an unexpected exception: "
                        f"{error_message}"
                    ),
                ),
            ),
            error_message=error_message,
        )

    @staticmethod
    def _determine_status(
        validator_results: list[ValidatorResult],
    ) -> ValidationStatus:
        """Determine the combined validation status."""

        if any(
            result.status is ValidationStatus.FAILED
            for result in validator_results
        ):
            return ValidationStatus.FAILED

        if any(
            result.status is ValidationStatus.PASSED_WITH_WARNINGS
            for result in validator_results
        ):
            return ValidationStatus.PASSED_WITH_WARNINGS

        return ValidationStatus.PASSED

    @staticmethod
    def _build_error_message(
        validator_results: list[ValidatorResult],
    ) -> str | None:
        """Combine validator execution error messages."""

        error_messages = tuple(
            (
                f"{result.validator_name}: "
                f"{result.error_message}"
            )
            for result in validator_results
            if result.error_message
        )

        if not error_messages:
            return None

        return "; ".join(error_messages)
