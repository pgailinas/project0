# ============================================================
# Project0 - Knowledge Services
#
# File: context_rules.py
#
# Purpose:
#     Define deterministic document-selection rules for
#     Project0 workflow and AI-agent context requests.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from project0.knowledge.context_filters import ContextFilterCriteria
from project0.models.context_models import ContextWorkflowType


@dataclass(frozen=True, slots=True)
class ContextRule:
    """Context-selection rule for one workflow type."""

    workflow_type: ContextWorkflowType
    required_patterns: tuple[str, ...]
    optional_patterns: tuple[str, ...] = ()
    excluded_paths: tuple[str, ...] = ()
    excluded_patterns: tuple[str, ...] = ()

    def to_filter_criteria(self) -> ContextFilterCriteria:
        """Convert the rule into deterministic filter criteria."""

        include_patterns = (
            self.required_patterns + self.optional_patterns
        )

        return ContextFilterCriteria(
            extensions=frozenset({".md"}),
            exclude_paths=self.excluded_paths,
            include_patterns=include_patterns,
            exclude_patterns=self.excluded_patterns,
            documentation_only=True,
        )


DEFAULT_CONTEXT_RULES: dict[ContextWorkflowType, ContextRule] = {
    ContextWorkflowType.GENERAL_DOCUMENTATION: ContextRule(
        workflow_type=ContextWorkflowType.GENERAL_DOCUMENTATION,
        required_patterns=(
            "README.md",
            "docs/*.md",
        ),
        excluded_paths=(
            "docs/archive",
        ),
        excluded_patterns=(
            "*Draft*.md",
            "*.bak",
        ),
    ),
    ContextWorkflowType.UPDATE_DOCUMENTATION: ContextRule(
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
        required_patterns=(
            "README.md",
            "docs/Documentation_Standards.md",
            "docs/Project_Charter.md",
            "docs/*Architecture*.md",
            "docs/*Design*.md",
            "docs/Implementation_Roadmap.md",
            "docs/Implementation_Status.md",
        ),
        excluded_paths=(
            "docs/archive",
        ),
        excluded_patterns=(
            "*Draft*.md",
            "*.bak",
        ),
    ),
    ContextWorkflowType.IMPLEMENT_COMPONENT: ContextRule(
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
        required_patterns=(
            "README.md",
            "docs/Project_Charter.md",
            "docs/*Architecture*.md",
            "docs/*Design*.md",
            "docs/Implementation_Roadmap.md",
            "docs/Implementation_Status.md",
        ),
        optional_patterns=(
            "docs/Development_Environment.md",
            "docs/Project_Directory_Structure.md",
            "docs/Shared_Data_Models_and_Error_Contracts.md",
            "docs/Component_Communication_Design.md",
        ),
        excluded_paths=(
            "docs/archive",
        ),
        excluded_patterns=(
            "*Draft*.md",
            "*.bak",
        ),
    ),
    ContextWorkflowType.VALIDATE_DOCUMENTATION: ContextRule(
        workflow_type=ContextWorkflowType.VALIDATE_DOCUMENTATION,
        required_patterns=(
            "README.md",
            "docs/Documentation_Standards.md",
            "docs/*.md",
        ),
        excluded_paths=(
            "docs/archive",
        ),
        excluded_patterns=(
            "*Draft*.md",
            "*.bak",
        ),
    ),
}


@dataclass(slots=True)
class ContextRuleRegistry:
    """Resolve workflow-specific context-selection rules."""

    rules: dict[ContextWorkflowType, ContextRule]

    def get_rule(
        self,
        workflow_type: ContextWorkflowType,
    ) -> ContextRule:
        """Return the rule registered for the workflow type."""

        try:
            return self.rules[workflow_type]
        except KeyError as exc:
            raise ValueError(
                f"No context rule is registered for workflow type: "
                f"{workflow_type}"
            ) from exc

    def get_filter_criteria(
        self,
        workflow_type: ContextWorkflowType,
    ) -> ContextFilterCriteria:
        """Return filter criteria for the workflow type."""

        return self.get_rule(workflow_type).to_filter_criteria()


def create_context_rule_registry() -> ContextRuleRegistry:
    """Create the default Project0 context-rule registry."""

    return ContextRuleRegistry(
        rules=dict(DEFAULT_CONTEXT_RULES)
    )
