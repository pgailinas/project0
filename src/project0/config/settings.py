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
from pathlib import Path


@dataclass(frozen=True)
class ProjectSettings:
    """Shared runtime configuration for Project0."""

    project_root: Path
    docs_dir: Path
    source_dir: Path
    tests_dir: Path
    log_level: str = "INFO"


def load_settings() -> ProjectSettings:
    """Create the shared Project0 configuration."""

    project_root = Path(__file__).resolve().parents[3]

    return ProjectSettings(
        project_root=project_root,
        docs_dir=project_root / "docs",
        source_dir=project_root / "src",
        tests_dir=project_root / "tests",
        log_level="INFO",
    )

SETTINGS = load_settings()


