# ============================================================
# Project0 - Repository Interfaces
#
# File: repository_interfaces.py
#
# Purpose:
#     Define the public read-only repository interface used
#     by Project0 platform components and AI agents.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from project0.repository.repository_service import (
    FileBatchResult,
    FileReadResult,
    RepositoryListResult,
    RepositoryQuery,
)


class RepositoryInterface(Protocol):
    """Public contract for read-only repository access."""

    def list_files(
        self,
        query: RepositoryQuery | None = None,
    ) -> RepositoryListResult:
        """Discover supported repository files."""

    def list_documentation_files(self) -> RepositoryListResult:
        """Discover Markdown documentation files."""

    def read_file(
        self,
        relative_path: str | Path,
    ) -> FileReadResult:
        """Read one supported repository file."""

    def read_files(
        self,
        relative_paths: Sequence[str | Path],
    ) -> FileBatchResult:
        """Read multiple repository files."""
