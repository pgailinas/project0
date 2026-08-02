# ============================================================
# Project0 - Documentation Agent
#
# File: logging_config.py
#
# Purpose:
#     Configure startup and environment validation for the
#     Documentation Agent.
#
# ============================================================

import logging
from pathlib import Path

from project0.config.settings import ProjectSettings

LOGGER = logging.getLogger(__name__)


class StartupValidationError(RuntimeError):
    """Raised when Project0 startup validation fails."""


def _validate_directory(path: Path, description: str) -> None:
    """Verify that a required directory exists."""

    if not path.exists():
        raise StartupValidationError(
            f"Required {description} does not exist: {path}"
        )

    if not path.is_dir():
        raise StartupValidationError(
            f"Expected {description} to be a directory: {path}"
        )

    LOGGER.info("Validated %s: %s", description, path)


def _validate_file(path: Path, description: str) -> None:
    """Verify that a required file exists."""

    if not path.exists():
        raise StartupValidationError(
            f"Required {description} does not exist: {path}"
        )

    if not path.is_file():
        raise StartupValidationError(
            f"Expected {description} to be a file: {path}"
        )

    LOGGER.info("Validated %s: %s", description, path)


def validate_startup(settings: ProjectSettings) -> None:
    """Validate the Project0 repository and shared configuration."""

    LOGGER.info("Starting Project0 startup validation.")

    _validate_directory(settings.project_root, "project root")
    _validate_directory(settings.docs_dir, "documentation directory")
    _validate_directory(settings.source_dir, "source directory")
    _validate_directory(settings.tests_dir, "test directory")

    _validate_directory(
        settings.source_dir / "project0" / "common",
        "common package",
    )
    _validate_directory(
        settings.source_dir / "project0" / "config",
        "configuration package",
    )

    _validate_file(
        settings.project_root / "pyproject.toml",
        "Python project configuration",
    )
    _validate_file(
        settings.project_root / "mkdocs.yml",
        "MkDocs configuration",
    )
    _validate_file(
        settings.project_root / "README.md",
        "repository README",
    )

    _validate_file(
        settings.source_dir / "project0" / "common" / "__init__.py",
        "common package initializer",
    )
    _validate_file(
        settings.source_dir / "project0" / "config" / "__init__.py",
        "configuration package initializer",
    )

    LOGGER.info("Project0 startup validation completed successfully.")
    
    
