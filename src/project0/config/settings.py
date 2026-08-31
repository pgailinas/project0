# ============================================================
# Project0 - Project0 Settings
#
# File: settings.py
#
# Purpose:
#     Define shared application configuration values used
#     throughout Project0.
#
# ============================================================

import os
from dataclasses import dataclass
from pathlib import Path

from project0.config.constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_OLLAMA_TIMEOUT_SECONDS,
    DEFAULT_RESEARCH_DIRECTION_ANALYSIS_ENABLED,
    DEFAULT_RESEARCH_SOURCE_PROVIDERS,
)


@dataclass(frozen=True)
class ProjectSettings:
    """Shared runtime configuration for Project0."""

    project_root: Path
    docs_dir: Path
    source_dir: Path
    tests_dir: Path
    log_level: str = DEFAULT_LOG_LEVEL
    reasoning_provider: str = "ollama"
    research_source_providers: tuple[str, ...] = DEFAULT_RESEARCH_SOURCE_PROVIDERS
    research_direction_analysis_enabled: bool = DEFAULT_RESEARCH_DIRECTION_ANALYSIS_ENABLED
    semantic_scholar_api_key: str | None = None
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS



def _parse_provider_list(value: str) -> tuple[str, ...]:
    """Parse comma-separated provider configuration values."""

    return tuple(
        provider.strip()
        for provider in value.split(",")
        if provider.strip()
    )

def _parse_boolean(value: str) -> bool:
    """Parse boolean configuration values."""

    return value.strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }

def load_settings() -> ProjectSettings:
    """Create the shared Project0 configuration."""

    project_root = Path(__file__).resolve().parents[3]

    return ProjectSettings(
        project_root=project_root,
        docs_dir=project_root / "docs",
        source_dir=project_root / "src",
        tests_dir=project_root / "tests",
        log_level=os.getenv(
            "PROJECT0_LOG_LEVEL",
            DEFAULT_LOG_LEVEL,
        ),
        reasoning_provider=os.getenv(
            "PROJECT0_REASONING_PROVIDER",
            "ollama",
        ),
        research_source_providers=_parse_provider_list(
            os.getenv(
                "PROJECT0_RESEARCH_SOURCE_PROVIDERS",
                ",".join(DEFAULT_RESEARCH_SOURCE_PROVIDERS),
            )
        ),
        research_direction_analysis_enabled=_parse_boolean(
            os.getenv(
                "PROJECT0_ENABLE_RESEARCH_DIRECTION_ANALYSIS",
                str(DEFAULT_RESEARCH_DIRECTION_ANALYSIS_ENABLED),
            )
        ),
        semantic_scholar_api_key=os.getenv(
            "PROJECT0_SEMANTIC_SCHOLAR_API_KEY",
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
                str(DEFAULT_OLLAMA_TIMEOUT_SECONDS),
            )
        ),
    )

SETTINGS = load_settings()


