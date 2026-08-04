# ============================================================
# Project0 - Common Services
#
# File: test_startup_validation.py
#
# Purpose:
#     Verify Project0 startup validation for required
#     directories, files, and error handling.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

import pytest

from project0.common.startup_validation import (
    StartupValidationError,
    _validate_directory,
    _validate_file,
    validate_startup,
)
from project0.config.settings import ProjectSettings


@pytest.fixture
def valid_settings(tmp_path: Path) -> ProjectSettings:
    (tmp_path/"docs").mkdir()
    src=tmp_path/"src"; src.mkdir()
    (tmp_path/"tests").mkdir()
    common=src/"project0"/"common"; common.mkdir(parents=True)
    config=src/"project0"/"config"; config.mkdir(parents=True)
    for f in ["pyproject.toml","mkdocs.yml","README.md"]:
        (tmp_path/f).write_text("",encoding="utf-8")
    (common/"__init__.py").write_text("",encoding="utf-8")
    (config/"__init__.py").write_text("",encoding="utf-8")
    return ProjectSettings(tmp_path,tmp_path/"docs",src,tmp_path/"tests")


def test_validate_directory_accepts_directory(tmp_path: Path):
    d=tmp_path/"docs"; d.mkdir()
    _validate_directory(d,"docs")


def test_validate_directory_missing(tmp_path: Path):
    with pytest.raises(StartupValidationError,match="does not exist"):
        _validate_directory(tmp_path/"missing","docs")


def test_validate_directory_not_directory(tmp_path: Path):
    f=tmp_path/"x"; f.write_text("")
    with pytest.raises(StartupValidationError,match="directory"):
        _validate_directory(f,"docs")


def test_validate_file_accepts_file(tmp_path: Path):
    f=tmp_path/"a.txt"; f.write_text("")
    _validate_file(f,"file")


def test_validate_file_missing(tmp_path: Path):
    with pytest.raises(StartupValidationError,match="does not exist"):
        _validate_file(tmp_path/"x","file")


def test_validate_file_not_file(tmp_path: Path):
    d=tmp_path/"d"; d.mkdir()
    with pytest.raises(StartupValidationError,match="file"):
        _validate_file(d,"file")


def test_validate_startup_valid(valid_settings: ProjectSettings):
    validate_startup(valid_settings)


def test_validate_startup_missing_docs(valid_settings: ProjectSettings):
    valid_settings.docs_dir.rmdir()
    with pytest.raises(StartupValidationError):
        validate_startup(valid_settings)
