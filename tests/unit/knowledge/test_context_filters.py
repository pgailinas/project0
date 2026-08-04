# ============================================================
# Project0 - Knowledge Services
#
# File: test_context_filters.py
#
# Purpose:
#     Verify deterministic repository file filtering by
#     documentation status, extension, path, and patterns.
#
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from project0.knowledge.context_filters import (
    ContextFilter,
    ContextFilterCriteria,
    filter_repository_files,
)
from project0.repository.repository_service import RepositoryFile


MODIFIED_AT = datetime(2026, 8, 4, tzinfo=timezone.utc)


def _repository_file(
    relative_path: str,
    *,
    extension: str = ".md",
    is_documentation: bool = True,
) -> RepositoryFile:
    """Create repository metadata for filter tests."""

    return RepositoryFile(
        relative_path=relative_path,
        extension=extension,
        size_bytes=100,
        modified_at=MODIFIED_AT,
        is_documentation=is_documentation,
    )


def test_default_filter_includes_documentation_files() -> None:
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Architecture.md"),
    )

    result = ContextFilter().apply(files)

    assert result == (
        _repository_file("docs/Architecture.md"),
        _repository_file("README.md"),
    )


def test_default_filter_excludes_non_documentation_files() -> None:
    files = (
        _repository_file("README.md"),
        _repository_file(
            "src/project0/main.py",
            extension=".py",
            is_documentation=False,
        ),
    )

    result = ContextFilter().apply(files)

    assert [item.relative_path for item in result] == [
        "README.md",
    ]


def test_documentation_only_can_be_disabled() -> None:
    criteria = ContextFilterCriteria(
        documentation_only=False
    )
    files = (
        _repository_file("README.md"),
        _repository_file(
            "src/project0/main.py",
            extension=".py",
            is_documentation=False,
        ),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "README.md",
        "src/project0/main.py",
    ]


def test_filter_by_extension() -> None:
    criteria = ContextFilterCriteria(
        extensions=frozenset({".md"}),
        documentation_only=False,
    )
    files = (
        _repository_file("README.md"),
        _repository_file(
            "mkdocs.yml",
            extension=".yml",
            is_documentation=False,
        ),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "README.md",
    ]


def test_extension_filter_accepts_missing_dot_and_case() -> None:
    criteria = ContextFilterCriteria(
        extensions=frozenset({"MD"}),
    )
    file = _repository_file("README.md")

    assert ContextFilter(criteria).matches(file)


def test_empty_extension_raises_value_error() -> None:
    criteria = ContextFilterCriteria(
        extensions=frozenset({""}),
    )
    file = _repository_file("README.md")

    with pytest.raises(ValueError, match="cannot be empty"):
        ContextFilter(criteria).matches(file)


def test_include_path_selects_file_and_descendants() -> None:
    criteria = ContextFilterCriteria(
        include_paths=("docs",),
    )
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Architecture.md"),
        _repository_file("docs/agents/Documentation.md"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "docs/agents/Documentation.md",
        "docs/Architecture.md",
    ]


def test_include_path_can_select_exact_file() -> None:
    criteria = ContextFilterCriteria(
        include_paths=("README.md",),
    )
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Architecture.md"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "README.md",
    ]


def test_exclude_path_removes_file_and_descendants() -> None:
    criteria = ContextFilterCriteria(
        exclude_paths=("docs/archive",),
    )
    files = (
        _repository_file("docs/Architecture.md"),
        _repository_file("docs/archive/Old_Architecture.md"),
        _repository_file("docs/archive/history/Decision.md"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "docs/Architecture.md",
    ]


def test_include_and_exclude_paths_are_combined() -> None:
    criteria = ContextFilterCriteria(
        include_paths=("docs",),
        exclude_paths=("docs/archive",),
    )
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Architecture.md"),
        _repository_file("docs/archive/Old.md"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "docs/Architecture.md",
    ]


def test_include_pattern_selects_matching_files() -> None:
    criteria = ContextFilterCriteria(
        include_patterns=("docs/*Architecture*.md",),
    )
    files = (
        _repository_file("docs/Architecture.md"),
        _repository_file("docs/Platform_Architecture.md"),
        _repository_file("docs/Project_Charter.md"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "docs/Architecture.md",
        "docs/Platform_Architecture.md",
    ]


def test_exclude_pattern_removes_matching_files() -> None:
    criteria = ContextFilterCriteria(
        exclude_patterns=("*.bak", "*Draft*.md"),
    )
    files = (
        _repository_file("docs/Architecture.md"),
        _repository_file("docs/Architecture_Draft.md"),
        _repository_file("README.md.bak"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "docs/Architecture.md",
    ]


def test_include_and_exclude_patterns_are_combined() -> None:
    criteria = ContextFilterCriteria(
        include_patterns=("docs/*.md",),
        exclude_patterns=("docs/*Draft*.md",),
    )
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Architecture.md"),
        _repository_file("docs/Architecture_Draft.md"),
    )

    result = ContextFilter(criteria).apply(files)

    assert [item.relative_path for item in result] == [
        "docs/Architecture.md",
    ]


def test_path_normalization_accepts_backslashes_and_slashes() -> None:
    criteria = ContextFilterCriteria(
        include_paths=("docs\\agents\\",),
    )
    file = _repository_file(
        "docs/agents/Documentation.md"
    )

    assert ContextFilter(criteria).matches(file)


def test_filter_output_is_deterministically_sorted() -> None:
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Zeta.md"),
        _repository_file("docs/alpha.md"),
    )

    result = ContextFilter().apply(files)

    assert [item.relative_path for item in result] == [
        "docs/alpha.md",
        "docs/Zeta.md",
        "README.md",
    ]


def test_matches_returns_false_when_any_rule_fails() -> None:
    criteria = ContextFilterCriteria(
        extensions=frozenset({".md"}),
        include_paths=("docs",),
        exclude_patterns=("*Draft*.md",),
    )

    context_filter = ContextFilter(criteria)

    assert context_filter.matches(
        _repository_file("docs/Architecture.md")
    )
    assert not context_filter.matches(
        _repository_file("README.md")
    )
    assert not context_filter.matches(
        _repository_file("docs/Architecture_Draft.md")
    )


def test_convenience_function_uses_default_criteria() -> None:
    files = (
        _repository_file("README.md"),
        _repository_file(
            "src/project0/main.py",
            extension=".py",
            is_documentation=False,
        ),
    )

    result = filter_repository_files(files)

    assert [item.relative_path for item in result] == [
        "README.md",
    ]


def test_convenience_function_uses_supplied_criteria() -> None:
    criteria = ContextFilterCriteria(
        include_paths=("docs",),
    )
    files = (
        _repository_file("README.md"),
        _repository_file("docs/Architecture.md"),
    )

    result = filter_repository_files(files, criteria)

    assert [item.relative_path for item in result] == [
        "docs/Architecture.md",
    ]


def test_apply_returns_tuple() -> None:
    result = ContextFilter().apply(
        [_repository_file("README.md")]
    )

    assert isinstance(result, tuple)
