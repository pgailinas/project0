# ============================================================
# Project0 - Research Source Provider Interface
#
# File: research_source_provider.py
#
# Purpose:
#     Define Research Agent source provider interfaces used by
#     Project0 research source services and implementations.
#
# ============================================================

from __future__ import annotations

from typing import Protocol, runtime_checkable

from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


@runtime_checkable
class ResearchSourceProviderProtocol(Protocol):
    """Interface for Research Agent source providers."""

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search a research source for references."""

        ...
