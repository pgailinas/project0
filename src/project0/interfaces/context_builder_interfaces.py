# ============================================================
# Project0 - Context Builder Interfaces
#
# File: context_builder_interfaces.py
#
# Purpose:
#     Define the public interface used to build Project0
#     context packages for workflow and AI-agent tasks.
#
# ============================================================

from __future__ import annotations

from typing import Protocol

from project0.models.context_models import (
    ContextPackage,
    ContextWorkflowType,
)


class ContextBuilderInterface(Protocol):
    """Public contract for Project0 context builders."""

    def build_documentation_context(
        self,
        context_id: str,
        workflow_type: ContextWorkflowType,
    ) -> ContextPackage:
        """Build and return documentation context for a workflow."""
