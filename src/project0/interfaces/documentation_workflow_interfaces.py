# ============================================================
# Project0 - Documentation Workflow Interfaces
#
# File: documentation_workflow_interfaces.py
#
# Purpose:
#     Define public interfaces for documentation workflow,
#     review, repository update, and Git diff services.
#
# ============================================================

from __future__ import annotations

from typing import Protocol

from project0.models.documentation_workflow_models import (
    AppliedDocumentationChange,
    DocumentationChangeProposal,
    DocumentationReview,
    DocumentationWorkflowRequest,
    DocumentationWorkflowResult,
)


class DocumentationWorkflowInterface(Protocol):
    """Public contract for documentation workflow execution."""

    def execute(
        self,
        request: DocumentationWorkflowRequest,
    ) -> DocumentationWorkflowResult:
        """Execute a documentation workflow and return its result."""


class ReviewCoordinatorInterface(Protocol):
    """Public contract for coordinating proposal review decisions."""

    def review(
        self,
        proposal: DocumentationChangeProposal,
    ) -> DocumentationReview:
        """Review one documentation change proposal."""


class RepositoryUpdateInterface(Protocol):
    """Public contract for applying approved documentation changes."""

    def apply(
        self,
        proposal: DocumentationChangeProposal,
        review: DocumentationReview,
    ) -> AppliedDocumentationChange:
        """Apply one reviewed documentation change."""


class GitDiffInterface(Protocol):
    """Public contract for generating repository Git diffs."""

    def generate_diff(
        self,
        repository_paths: tuple[str, ...] = (),
    ) -> str:
        """Generate a Git diff for selected repository paths."""
