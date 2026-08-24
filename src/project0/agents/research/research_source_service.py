# ============================================================
# Project0 - Research Source Service
#
# File: research_source_service.py
#
# Purpose:
#     Execute Research Agent source searches against configured
#     research providers and return normalized results.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass

from project0.agents.research.research_source_provider import (
    ResearchSourceProviderProtocol,
)
from project0.models.research_models import (
    ResearchSourceReference,
    ResearchStrategy,
)


@dataclass(slots=True)
class ResearchSourceService:
    """Execute research searches against supported providers."""

    providers: dict[
        str,
        ResearchSourceProviderProtocol,
    ]

    def search(
        self,
        strategy: ResearchStrategy,
    ) -> tuple[ResearchSourceReference, ...]:
        """Search configured research providers for a strategy."""

        source_names = strategy.source_names or (
            "semantic_scholar",
        )

        references: list[ResearchSourceReference] = []
        failures: list[str] = []

        for source_name in source_names:
            provider = self.providers.get(source_name)

            if provider is None:
                raise ValueError(
                    f"Unsupported research source: {source_name}"
                )

            try:
                references.extend(
                    provider.search(strategy)
                )

            except RuntimeError as error:
                failures.append(
                    f"{source_name}: {error}"
                )
                continue

        if not references and failures:
            raise RuntimeError(
                "All research sources failed: "
                + "; ".join(failures)
            )

        return self._deduplicate_references(references)

    @staticmethod
    def _deduplicate_references(
        references: list[ResearchSourceReference],
    ) -> tuple[ResearchSourceReference, ...]:
        """Remove duplicate research references in source order."""

        unique_references: list[ResearchSourceReference] = []
        seen: set[tuple[str, str]] = set()

        for reference in references:
            key = (
                reference.source_name,
                reference.source_id,
            )

            if key in seen:
                continue

            seen.add(key)
            unique_references.append(reference)

        return tuple(unique_references)
