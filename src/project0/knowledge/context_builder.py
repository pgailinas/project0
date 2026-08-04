# ============================================================
# Project0 - Knowledge Services
#
# File: context_builder.py
#
# Purpose:
#     Assemble validated Project0 documentation into a
#     structured context package for AI agents.
#
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from project0.knowledge.context_filters import ContextFilter
from project0.knowledge.context_rules import (
    ContextRuleRegistry,
    ContextWorkflowType,
    create_context_rule_registry,
)
from project0.models.context_models import (
    ContextBuildStatus,
    ContextDocument,
    ContextPackage,
)
from project0.repository.repository_service import (
    FileBatchResult,
    RepositoryService,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ContextBuilder:
    """Build task-specific documentation context from repository content.

    The initial implementation selects Markdown files using deterministic
    workflow-specific rules. Ranking and semantic retrieval are intentionally
    deferred.
    """

    repository_service: RepositoryService
    rule_registry: ContextRuleRegistry = field(
        default_factory=create_context_rule_registry
    )
    project_id: str = "Project0"

    def build_documentation_context(
        self,
        context_id: str,
        workflow_type: ContextWorkflowType,
    ) -> ContextPackage:
        """Discover, select, read, and package Markdown documentation."""

        if not context_id.strip():
            raise ValueError("Context identifier cannot be empty.")

        LOGGER.info(
            "Building documentation context '%s' for project '%s' "
            "and workflow type '%s'.",
            context_id,
            self.project_id,
            workflow_type,
        )

        discovery_result = (
            self.repository_service.list_documentation_files()
        )

        if discovery_result.errors:
            error_messages = tuple(
                error.message for error in discovery_result.errors
            )

            LOGGER.error(
                "Documentation discovery failed for context '%s'.",
                context_id,
            )

            return ContextPackage(
                context_id=context_id,
                project_id=self.project_id,
                status=ContextBuildStatus.FAILED,
                created_at=self._utc_now(),
                documents=(),
                source_count=0,
                total_characters=0,
                errors=error_messages,
            )

        filter_criteria = self.rule_registry.get_filter_criteria(
            workflow_type
        )
        context_filter = ContextFilter(criteria=filter_criteria)
        filtered_files = context_filter.apply(
            discovery_result.files
        )

        LOGGER.info(
            "Discovered %d documentation files and selected %d "
            "for context '%s'.",
            len(discovery_result.files),
            len(filtered_files),
            context_id,
        )

        relative_paths = [
            repository_file.relative_path
            for repository_file in filtered_files
        ]

        if not relative_paths:
            warning = (
                "No Markdown documentation files matched the "
                "workflow context rules."
            )

            LOGGER.warning(
                "%s Context id: %s",
                warning,
                context_id,
            )

            return ContextPackage(
                context_id=context_id,
                project_id=self.project_id,
                status=ContextBuildStatus.COMPLETED_WITH_WARNINGS,
                created_at=self._utc_now(),
                documents=(),
                source_count=0,
                total_characters=0,
                warnings=(warning,),
            )

        read_result = self.repository_service.read_files(
            relative_paths
        )

        package = self._create_context_package(
            context_id=context_id,
            read_result=read_result,
        )

        LOGGER.info(
            "Built context '%s' with %d documents.",
            context_id,
            package.source_count,
        )

        return package

    def _create_context_package(
        self,
        context_id: str,
        read_result: FileBatchResult,
    ) -> ContextPackage:
        """Create a context package from repository read results."""

        documents = tuple(
            ContextDocument(
                relative_path=file_content.file.relative_path,
                content=file_content.content,
                size_bytes=file_content.file.size_bytes,
                modified_at=file_content.file.modified_at,
            )
            for file_content in read_result.files
        )

        warnings = tuple(
            self._format_read_warning(error.path, error.message)
            for error in read_result.errors
        )

        status = (
            ContextBuildStatus.COMPLETED_WITH_WARNINGS
            if warnings
            else ContextBuildStatus.COMPLETED
        )

        return ContextPackage(
            context_id=context_id,
            project_id=self.project_id,
            status=status,
            created_at=self._utc_now(),
            documents=documents,
            source_count=len(documents),
            total_characters=sum(
                len(document.content)
                for document in documents
            ),
            warnings=warnings,
        )

    @staticmethod
    def _format_read_warning(
        path: str | None,
        message: str,
    ) -> str:
        """Format a repository read error as a context warning."""

        if path:
            return f"{path}: {message}"

        return message

    @staticmethod
    def _utc_now() -> datetime:
        """Return the current timezone-aware UTC timestamp."""

        return datetime.now(timezone.utc)


def create_context_builder(
    repository_service: RepositoryService,
    project_id: str = "Project0",
    rule_registry: ContextRuleRegistry | None = None,
) -> ContextBuilder:
    """Create a ContextBuilder instance."""

    return ContextBuilder(
        repository_service=repository_service,
        rule_registry=(
            rule_registry or create_context_rule_registry()
        ),
        project_id=project_id,
    )
