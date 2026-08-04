# ============================================================
# Project0 - Repository Tools
#
# File: repository_service.py
#
# Purpose:
#     Provide read-only repository discovery,
#     file filtering, metadata collection, and
#     text-file retrieval services.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Sequence


class RepositoryErrorCode(StrEnum):
    """Standard repository service error categories."""

    INVALID_REPOSITORY_ROOT = "invalid_repository_root"
    FILE_NOT_FOUND = "file_not_found"
    PATH_OUTSIDE_REPOSITORY = "path_outside_repository"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_READ_ERROR = "file_read_error"
    INVALID_REQUEST = "invalid_request"


@dataclass(frozen=True, slots=True)
class RepositoryError:
    """Structured error returned by the repository service."""

    code: RepositoryErrorCode
    message: str
    path: str | None = None
    retryable: bool = False
    technical_details: str | None = None


@dataclass(frozen=True, slots=True)
class RepositoryFile:
    """Metadata describing a file contained in the repository."""

    relative_path: str
    extension: str
    size_bytes: int
    modified_at: datetime
    is_documentation: bool


@dataclass(frozen=True, slots=True)
class FileContent:
    """Repository file metadata and decoded text content."""

    file: RepositoryFile
    content: str
    encoding: str = "utf-8"


@dataclass(frozen=True, slots=True)
class RepositoryQuery:
    """Criteria used to discover repository files."""

    extensions: frozenset[str] | None = None
    include_hidden: bool = False


@dataclass(frozen=True, slots=True)
class RepositoryListResult:
    """Result returned by a repository file-discovery operation."""

    files: tuple[RepositoryFile, ...] = ()
    errors: tuple[RepositoryError, ...] = ()

    @property
    def succeeded(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class FileReadResult:
    """Result returned when reading one repository file."""

    file_content: FileContent | None = None
    error: RepositoryError | None = None

    @property
    def succeeded(self) -> bool:
        return self.file_content is not None and self.error is None


@dataclass(frozen=True, slots=True)
class FileBatchResult:
    """Result returned when reading multiple repository files."""

    files: tuple[FileContent, ...] = ()
    errors: tuple[RepositoryError, ...] = ()

    @property
    def succeeded(self) -> bool:
        return not self.errors


@dataclass(slots=True)
class RepositoryService:
    """Read-only access to files within one validated repository root.

    External callers identify files using repository-relative paths. All paths
    are resolved and validated before access to prevent traversal outside the
    configured repository root.
    """

    repository_root: Path
    supported_extensions: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {".md", ".yml", ".yaml", ".toml", ".py", ".json"}
        )
    )
    excluded_directories: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                ".git",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                ".tox",
                ".venv",
                "venv",
                "__pycache__",
                "build",
                "dist",
                "htmlcov",
                "node_modules",
                "site",
            }
        )
    )
    excluded_file_suffixes: tuple[str, ...] = (
        "~",
        ".bak",
        ".orig",
        ".rej",
        ".swp",
        ".tmp",
    )

    def __post_init__(self) -> None:
        root = self.repository_root.expanduser().resolve()

        if not root.exists():
            raise ValueError(f"Repository root does not exist: {root}")

        if not root.is_dir():
            raise ValueError(f"Repository root is not a directory: {root}")

        self.repository_root = root
        self.supported_extensions = frozenset(
            self._normalize_extension(ext) for ext in self.supported_extensions
        )

    def list_files(
        self,
        query: RepositoryQuery | None = None,
    ) -> RepositoryListResult:
        """Discover supported files in deterministic relative-path order."""

        query = query or RepositoryQuery()
        requested_extensions = self._resolve_requested_extensions(query)

        files: list[RepositoryFile] = []
        errors: list[RepositoryError] = []

        for path in self.repository_root.rglob("*"):
            try:
                if not path.is_file():
                    continue

                relative_path = path.relative_to(self.repository_root)

                if self._is_excluded(relative_path, query.include_hidden):
                    continue

                extension = path.suffix.lower()
                if extension not in requested_extensions:
                    continue

                files.append(self._build_metadata(path))

            except OSError as exc:
                errors.append(
                    RepositoryError(
                        code=RepositoryErrorCode.FILE_READ_ERROR,
                        message="Unable to inspect repository file.",
                        path=self._display_path(path),
                        retryable=True,
                        technical_details=str(exc),
                    )
                )

        files.sort(key=lambda item: item.relative_path.casefold())
        errors.sort(key=lambda item: (item.path or "").casefold())

        return RepositoryListResult(
            files=tuple(files),
            errors=tuple(errors),
        )

    def read_file(self, relative_path: str | Path) -> FileReadResult:
        """Safely read one supported UTF-8 text file."""

        resolved_path, error = self._resolve_repository_file(relative_path)
        if error is not None:
            return FileReadResult(error=error)

        assert resolved_path is not None

        extension = resolved_path.suffix.lower()
        if extension not in self.supported_extensions:
            return FileReadResult(
                error=RepositoryError(
                    code=RepositoryErrorCode.UNSUPPORTED_FILE_TYPE,
                    message=f"Unsupported file type: {extension or '<none>'}",
                    path=self._display_path(resolved_path),
                )
            )

        try:
            content = resolved_path.read_text(encoding="utf-8")
            metadata = self._build_metadata(resolved_path)
        except UnicodeDecodeError as exc:
            return FileReadResult(
                error=RepositoryError(
                    code=RepositoryErrorCode.FILE_READ_ERROR,
                    message="File is not valid UTF-8 text.",
                    path=self._display_path(resolved_path),
                    technical_details=str(exc),
                )
            )
        except OSError as exc:
            return FileReadResult(
                error=RepositoryError(
                    code=RepositoryErrorCode.FILE_READ_ERROR,
                    message="Unable to read repository file.",
                    path=self._display_path(resolved_path),
                    retryable=True,
                    technical_details=str(exc),
                )
            )

        return FileReadResult(
            file_content=FileContent(
                file=metadata,
                content=content,
            )
        )

    def read_files(
        self,
        relative_paths: Sequence[str | Path],
    ) -> FileBatchResult:
        """Read multiple files while preserving successful partial results."""

        files: list[FileContent] = []
        errors: list[RepositoryError] = []

        for relative_path in relative_paths:
            result = self.read_file(relative_path)

            if result.file_content is not None:
                files.append(result.file_content)

            if result.error is not None:
                errors.append(result.error)

        files.sort(key=lambda item: item.file.relative_path.casefold())
        errors.sort(key=lambda item: (item.path or "").casefold())

        return FileBatchResult(
            files=tuple(files),
            errors=tuple(errors),
        )

    def list_documentation_files(self) -> RepositoryListResult:
        """Convenience operation for discovering Markdown documentation."""

        return self.list_files(
            RepositoryQuery(extensions=frozenset({".md"}))
        )

    def _resolve_requested_extensions(
        self,
        query: RepositoryQuery,
    ) -> frozenset[str]:
        if query.extensions is None:
            return self.supported_extensions

        normalized = frozenset(
            self._normalize_extension(ext) for ext in query.extensions
        )

        return normalized.intersection(self.supported_extensions)

    def _resolve_repository_file(
        self,
        relative_path: str | Path,
    ) -> tuple[Path | None, RepositoryError | None]:
        raw_path = Path(relative_path)

        if raw_path.is_absolute():
            return None, RepositoryError(
                code=RepositoryErrorCode.INVALID_REQUEST,
                message="Repository files must be identified by relative path.",
                path=str(relative_path),
            )

        candidate = (self.repository_root / raw_path).resolve()

        try:
            candidate.relative_to(self.repository_root)
        except ValueError:
            return None, RepositoryError(
                code=RepositoryErrorCode.PATH_OUTSIDE_REPOSITORY,
                message="Requested path resolves outside the repository root.",
                path=str(relative_path),
            )

        if not candidate.exists() or not candidate.is_file():
            return None, RepositoryError(
                code=RepositoryErrorCode.FILE_NOT_FOUND,
                message="Repository file was not found.",
                path=str(relative_path),
            )

        return candidate, None

    def _is_excluded(
        self,
        relative_path: Path,
        include_hidden: bool,
    ) -> bool:
        if any(
            part in self.excluded_directories
            for part in relative_path.parts[:-1]
        ):
            return True

        if not include_hidden and any(
            part.startswith(".") for part in relative_path.parts
        ):
            return True

        filename = relative_path.name
        return filename.endswith(self.excluded_file_suffixes)

    def _build_metadata(self, path: Path) -> RepositoryFile:
        stat = path.stat()
        relative_path = path.relative_to(self.repository_root).as_posix()

        return RepositoryFile(
            relative_path=relative_path,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ),
            is_documentation=path.suffix.lower() == ".md",
        )

    def _display_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.repository_root).as_posix()
        except ValueError:
            return str(path)

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        value = extension.strip().lower()

        if not value:
            raise ValueError("File extension cannot be empty.")

        return value if value.startswith(".") else f".{value}"


def create_repository_service(
    repository_root: str | Path,
) -> RepositoryService:
    """Create a validated RepositoryService instance."""

    return RepositoryService(repository_root=Path(repository_root))
