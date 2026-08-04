# ============================================================
# Project0 - Context Models
#
# File: test_context_models.py
#
# Purpose:
#     Verify shared context model values, defaults,
#     immutability, status behavior, and helper properties.
#
# ============================================================

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from project0.models.context_models import (
    ContextBuildStatus,
    ContextDocument,
    ContextPackage,
    ContextRequest,
)


def test_context_build_status_values() -> None:
    assert ContextBuildStatus.COMPLETED == "completed"
    assert (
        ContextBuildStatus.COMPLETED_WITH_WARNINGS
        == "completed_with_warnings"
    )
    assert ContextBuildStatus.FAILED == "failed"


def test_context_request_uses_default_project_id() -> None:
    request = ContextRequest(context_id="context-1")

    assert request.context_id == "context-1"
    assert request.project_id == "Project0"


def test_context_request_accepts_custom_project_id() -> None:
    request = ContextRequest(
        context_id="context-2",
        project_id="ProductA",
    )

    assert request.project_id == "ProductA"


def test_context_request_is_immutable() -> None:
    request = ContextRequest(context_id="context-3")

    with pytest.raises(FrozenInstanceError):
        request.project_id = "Changed"  # type: ignore[misc]


def test_context_document_stores_supplied_values() -> None:
    modified_at = datetime(2026, 8, 4, tzinfo=timezone.utc)

    document = ContextDocument(
        relative_path="docs/Architecture.md",
        content="# Architecture\n",
        size_bytes=15,
        modified_at=modified_at,
    )

    assert document.relative_path == "docs/Architecture.md"
    assert document.content == "# Architecture\n"
    assert document.size_bytes == 15
    assert document.modified_at == modified_at


def test_context_document_is_immutable() -> None:
    document = ContextDocument(
        relative_path="README.md",
        content="# Project0\n",
        size_bytes=11,
        modified_at=datetime(
            2026,
            8,
            4,
            tzinfo=timezone.utc,
        ),
    )

    with pytest.raises(FrozenInstanceError):
        document.content = "Changed"  # type: ignore[misc]


def test_context_package_uses_empty_warning_and_error_defaults() -> None:
    package = ContextPackage(
        context_id="context-4",
        project_id="Project0",
        status=ContextBuildStatus.COMPLETED,
        created_at=datetime(
            2026,
            8,
            4,
            tzinfo=timezone.utc,
        ),
        documents=(),
        source_count=0,
        total_characters=0,
    )

    assert package.warnings == ()
    assert package.errors == ()


def test_completed_context_package_succeeds() -> None:
    package = ContextPackage(
        context_id="context-complete",
        project_id="Project0",
        status=ContextBuildStatus.COMPLETED,
        created_at=datetime(
            2026,
            8,
            4,
            tzinfo=timezone.utc,
        ),
        documents=(),
        source_count=0,
        total_characters=0,
    )

    assert package.succeeded is True
    assert package.has_warnings is False
    assert package.has_errors is False


def test_context_package_with_warnings_succeeds() -> None:
    package = ContextPackage(
        context_id="context-warning",
        project_id="Project0",
        status=ContextBuildStatus.COMPLETED_WITH_WARNINGS,
        created_at=datetime(
            2026,
            8,
            4,
            tzinfo=timezone.utc,
        ),
        documents=(),
        source_count=0,
        total_characters=0,
        warnings=("One document could not be read.",),
    )

    assert package.succeeded is True
    assert package.has_warnings is True
    assert package.has_errors is False


def test_failed_context_package_does_not_succeed() -> None:
    package = ContextPackage(
        context_id="context-failed",
        project_id="Project0",
        status=ContextBuildStatus.FAILED,
        created_at=datetime(
            2026,
            8,
            4,
            tzinfo=timezone.utc,
        ),
        documents=(),
        source_count=0,
        total_characters=0,
        errors=("Repository discovery failed.",),
    )

    assert package.succeeded is False
    assert package.has_warnings is False
    assert package.has_errors is True


def test_context_package_preserves_documents_and_counts() -> None:
    modified_at = datetime(2026, 8, 4, tzinfo=timezone.utc)
    document = ContextDocument(
        relative_path="README.md",
        content="# Project0\n",
        size_bytes=11,
        modified_at=modified_at,
    )

    package = ContextPackage(
        context_id="context-documents",
        project_id="Project0",
        status=ContextBuildStatus.COMPLETED,
        created_at=modified_at,
        documents=(document,),
        source_count=1,
        total_characters=len(document.content),
    )

    assert package.documents == (document,)
    assert package.source_count == 1
    assert package.total_characters == len(document.content)


def test_context_package_is_immutable() -> None:
    package = ContextPackage(
        context_id="context-immutable",
        project_id="Project0",
        status=ContextBuildStatus.COMPLETED,
        created_at=datetime(
            2026,
            8,
            4,
            tzinfo=timezone.utc,
        ),
        documents=(),
        source_count=0,
        total_characters=0,
    )

    with pytest.raises(FrozenInstanceError):
        package.source_count = 1  # type: ignore[misc]
