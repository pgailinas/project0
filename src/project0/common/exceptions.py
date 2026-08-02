# ============================================================
# Project0 - Documentation Agent
#
# File: exceptions.py
#
# Purpose:
#     Define shared application exception types.
#
# ============================================================


class Project0Error(Exception):
    """Base exception for Project0 application errors."""


class ConfigurationError(Project0Error):
    """Raised when application configuration is invalid."""


class RepositoryError(Project0Error):
    """Raised when repository access or processing fails."""


class ValidationError(Project0Error):
    """Raised when documentation validation fails."""
    
