# ============================================================
# Project0 - Knowledge Services
#
# File: test_context_rules.py
#
# Purpose:
#     Verify workflow-specific context rules, filter criteria,
#     registry lookup, defaults, and error handling.
#
# ============================================================

from __future__ import annotations

import pytest

from project0.knowledge.context_filters import ContextFilterCriteria
from project0.knowledge.context_rules import (
    DEFAULT_CONTEXT_RULES,
    ContextRule,
    ContextRuleRegistry,
    create_context_rule_registry,
)
from project0.models.context_models import ContextWorkflowType


def test_context_workflow_type_values() -> None:
    assert (
        ContextWorkflowType.GENERAL_DOCUMENTATION
        == "general_documentation"
    )
    assert (
        ContextWorkflowType.UPDATE_DOCUMENTATION
        == "update_documentation"
    )
    assert (
        ContextWorkflowType.IMPLEMENT_COMPONENT
        == "implement_component"
    )
    assert (
        ContextWorkflowType.VALIDATE_DOCUMENTATION
        == "validate_documentation"
    )


def test_context_rule_stores_supplied_values() -> None:
    rule = ContextRule(
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
        required_patterns=("README.md",),
        optional_patterns=("docs/*.md",),
        excluded_paths=("docs/archive",),
        excluded_patterns=("*Draft*.md",),
    )

    assert (
        rule.workflow_type
        == ContextWorkflowType.UPDATE_DOCUMENTATION
    )
    assert rule.required_patterns == ("README.md",)
    assert rule.optional_patterns == ("docs/*.md",)
    assert rule.excluded_paths == ("docs/archive",)
    assert rule.excluded_patterns == ("*Draft*.md",)


def test_context_rule_uses_empty_optional_defaults() -> None:
    rule = ContextRule(
        workflow_type=ContextWorkflowType.GENERAL_DOCUMENTATION,
        required_patterns=("README.md",),
    )

    assert rule.optional_patterns == ()
    assert rule.excluded_paths == ()
    assert rule.excluded_patterns == ()


def test_context_rule_converts_to_filter_criteria() -> None:
    rule = ContextRule(
        workflow_type=ContextWorkflowType.IMPLEMENT_COMPONENT,
        required_patterns=(
            "README.md",
            "docs/*Architecture*.md",
        ),
        optional_patterns=(
            "docs/Development_Environment.md",
        ),
        excluded_paths=("docs/archive",),
        excluded_patterns=("*Draft*.md", "*.bak"),
    )

    criteria = rule.to_filter_criteria()

    assert isinstance(criteria, ContextFilterCriteria)
    assert criteria.extensions == frozenset({".md"})
    assert criteria.include_patterns == (
        "README.md",
        "docs/*Architecture*.md",
        "docs/Development_Environment.md",
    )
    assert criteria.exclude_paths == ("docs/archive",)
    assert criteria.exclude_patterns == (
        "*Draft*.md",
        "*.bak",
    )
    assert criteria.documentation_only is True


def test_context_rule_conversion_preserves_pattern_order() -> None:
    rule = ContextRule(
        workflow_type=ContextWorkflowType.GENERAL_DOCUMENTATION,
        required_patterns=("required-1", "required-2"),
        optional_patterns=("optional-1", "optional-2"),
    )

    criteria = rule.to_filter_criteria()

    assert criteria.include_patterns == (
        "required-1",
        "required-2",
        "optional-1",
        "optional-2",
    )


def test_default_rules_cover_all_workflow_types() -> None:
    assert set(DEFAULT_CONTEXT_RULES) == set(ContextWorkflowType)


@pytest.mark.parametrize(
    "workflow_type",
    list(ContextWorkflowType),
)
def test_default_rule_matches_registry_key(
    workflow_type: ContextWorkflowType,
) -> None:
    rule = DEFAULT_CONTEXT_RULES[workflow_type]

    assert rule.workflow_type == workflow_type
    assert rule.required_patterns


def test_general_documentation_rule_includes_all_docs() -> None:
    rule = DEFAULT_CONTEXT_RULES[
        ContextWorkflowType.GENERAL_DOCUMENTATION
    ]

    assert "README.md" in rule.required_patterns
    assert "docs/*.md" in rule.required_patterns
    assert "docs/archive" in rule.excluded_paths


def test_update_documentation_rule_includes_standards() -> None:
    rule = DEFAULT_CONTEXT_RULES[
        ContextWorkflowType.UPDATE_DOCUMENTATION
    ]

    assert (
        "docs/project/Documentation_Standards.md"
        in rule.required_patterns
    )
    assert "docs/project/Project_Charter.md" in rule.required_patterns
    assert "docs/*Architecture*.md" in rule.required_patterns


def test_implement_component_rule_includes_platform_documents() -> None:
    rule = DEFAULT_CONTEXT_RULES[
        ContextWorkflowType.IMPLEMENT_COMPONENT
    ]

    assert (
        "docs/platform/Shared_Data_Models_and_Error_Contracts.md"
        in rule.optional_patterns
    )
    assert (
        "docs/platform/Component_Communication_Design.md"
        in rule.optional_patterns
    )


def test_validate_documentation_rule_includes_standards() -> None:
    rule = DEFAULT_CONTEXT_RULES[
        ContextWorkflowType.VALIDATE_DOCUMENTATION
    ]

    assert (
        "docs/project/Documentation_Standards.md"
        in rule.required_patterns
    )
    assert "docs/*.md" in rule.required_patterns


def test_default_rules_exclude_drafts_and_backups() -> None:
    for rule in DEFAULT_CONTEXT_RULES.values():
        assert "*Draft*.md" in rule.excluded_patterns
        assert "*.bak" in rule.excluded_patterns


def test_registry_returns_registered_rule() -> None:
    rule = ContextRule(
        workflow_type=ContextWorkflowType.GENERAL_DOCUMENTATION,
        required_patterns=("README.md",),
    )
    registry = ContextRuleRegistry(
        rules={
            ContextWorkflowType.GENERAL_DOCUMENTATION: rule,
        }
    )

    result = registry.get_rule(
        ContextWorkflowType.GENERAL_DOCUMENTATION
    )

    assert result is rule


def test_registry_returns_filter_criteria() -> None:
    rule = ContextRule(
        workflow_type=ContextWorkflowType.UPDATE_DOCUMENTATION,
        required_patterns=("README.md",),
    )
    registry = ContextRuleRegistry(
        rules={
            ContextWorkflowType.UPDATE_DOCUMENTATION: rule,
        }
    )

    criteria = registry.get_filter_criteria(
        ContextWorkflowType.UPDATE_DOCUMENTATION
    )

    assert criteria.include_patterns == ("README.md",)
    assert criteria.extensions == frozenset({".md"})


def test_registry_rejects_unregistered_workflow_type() -> None:
    registry = ContextRuleRegistry(rules={})

    with pytest.raises(
        ValueError,
        match="No context rule is registered",
    ):
        registry.get_rule(
            ContextWorkflowType.IMPLEMENT_COMPONENT
        )


def test_create_registry_contains_default_rules() -> None:
    registry = create_context_rule_registry()

    assert registry.rules == DEFAULT_CONTEXT_RULES
    assert set(registry.rules) == set(ContextWorkflowType)


def test_create_registry_copies_default_rules_dictionary() -> None:
    first = create_context_rule_registry()
    second = create_context_rule_registry()

    assert first.rules == second.rules
    assert first.rules is not second.rules
    assert first.rules is not DEFAULT_CONTEXT_RULES


def test_registry_modification_does_not_change_defaults() -> None:
    registry = create_context_rule_registry()
    original_count = len(DEFAULT_CONTEXT_RULES)

    registry.rules.pop(
        ContextWorkflowType.GENERAL_DOCUMENTATION
    )

    assert len(registry.rules) == original_count - 1
    assert len(DEFAULT_CONTEXT_RULES) == original_count
    assert (
        ContextWorkflowType.GENERAL_DOCUMENTATION
        in DEFAULT_CONTEXT_RULES
    )
