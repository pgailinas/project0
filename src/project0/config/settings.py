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

import os
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
    reasoning_provider: str = "ollama"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_timeout_seconds: float = 300.0


def load_settings() -> ProjectSettings:
    """Create the shared Project0 configuration."""

    project_root = Path(__file__).resolve().parents[3]

    return ProjectSettings(
        project_root=project_root,
        docs_dir=project_root / "docs",
        source_dir=project_root / "src",
        tests_dir=project_root / "tests",
        log_level="INFO",
        reasoning_provider=os.getenv(
            "PROJECT0_REASONING_PROVIDER",
            "ollama",
        ),
        ollama_model=os.getenv(
            "PROJECT0_OLLAMA_MODEL",
            "qwen2.5:7b",
        ),
        ollama_base_url=os.getenv(
            "PROJECT0_OLLAMA_BASE_URL",
            "http://127.0.0.1:11434",
        ),
        ollama_timeout_seconds=float(
            os.getenv(
                "PROJECT0_OLLAMA_TIMEOUT_SECONDS",
                "300.0",
            )
        ),
    )

SETTINGS = load_settings()


