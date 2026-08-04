# ============================================================
# Project0 - Repository Tools
#
# File: test_repository_service.py
#
# Purpose:
#     Verify repository discovery, filtering, metadata,
#     safe file access, batch reads, and error handling.
#
# ============================================================

from __future__ import annotations

from pathlib import Path

import pytest

from project0.repository.repository_service import (
    RepositoryErrorCode,
    RepositoryQuery,
    RepositoryService,
    create_repository_service,
)


@pytest.fixture
def repository_root(tmp_path: Path) -> Path:
    """Create a representative temporary Project0 repository."""

    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "project0").mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    (tmp_path / "site").mkdir()
    (tmp_path / "__pycache__").mkdir()

    (tmp_path / "README.md").write_text(
        "# Project0\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "Architecture.md").write_text(
        "# Architecture\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "project0" / "main.py").write_text(
        'print("Project0")\n',
        encoding="utf-8",
    )
    (tmp_path / "mkdocs.yml").write_text(
        "site_name: Project0\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"project0\"\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text(
        "Unsupported text file type.\n",
        encoding="utf-8",
    )

    (tmp_path / ".git" / "config").write_text(
        "[core]\n",
        encoding="utf-8",
    )
    (tmp_path / "site" / "index.html").write_text(
        "<html></html>\n",
        encoding="utf-8",
    )
    (tmp_path / "__pycache__" / "main.pyc").write_bytes(
        b"\x00\x01\x02"
    )
    (tmp_path / "README.md.bak").write_text(
        "Backup file.\n",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def repository_service(repository_root: Path) -> RepositoryService:
    """Create a RepositoryService for the temporary repository."""

    return RepositoryService(repository_root=repository_root)


def test_create_repository_service_resolves_root(
    repository_root: Path,
) -> None:
    service = create_repository_service(repository_root)

    assert service.repository_root == repository_root.resolve()


def test_repository_service_rejects_missing_root(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing"

    with pytest.raises(ValueError, match="does not exist"):
        RepositoryService(repository_root=missing_root)


def test_repository_service_rejects_file_as_root(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "not_a_directory"
    file_path.write_text("content\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        RepositoryService(repository_root=file_path)


def test_list_files_returns_supported_files_in_sorted_order(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_files()

    relative_paths = [item.relative_path for item in result.files]

    assert result.succeeded
    assert relative_paths == sorted(relative_paths, key=str.casefold)
    assert relative_paths == [
        "docs/Architecture.md",
        "mkdocs.yml",
        "pyproject.toml",
        "README.md",
        "src/project0/main.py",
    ]


def test_list_files_excludes_generated_and_hidden_directories(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_files()

    relative_paths = {item.relative_path for item in result.files}

    assert ".git/config" not in relative_paths
    assert "site/index.html" not in relative_paths
    assert "__pycache__/main.pyc" not in relative_paths


def test_list_files_excludes_unsupported_and_backup_files(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_files()

    relative_paths = {item.relative_path for item in result.files}

    assert "notes.txt" not in relative_paths
    assert "README.md.bak" not in relative_paths


def test_list_files_filters_requested_extensions(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_files(
        RepositoryQuery(extensions=frozenset({"md"}))
    )

    relative_paths = [item.relative_path for item in result.files]

    assert result.succeeded
    assert relative_paths == [
        "docs/Architecture.md",
        "README.md",
    ]


def test_list_documentation_files_returns_only_markdown(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_documentation_files()

    assert result.succeeded
    assert result.files
    assert all(item.extension == ".md" for item in result.files)
    assert all(item.is_documentation for item in result.files)


def test_list_files_returns_expected_metadata(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_files(
        RepositoryQuery(extensions=frozenset({".md"}))
    )

    readme = next(
        item for item in result.files
        if item.relative_path == "README.md"
    )

    assert readme.extension == ".md"
    assert readme.size_bytes > 0
    assert readme.modified_at.tzinfo is not None
    assert readme.is_documentation is True


def test_read_file_returns_content_and_metadata(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.read_file("docs/Architecture.md")

    assert result.succeeded
    assert result.file_content is not None
    assert result.file_content.content == "# Architecture\n"
    assert (
        result.file_content.file.relative_path
        == "docs/Architecture.md"
    )
    assert result.file_content.encoding == "utf-8"


def test_read_file_rejects_absolute_path(
    repository_service: RepositoryService,
    repository_root: Path,
) -> None:
    result = repository_service.read_file(
        repository_root / "README.md"
    )

    assert not result.succeeded
    assert result.error is not None
    assert result.error.code == RepositoryErrorCode.INVALID_REQUEST


def test_read_file_rejects_path_outside_repository(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.read_file("../outside.md")

    assert not result.succeeded
    assert result.error is not None
    assert (
        result.error.code
        == RepositoryErrorCode.PATH_OUTSIDE_REPOSITORY
    )


def test_read_file_returns_not_found_error(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.read_file("docs/Missing.md")

    assert not result.succeeded
    assert result.error is not None
    assert result.error.code == RepositoryErrorCode.FILE_NOT_FOUND


def test_read_file_rejects_unsupported_extension(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.read_file("notes.txt")

    assert not result.succeeded
    assert result.error is not None
    assert (
        result.error.code
        == RepositoryErrorCode.UNSUPPORTED_FILE_TYPE
    )


def test_read_file_reports_invalid_utf8(
    repository_service: RepositoryService,
    repository_root: Path,
) -> None:
    invalid_file = repository_root / "invalid.md"
    invalid_file.write_bytes(b"\xff\xfe\x00")

    result = repository_service.read_file("invalid.md")

    assert not result.succeeded
    assert result.error is not None
    assert result.error.code == RepositoryErrorCode.FILE_READ_ERROR
    assert "UTF-8" in result.error.message


def test_read_files_preserves_successful_partial_results(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.read_files(
        [
            "README.md",
            "docs/Missing.md",
            "docs/Architecture.md",
        ]
    )

    relative_paths = [
        item.file.relative_path for item in result.files
    ]

    assert not result.succeeded
    assert relative_paths == [
        "docs/Architecture.md",
        "README.md",
    ]
    assert len(result.errors) == 1
    assert result.errors[0].code == RepositoryErrorCode.FILE_NOT_FOUND


def test_read_files_returns_deterministic_order(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.read_files(
        [
            "README.md",
            "docs/Architecture.md",
        ]
    )

    relative_paths = [
        item.file.relative_path for item in result.files
    ]

    assert relative_paths == sorted(relative_paths, key=str.casefold)


def test_extension_filter_ignores_unsupported_requested_types(
    repository_service: RepositoryService,
) -> None:
    result = repository_service.list_files(
        RepositoryQuery(
            extensions=frozenset({".md", ".txt"})
        )
    )

    relative_paths = {item.relative_path for item in result.files}

    assert "README.md" in relative_paths
    assert "docs/Architecture.md" in relative_paths
    assert "notes.txt" not in relative_paths
