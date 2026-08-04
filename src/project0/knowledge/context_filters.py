# ============================================================
# Project0 - Knowledge Services
#
# File: context_filters.py
#
# Purpose:
#     Filter repository files for inclusion in Project0
#     context packages using deterministic selection rules.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Iterable

from project0.repository.repository_service import RepositoryFile


@dataclass(frozen=True, slots=True)
class ContextFilterCriteria:
    """Deterministic rules used to select repository files."""

    extensions: frozenset[str] | None = None
    include_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    include_patterns: tuple[str, ...] = ()
    exclude_patterns: tuple[str, ...] = ()
    documentation_only: bool = True


@dataclass(slots=True)
class ContextFilter:
    """Select repository files eligible for a context package."""

    criteria: ContextFilterCriteria = field(
        default_factory=ContextFilterCriteria
    )

    def apply(
        self,
        files: Iterable[RepositoryFile],
    ) -> tuple[RepositoryFile, ...]:
        """Return files that satisfy the configured criteria."""

        selected = [
            repository_file
            for repository_file in files
            if self.matches(repository_file)
        ]

        selected.sort(
            key=lambda repository_file: (
                repository_file.relative_path.casefold()
            )
        )

        return tuple(selected)

    def matches(self, repository_file: RepositoryFile) -> bool:
        """Return True when a repository file satisfies all rules."""

        if (
            self.criteria.documentation_only
            and not repository_file.is_documentation
        ):
            return False

        if not self._matches_extension(repository_file):
            return False

        relative_path = self._normalize_path(
            repository_file.relative_path
        )

        if not self._matches_included_paths(relative_path):
            return False

        if self._matches_excluded_paths(relative_path):
            return False

        if not self._matches_included_patterns(relative_path):
            return False

        if self._matches_excluded_patterns(relative_path):
            return False

        return True

    def _matches_extension(
        self,
        repository_file: RepositoryFile,
    ) -> bool:
        extensions = self.criteria.extensions

        if extensions is None:
            return True

        normalized_extensions = {
            self._normalize_extension(extension)
            for extension in extensions
        }

        return (
            repository_file.extension.lower()
            in normalized_extensions
        )

    def _matches_included_paths(
        self,
        relative_path: str,
    ) -> bool:
        include_paths = self.criteria.include_paths

        if not include_paths:
            return True

        return any(
            self._is_within_path(
                relative_path,
                self._normalize_path(path),
            )
            for path in include_paths
        )

    def _matches_excluded_paths(
        self,
        relative_path: str,
    ) -> bool:
        return any(
            self._is_within_path(
                relative_path,
                self._normalize_path(path),
            )
            for path in self.criteria.exclude_paths
        )

    def _matches_included_patterns(
        self,
        relative_path: str,
    ) -> bool:
        include_patterns = self.criteria.include_patterns

        if not include_patterns:
            return True

        return any(
            fnmatch(relative_path, pattern)
            for pattern in include_patterns
        )

    def _matches_excluded_patterns(
        self,
        relative_path: str,
    ) -> bool:
        return any(
            fnmatch(relative_path, pattern)
            for pattern in self.criteria.exclude_patterns
        )

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        value = extension.strip().lower()

        if not value:
            raise ValueError("File extension cannot be empty.")

        return value if value.startswith(".") else f".{value}"

    @staticmethod
    def _normalize_path(path: str) -> str:
        value = path.strip().replace("\\", "/").strip("/")

        if not value:
            return ""

        return PurePosixPath(value).as_posix()

    @staticmethod
    def _is_within_path(
        relative_path: str,
        parent_path: str,
    ) -> bool:
        if not parent_path:
            return True

        return (
            relative_path == parent_path
            or relative_path.startswith(f"{parent_path}/")
        )


def filter_repository_files(
    files: Iterable[RepositoryFile],
    criteria: ContextFilterCriteria | None = None,
) -> tuple[RepositoryFile, ...]:
    """Filter repository files using the supplied criteria."""

    return ContextFilter(
        criteria=criteria or ContextFilterCriteria()
    ).apply(files)
