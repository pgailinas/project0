# ============================================================
# Project0 - Stub Research Source Provider
#
# File: stub_research_source_provider.py
#
# Purpose:
#     Provide deterministic research source provider behavior for
#     Project0 tests, demonstrations, and integration flows.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field

from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


@dataclass(slots=True)
class StubResearchSourceProvider(
    ResearchSourceProviderProtocol,
):
    """Return configured research references without source execution."""

    references: tuple[ResearchSourceReference, ...] = ()
    error: Exception | None = None
    requests: list[ResearchStrategy] = field(
        default_factory=list,
        init=False,
    )

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Record the strategy and return configured references."""

        self.requests.append(strategy)

        if self.error is not None:
            raise self.error

        return self.references
