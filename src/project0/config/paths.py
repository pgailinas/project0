# ============================================================
# Project0 - Documentation Agent
#
# File: paths.py
#
# Purpose:
#     Define the standard repository directory locations used
#     throughout the Documentation Agent.
#
# ============================================================

from pathlib import Path


#
# Repository root
#
PROJECT_ROOT = Path(__file__).resolve().parents[3]


#
# Standard repository directories
#
DOCS_DIR = PROJECT_ROOT / "docs"

SRC_DIR = PROJECT_ROOT / "src"

TESTS_DIR = PROJECT_ROOT / "tests"

SCRIPTS_DIR = PROJECT_ROOT / "scripts"

LOGS_DIR = PROJECT_ROOT / "logs"

CONFIG_DIR = PROJECT_ROOT / "config"


#
# MkDocs configuration
#
MKDOCS_CONFIG_FILE = PROJECT_ROOT / "mkdocs.yml"


#
# Repository documentation
#
README_FILE = PROJECT_ROOT / "README.md"

