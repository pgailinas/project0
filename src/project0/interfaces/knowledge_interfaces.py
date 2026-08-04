```python
# ============================================================
# Project0 - Knowledge Interfaces
#
# File: knowledge_interfaces.py
#
# Purpose:
#     Define shared interfaces for repository knowledge
#     services used by Project0 platform components and agents.
#
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from project0.models.knowledge_models import (
    DocumentRecord,
    DocumentSelection,
    KnowledgeRequest,
    KnowledgeResult,
)


class DocumentParserProtocol(Protocol):
    """Interface for parsing repository documents."""

    def parse_document(self, path: Path) -> DocumentRecord:
        """Parse one repository document."""

        ...


class DocumentIndexProtocol(Protocol):
    """Interface for indexing parsed repository documents."""

    def build_index(
        self,
        documents: Sequence[DocumentRecord],
    ) -> None:
        """Build or replace the document index."""

        ...

    def get_document(self, path: Path) -> DocumentRecord | None:
        """Return an indexed document by repository-relative path."""

        ...

    def list_documents(self) -> tuple[DocumentRecord, ...]:
        """Return all indexed documents."""

        ...


class DocumentSelectorProtocol(Protocol):
    """Interface for selecting relevant repository documents."""

    def select_documents(
        self,
        request: KnowledgeRequest,
        documents: Sequence[DocumentRecord],
    ) -> DocumentSelection:
        """Select documents relevant to a knowledge request."""

        ...


class KnowledgeServiceProtocol(Protocol):
    """Interface for repository knowledge services."""

    def build_knowledge(
        self,
        request: KnowledgeRequest,
    ) -> KnowledgeResult:
        """Build repository knowledge for a request."""

        ...
```


