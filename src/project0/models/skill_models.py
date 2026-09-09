# ============================================================
# Project0 - Skill Models
#
# File: skill_models.py
#
# Purpose:
#     Define immutable models for repository-local Project0
#     Agent Skills.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    """Metadata discovered from a repository-local SKILL.md file."""

    name: str
    description: str
    skill_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """A fully loaded repository-local Agent Skill."""

    name: str
    description: str
    skill_path: Path
    instructions: str
    metadata: dict[str, Any] = field(default_factory=dict)
