# ============================================================
# Project0 - Documentation Agent
#
# File: settings.py
#
# Purpose:
#     Define shared application configuration values used
#     throughout the Documentation Agent.
#
# ============================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    Shared application configuration.

    These values represent the default runtime configuration for
    the Documentation Agent. Future releases may override these
    values from a TOML configuration file or command-line options.
    """

    project_name: str = "Project0"
    application_name: str = "Documentation Agent"

    log_level: str = "INFO"

    documentation_extension: str = ".md"

    encoding: str = "utf-8"


#
# Shared application settings
#
SETTINGS = Settings()

