# ============================================================
# Project0 - Skill Registry Tests
#
# File: test_skill_registry.py
#
# Purpose:
#     Verify repository-local Agent Skill discovery, loading,
#     validation, and path safety.
#
# ============================================================

from pathlib import Path

import pytest

from project0.skills.skill_registry import SkillRegistry


def _write_skill(
    skills_root: Path,
    name: str,
    *,
    description: str = "Example skill.",
    body: str = "# Instructions\nDo the work.",
    extra_frontmatter: str = "",
) -> Path:
    """Create one repository-local SKILL.md test fixture."""

    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            f"{extra_frontmatter}"
            "---\n"
            f"{body}\n"
        ),
        encoding="utf-8",
    )
    return skill_file


def test_discover_returns_metadata_without_loading_instructions(
    tmp_path: Path,
) -> None:
    """Discovery provides progressive metadata for valid local skills."""

    skills_root = tmp_path / "skills"
    _write_skill(
        skills_root,
        "strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
    )

    discovered = SkillRegistry(skills_root).discover()

    assert len(discovered) == 1
    assert discovered[0].name == "strict-documentation-editor"
    assert discovered[0].description == (
        "Preserve controlled documentation artifacts."
    )
    assert discovered[0].skill_path == (
        skills_root / "strict-documentation-editor" / "SKILL.md"
    )


def test_discover_returns_skills_in_deterministic_name_order(
    tmp_path: Path,
) -> None:
    """Skill discovery order is deterministic."""

    skills_root = tmp_path / "skills"
    _write_skill(skills_root, "technical-writer")
    _write_skill(skills_root, "repository-analyst")

    discovered = SkillRegistry(skills_root).discover()

    assert tuple(skill.name for skill in discovered) == (
        "repository-analyst",
        "technical-writer",
    )


def test_load_returns_full_skill_definition(tmp_path: Path) -> None:
    """Loading returns instructions and additional frontmatter metadata."""

    skills_root = tmp_path / "skills"
    skill_file = _write_skill(
        skills_root,
        "strict-documentation-editor",
        description="Preserve controlled documentation artifacts.",
        body="# Rules\n- Preserve formatting.",
        extra_frontmatter="metadata:\n  category: documentation\n",
    )

    skill = SkillRegistry(skills_root).load(
        "strict-documentation-editor"
    )

    assert skill.name == "strict-documentation-editor"
    assert skill.description == (
        "Preserve controlled documentation artifacts."
    )
    assert skill.skill_path == skill_file
    assert skill.instructions == "# Rules\n- Preserve formatting."
    assert skill.metadata == {
        "metadata": {
            "category": "documentation",
        }
    }


def test_missing_skills_root_discovers_no_skills(tmp_path: Path) -> None:
    """An absent local skills directory is a valid empty registry."""

    registry = SkillRegistry(tmp_path / "skills")

    assert registry.discover() == ()


def test_load_rejects_unknown_skill(tmp_path: Path) -> None:
    """Unknown local skills fail explicitly."""

    with pytest.raises(ValueError, match="Skill was not found"):
        SkillRegistry(tmp_path / "skills").load("missing-skill")


def test_load_rejects_path_traversal_name(tmp_path: Path) -> None:
    """Skill names cannot escape the configured local skills root."""

    with pytest.raises(ValueError, match="Skill name must use"):
        SkillRegistry(tmp_path / "skills").load("../outside")


def test_skill_requires_yaml_frontmatter(tmp_path: Path) -> None:
    """SKILL.md files must begin with YAML frontmatter."""

    skill_dir = tmp_path / "skills" / "invalid-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Instructions\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="must begin with YAML frontmatter",
    ):
        SkillRegistry(tmp_path / "skills").load("invalid-skill")


def test_skill_requires_name_and_description(tmp_path: Path) -> None:
    """Required Agent Skills frontmatter fields are validated."""

    skill_dir = tmp_path / "skills" / "invalid-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: invalid-skill\n"
        "---\n"
        "# Instructions\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="description must be a non-empty string",
    ):
        SkillRegistry(tmp_path / "skills").load("invalid-skill")


def test_skill_name_must_match_parent_directory(tmp_path: Path) -> None:
    """A skill's frontmatter name matches its stable directory name."""

    skill_dir = tmp_path / "skills" / "expected-name"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: different-name\n"
        "description: Example.\n"
        "---\n"
        "# Instructions\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="must match its parent directory",
    ):
        SkillRegistry(tmp_path / "skills").load("expected-name")
