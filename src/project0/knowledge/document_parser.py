# ============================================================
# Project0 - Document Parser
#
# File: document_parser.py
#
# Purpose:
#     Parse repository Markdown documents into shared
#     Project0 knowledge data models.
#
# ============================================================

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from project0.models.knowledge_models import (
    DocumentHeading,
    DocumentLink,
    DocumentRecord,
)


class DocumentParser:
    """Parse repository Markdown documents."""

    _HEADING_PATTERN = re.compile(
        r"^(#{1,6})\s+(.+?)\s*$"
    )

    _LINK_PATTERN = re.compile(
        r"\[([^\]]+)\]\(([^)]+)\)"
    )

    _EXTERNAL_PREFIXES = (
        "http://",
        "https://",
        "mailto:",
    )

    def __init__(self, repository_root: Path) -> None:
        """Initialize the parser with the repository root."""

        self._repository_root = repository_root.resolve()

    def parse_document(self, path: Path) -> DocumentRecord:
        """Parse one repository Markdown document."""

        repository_path = self._normalize_repository_path(path)
        absolute_path = self._repository_root / repository_path

        self._validate_document_path(absolute_path)

        content = absolute_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        headings = self._extract_headings(lines)
        links = self._extract_links(lines)
        title = self._determine_title(
            repository_path,
            headings,
        )

        modified_at = datetime.fromtimestamp(
            absolute_path.stat().st_mtime
        )

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        return DocumentRecord(
            path=repository_path,
            title=title,
            content=content,
            headings=headings,
            links=links,
            modified_at=modified_at,
            content_hash=content_hash,
            metadata={
                "suffix": absolute_path.suffix.lower(),
                "size_bytes": absolute_path.stat().st_size,
            },
        )

    def _normalize_repository_path(self, path: Path) -> Path:
        """Return a repository-relative document path."""

        if path.is_absolute():
            resolved_path = path.resolve()

            try:
                return resolved_path.relative_to(
                    self._repository_root
                )
            except ValueError as error:
                raise ValueError(
                    "Document path is outside the repository root."
                ) from error

        return path

    def _validate_document_path(
        self,
        absolute_path: Path,
    ) -> None:
        """Validate that the document can be parsed."""

        resolved_path = absolute_path.resolve()

        try:
            resolved_path.relative_to(self._repository_root)
        except ValueError as error:
            raise ValueError(
                "Document path is outside the repository root."
            ) from error

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Document does not exist: {resolved_path}"
            )

        if not resolved_path.is_file():
            raise ValueError(
                f"Document path is not a file: {resolved_path}"
            )

        if resolved_path.suffix.lower() != ".md":
            raise ValueError(
                "Document parser supports Markdown files only."
            )

    def _extract_headings(
        self,
        lines: list[str],
    ) -> tuple[DocumentHeading, ...]:
        """Extract Markdown headings from document lines."""

        headings: list[DocumentHeading] = []

        for line_number, line in enumerate(lines, start=1):
            match = self._HEADING_PATTERN.match(line)

            if match is None:
                continue

            heading_markers, title = match.groups()
            clean_title = title.strip().rstrip("#").strip()

            headings.append(
                DocumentHeading(
                    level=len(heading_markers),
                    title=clean_title,
                    line_number=line_number,
                    anchor=self._create_anchor(clean_title),
                )
            )

        return tuple(headings)

    def _extract_links(
        self,
        lines: list[str],
    ) -> tuple[DocumentLink, ...]:
        """Extract Markdown links from document lines."""

        links: list[DocumentLink] = []

        for line_number, line in enumerate(lines, start=1):
            for match in self._LINK_PATTERN.finditer(line):
                text, target = match.groups()
                clean_target = target.strip()

                links.append(
                    DocumentLink(
                        text=text.strip(),
                        target=clean_target,
                        line_number=line_number,
                        is_internal=self._is_internal_link(
                            clean_target
                        ),
                    )
                )

        return tuple(links)

    def _determine_title(
        self,
        path: Path,
        headings: tuple[DocumentHeading, ...],
    ) -> str:
        """Determine the document title."""

        for heading in headings:
            if heading.level == 1:
                return heading.title

        return path.stem.replace("_", " ").replace("-", " ")

    def _create_anchor(self, title: str) -> str:
        """Create a Markdown-compatible heading anchor."""

        anchor = title.strip().lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)
        anchor = re.sub(r"[\s_]+", "-", anchor)
        anchor = re.sub(r"-+", "-", anchor)

        return anchor.strip("-")

    def _is_internal_link(self, target: str) -> bool:
        """Return whether a link target is repository-local."""

        normalized_target = target.lower()

        return not normalized_target.startswith(
            self._EXTERNAL_PREFIXES
        )


