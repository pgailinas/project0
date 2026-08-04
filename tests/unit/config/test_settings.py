# ============================================================
# Project0 - Configuration
#
# File: test_settings.py
#
# Purpose:
#     Verify Project0 settings creation, path derivation,
#     default values, and immutable configuration behavior.
#
# ============================================================

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from project0.config.settings import (
    SETTINGS,
    ProjectSettings,
    load_settings,
)


def test_project_settings_stores_supplied_values(
    tmp_path: Path,
) -> None:
    settings = ProjectSettings(
        project_root=tmp_path,
        docs_dir=tmp_path / "docs",
        source_dir=tmp_path / "src",
        tests_dir=tmp_path / "tests",
        log_level="DEBUG",
    )

    assert settings.project_root == tmp_path
    assert settings.docs_dir == tmp_path / "docs"
    assert settings.source_dir == tmp_path / "src"
    assert settings.tests_dir == tmp_path / "tests"
    assert settings.log_level == "DEBUG"


def test_project_settings_uses_default_log_level(
    tmp_path: Path,
) -> None:
    settings = ProjectSettings(
        project_root=tmp_path,
        docs_dir=tmp_path / "docs",
        source_dir=tmp_path / "src",
        tests_dir=tmp_path / "tests",
    )

    assert settings.log_level == "INFO"


def test_project_settings_is_immutable(
    tmp_path: Path,
) -> None:
    settings = ProjectSettings(
        project_root=tmp_path,
        docs_dir=tmp_path / "docs",
        source_dir=tmp_path / "src",
        tests_dir=tmp_path / "tests",
    )

    with pytest.raises(FrozenInstanceError):
        settings.log_level = "DEBUG"  # type: ignore[misc]


def test_load_settings_returns_project_settings() -> None:
    settings = load_settings()

    assert isinstance(settings, ProjectSettings)


def test_load_settings_derives_expected_project_paths() -> None:
    settings = load_settings()

    assert settings.project_root.is_absolute()
    assert settings.docs_dir == settings.project_root / "docs"
    assert settings.source_dir == settings.project_root / "src"
    assert settings.tests_dir == settings.project_root / "tests"


def test_load_settings_uses_info_log_level() -> None:
    settings = load_settings()

    assert settings.log_level == "INFO"


def test_load_settings_returns_consistent_values() -> None:
    first = load_settings()
    second = load_settings()

    assert first == second
    assert first is not second


def test_module_settings_matches_loaded_settings() -> None:
    assert SETTINGS == load_settings()


def test_module_settings_paths_exist_in_project_repository() -> None:
    assert SETTINGS.project_root.is_dir()
    assert SETTINGS.docs_dir.is_dir()
    assert SETTINGS.source_dir.is_dir()
    assert SETTINGS.tests_dir.is_dir()
