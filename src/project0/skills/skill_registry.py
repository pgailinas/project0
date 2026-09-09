# ============================================================
# Project0 - Skill Registry
#
# File: skill_registry.py
#
# Purpose:
#     Discover and load repository-local Agent Skills using
#     directory-per-skill SKILL.md definitions.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

from project0.models.skill_models import (
    SkillDefinition,
    SkillMetadata,
)


_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SkillRegistry:
    """Discover and load repository-local Project0 Agent Skills."""

    def __init__(self, skills_root: Path) -> None:
        self._skills_root = skills_root.resolve()

    @property
    def skills_root(self) -> Path:
        """Return the configured repository-local skills directory."""

        return self._skills_root

    def discover(self) -> tuple[SkillMetadata, ...]:
        """Return metadata for valid local skills without loading bodies."""

        if not self._skills_root.exists():
            return ()

        if not self._skills_root.is_dir():
            raise ValueError(
                "Configured skills root is not a directory: "
                f"{self._skills_root}"
            )

        discovered: list[SkillMetadata] = []

        for skill_dir in sorted(
            (
                path
                for path in self._skills_root.iterdir()
                if path.is_dir()
            ),
            key=lambda path: path.name,
        ):
            skill_file = skill_dir / "SKILL.md"

            if not skill_file.is_file():
                continue

            metadata, _ = self._read_skill_file(
                skill_file,
                include_instructions=False,
            )
            discovered.append(metadata)

        return tuple(discovered)

    def load(self, name: str) -> SkillDefinition:
        """Load one local skill by its stable directory/name identifier."""

        normalized_name = name.strip()

        if not _SKILL_NAME_PATTERN.fullmatch(normalized_name):
            raise ValueError(
                "Skill name must use lowercase letters, numbers, "
                "and hyphens only."
            )

        skill_dir = (self._skills_root / normalized_name).resolve()

        try:
            skill_dir.relative_to(self._skills_root)
        except ValueError as error:
            raise ValueError(
                "Skill path is outside the configured skills root."
            ) from error

        skill_file = skill_dir / "SKILL.md"

        if not skill_file.is_file():
            raise ValueError(
                f"Skill was not found: {normalized_name}"
            )

        metadata, instructions = self._read_skill_file(
            skill_file,
            include_instructions=True,
        )

        return SkillDefinition(
            name=metadata.name,
            description=metadata.description,
            skill_path=metadata.skill_path,
            instructions=instructions,
            metadata=dict(metadata.metadata),
        )

    def _read_skill_file(
        self,
        skill_file: Path,
        *,
        include_instructions: bool,
    ) -> tuple[SkillMetadata, str]:
        """Parse and validate one local SKILL.md file."""

        content = skill_file.read_text(encoding="utf-8")

        frontmatter, instructions = self._split_frontmatter(content)

        parsed = yaml.safe_load(frontmatter)

        if not isinstance(parsed, dict):
            raise ValueError(
                f"Skill frontmatter must be a mapping: {skill_file}"
            )

        name = self._require_string(parsed, "name", skill_file)
        description = self._require_string(
            parsed,
            "description",
            skill_file,
        )

        if not _SKILL_NAME_PATTERN.fullmatch(name):
            raise ValueError(
                f"Invalid skill name in {skill_file}: {name}"
            )

        if name != skill_file.parent.name:
            raise ValueError(
                "Skill name must match its parent directory: "
                f"{skill_file}"
            )

        extra_metadata: dict[str, Any] = {
            key: value
            for key, value in parsed.items()
            if key not in {"name", "description"}
        }

        metadata = SkillMetadata(
            name=name,
            description=description,
            skill_path=skill_file,
            metadata=extra_metadata,
        )

        if not include_instructions:
            instructions = ""

        return metadata, instructions

    @staticmethod
    def _split_frontmatter(content: str) -> tuple[str, str]:
        """Split required YAML frontmatter from Markdown instructions."""

        lines = content.splitlines()

        if not lines or lines[0].strip() != "---":
            raise ValueError(
                "Skill file must begin with YAML frontmatter."
            )

        closing_index = next(
            (
                index
                for index, line in enumerate(lines[1:], start=1)
                if line.strip() == "---"
            ),
            None,
        )

        if closing_index is None:
            raise ValueError(
                "Skill YAML frontmatter is not terminated."
            )

        frontmatter = "\n".join(lines[1:closing_index])
        instructions = "\n".join(lines[closing_index + 1:]).strip()

        return frontmatter, instructions

    @staticmethod
    def _require_string(
        mapping: dict[str, Any],
        field_name: str,
        skill_file: Path,
    ) -> str:
        """Return one required non-empty frontmatter string."""

        value = mapping.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Skill {field_name} must be a non-empty string: "
                f"{skill_file}"
            )

        return value.strip()
