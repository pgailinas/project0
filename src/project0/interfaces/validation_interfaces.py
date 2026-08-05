# ============================================================
# Project0 - Validation Interfaces
#
# File: validation_interfaces.py
#
# Purpose:
#     Define public interfaces for validation services and
#     individual validators used by Project0.
#
# ============================================================

from __future__ import annotations

from typing import Protocol

from project0.models.validation_models import (
    ValidationRequest,
    ValidationResult,
    ValidatorResult,
)


class ValidatorInterface(Protocol):
    """Public contract for individual Project0 validators."""

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidatorResult:
        """Validate a request and return a validator result."""


class ValidationInterface(Protocol):
    """Public contract for Project0 validation services."""

    def validate(
        self,
        request: ValidationRequest,
    ) -> ValidationResult:
        """Execute validation and return the combined result."""
